// P2 «Ванильный остаток»: всё, что ещё собиралось руками, уходит сборщику.
//
// Решение владельца от 9 августа 2026 года. Линия — docs/registries/recipe_devolution.json.
//
// Волна закрывает остаток ванильных шаблонных рецептов: наковальня, стойка для
// брони, деревянные и бамбуковые блоки, тележки, книжные полки и прочая утварь.
// Владелец прежний и проверенный — механический сборщик.
//
// Оставлено ручным то, без чего не пережить первые часы и не построить первую
// же машину: инструменты, оружие, броня, щит, ведро, кровать, факел, рычаг,
// кнопка, нажимная плита, лодка, лестница, верстак, печь, сундук и палки.
// Инструменты и броня ждут отдельного решения владельца сборки.
ServerEvents.recipes((event) => {
  const KEEP = /(_sword|_pickaxe|_axe|_shovel|_hoe|_helmet|_chestplate|_leggings|_boots|shield|bucket|_bed|torch|lever|button|pressure_plate|_boat|ladder|crafting_table|furnace|chest$|stick|bow$|arrow|flint_and_steel|shears|string|campfire)/

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    if (output.split(':')[0] !== 'minecraft') return
    if (KEEP.test(output.split(':')[1])) return
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

  console.info('[Recast] P2 vanilla rest: ' + handed + ' items moved to the mechanical crafter')
})
