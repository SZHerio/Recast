// P2 «Стекло, ткань, окраска»: массовая отделка собирается машиной.
//
// Решение владельца от 9 августа 2026 года. Линия — docs/registries/recipe_devolution.json.
//
// Класс из выгрузки рецептов запущенной игры: знамёна, ковры, окрашенное стекло,
// шерсть и глазурованная керамика. Это массовый материал городской застройки —
// именно тот случай, когда ручная выкладка сотен одинаковых блоков и есть гринд.
//
// Владелец — механический сборщик: он получает ту же выкладку, что была на
// верстаке. Сначала машине, потом снятие ручного.
//
// Кровати намеренно оставлены ручными: точка возрождения нужна в первую ночь,
// когда сборщика ещё нет, и запирать её за фабрикой — наказание, а не сложность.
ServerEvents.recipes((event) => {
  const TAKE = /(_banner|_carpet|_glazed_terracotta|stained_glass|_wool|_terracotta)$/
  const SKIP = /(_bed|banner_pattern)$/

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    if (output.split(':')[0] !== 'minecraft') return
    const path = output.split(':')[1]
    if (!TAKE.test(path) || SKIP.test(path)) return
    if (!json.has('pattern') || !json.has('key')) return

    const pattern = []
    json.get('pattern').getAsJsonArray().forEach(function (row) {
      pattern.push(row.getAsString())
    })
    const key = {}
    const rawKey = json.get('key').getAsJsonObject()
    rawKey.keySet().forEach(function (symbol) {
      key[symbol] = Ingredient.of(rawKey.get(symbol))
    })
    const count = result.getAsJsonObject().has('count')
      ? result.getAsJsonObject().get('count').getAsInt() : 1

    event.recipes.create.mechanical_crafting(Item.of(output, count), pattern, key)
    event.remove({ type: 'minecraft:crafting_shaped', output: output })
    handed += 1
  })

  console.info('[Recast] P2 textile: ' + handed + ' decorative blocks moved to the mechanical crafter')
})
