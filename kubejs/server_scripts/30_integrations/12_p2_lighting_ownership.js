// P2 «Свет»: осветительные сборки собирает механический сборщик.
//
// Решение владельца от 9 августа 2026 года: ручной рецепт снимается полностью.
// Линия — docs/registries/recipe_devolution.json.
//
// Обход показал 278 позиций и 243 разных состава у десяти модов: общей
// физической операции у них нет, это шаблонная сборка. Поэтому владельцем
// становится механический сборщик Create — та же выкладка, но машиной.
//
// Список не выписывается вручную: источником истины служат сами рецепты. Для
// каждого шаблонного рецепта света создаётся зеркальный рецепт сборщика, и лишь
// затем снимается ручная выкладка. Предмет не может выпасть из игры.
//
// Факелы и фонари ванили не входят: без источника света в первый час игрок
// остаётся в темноте до первой машины.
ServerEvents.recipes((event) => {
  const owners = [
    'mcwlights', 'projectred_illumination', 'supplementaries',
    'pneumaticcraft', 'createdeco', 'hbm_ntm_rebirth'
  ]
  const lightNames = /_(lamp|lantern|chandelier|candle_holder|torch|light|sconce)$/

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    const namespace = output.split(':')[0]
    if (owners.indexOf(namespace) < 0) return
    if (!lightNames.test(output.split(':')[1])) return

    const pattern = []
    json.get('pattern').getAsJsonArray().forEach((row) => pattern.push(row.getAsString()))
    const key = {}
    const rawKey = json.get('key').getAsJsonObject()
    rawKey.keySet().forEach((symbol) => {
      key[symbol] = Ingredient.of(rawKey.get(symbol))
    })
    const count = result.getAsJsonObject().has('count')
      ? result.getAsJsonObject().get('count').getAsInt()
      : 1

    // Механический сборщик выполняет ту же выкладку.
    event.recipes.create.mechanical_crafting(Item.of(output, count), pattern, key)
    // Руками эту сборку больше не выполнить.
    event.remove({ type: 'minecraft:crafting_shaped', output: output })
    handed += 1
  })

  console.info(`[Recast] свет: механическому сборщику передано ${handed} сборок`)
})
