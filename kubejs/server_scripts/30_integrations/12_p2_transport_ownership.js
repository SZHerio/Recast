// P2 «Транспорт»: подвижной состав и путевое хозяйство собирает машина.
//
// Городской транспорт — часть промышленной инфраструктуры, а не поделка на
// верстаке. Поезд, вагон, стрелка и сигнал требуют производства, как и всё
// остальное в сборке.
//
// Владелец — механический сборщик: выкладка берётся из самого рецепта, сначала
// операция отдаётся машине, потом снимается ручная.
//
// Ванильные вагонетки уже переданы прежней волной. Лодки и обычные рельсы
// оставлены: первое — ранний способ пересечь воду, второе снято отдельно.
ServerEvents.recipes((event) => {
  const OWNERS = ['mtr', 'railways', 'littlelogistics']

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    if (OWNERS.indexOf(output.split(':')[0]) < 0) return
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

  console.info('[Recast] P2 transport: ' + handed + ' rolling stock and track parts moved to the mechanical crafter')
})
