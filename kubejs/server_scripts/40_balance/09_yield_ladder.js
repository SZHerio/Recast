// Лестница выхода: старшая машина обязана быть выгоднее младшей.
//
// Решение владельца от 9 августа 2026 года: ориентир — превосходство в
// полтора-два раза на ступень. Правило записано в
// docs/registries/recipe_devolution.json, статическая сверка —
// tools/audit_recipe_owners.py.
//
// Скрипт не содержит списка предметов: он считает лестницу по фактическим
// рецептам сборки, поэтому новый мод не оставит перевёрнутую ступень незаметной.
//
// Два правила безопасности, оба выстраданы:
// 1. Количество меняется только на стороне JavaScript, через разбор и сборку
//    текста рецепта. Правка Gson-объекта записывала «4.0» вместо «4», и разбор
//    рецептов падал, обрывая все остальные волны.
// 2. Выход только поднимается у старшей ступени и никогда не срезается у
//    младшей: оценка не видит энергию и время, а её ошибка не должна отнимать
//    у игрока привычный маршрут.
//
// Строки журнала латинские: журнал KubeJS пишется не в UTF-8, кириллица в нём
// нечитаема.
ServerEvents.recipes((event) => {
  const TIERS = {
    'farmersdelight:cutting': 0,
    'refurbished_furniture:cutting_board_slicing': 0,
    'refurbished_furniture:freezer_solidifying': 0,
    'create:milling': 1,
    'create:crushing': 1,
    'create:pressing': 1,
    'create:splashing': 1,
    'create:compacting': 1,
    'create:mixing': 1,
    'create:cutting': 1,
    'create:mechanical_crafting': 1,
    'create:sequenced_assembly': 2,
    'immersiveengineering:crusher': 2,
    'pneumaticcraft:pressure_chamber': 2,
    'nuclearcraft:manufactory': 3,
    'nuclearcraft:irradiator': 3,
    'hbm_ntm_rebirth:shredder': 3
  }
  const STEP = 1.75

  // Результаты рецепта в виде обычного массива JavaScript.
  function resultsOf(data) {
    if (data.results) return data.results
    if (data.result) return Array.isArray(data.result) ? data.result : [data.result]
    return []
  }

  function idOf(row) {
    if (!row) return null
    if (typeof row === 'string') return row
    return row.item || row.id || null
  }

  function consumedBy(data) {
    let total = 0
    const raw = data.ingredients || data.ingredient || []
    const list = Array.isArray(raw) ? raw : [raw]
    list.forEach(function (one) {
      total = total + (one && one.count ? one.count : 1)
    })
    return total > 0 ? total : 1
  }

  // Первый проход: лучшая отдача каждой ступени по каждому предмету.
  const best = {}
  Object.keys(TIERS).forEach(function (type) {
    event.forEachRecipe({ type: type }, function (recipe) {
      let data = null
      try {
        data = JSON.parse(recipe.json.toString())
      } catch (error) {
        return
      }
      const consumed = consumedBy(data)
      resultsOf(data).forEach(function (row) {
        const item = idOf(row)
        if (!item) return
        const produced = row.count ? row.count : 1
        const ratio = produced / consumed
        if (!best[item]) best[item] = {}
        const tier = TIERS[type]
        if (!best[item][tier] || best[item][tier] < ratio) best[item][tier] = ratio
      })
    })
  })

  // Второй проход: старшая ступень поднимается до превосходства над младшей.
  let raised = 0
  let failed = 0
  Object.keys(TIERS).forEach(function (type) {
    const tier = TIERS[type]
    event.forEachRecipe({ type: type }, function (recipe) {
      let data = null
      try {
        data = JSON.parse(recipe.json.toString())
      } catch (error) {
        return
      }
      const consumed = consumedBy(data)
      let changed = false

      resultsOf(data).forEach(function (row) {
        const item = idOf(row)
        if (!item || !best[item]) return

        let lower = 0
        Object.keys(best[item]).forEach(function (key) {
          if (parseInt(key, 10) < tier && best[item][key] > lower) lower = best[item][key]
        })
        if (lower === 0) return

        const produced = row.count ? row.count : 1
        if (produced / consumed >= lower * STEP) return

        const wanted = Math.ceil(lower * STEP * consumed)
        if (wanted <= produced) return
        row.count = wanted
        changed = true
      })

      if (!changed) return
      try {
        event.remove({ id: recipe.getId() })
        event.custom(data)
        raised = raised + 1
      } catch (error) {
        failed = failed + 1
      }
    })
  })

  console.info('[Recast] yield ladder: raised ' + raised + ' recipes, failed ' + failed + ', step x' + STEP)
})
