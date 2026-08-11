// P2 «Броня»: комплекты защиты собирает машина.
//
// Решение владельца сборки от 9 августа 2026 года передано мне: инструменты
// остаются ручными, броня уходит машине. Причина в том, как игрок ими живёт.
// Кирка ломается посреди шахты, и возвращаться за ней к сборщику — издевательство,
// а не сложность. Броню делают заранее и партией, перед вылазкой: здесь фабрика
// уместна и ощущается снаряжением экспедиции, а не бытовой мелочью.
//
// Инструменты при этом не остаются прежними: штатный переключатель GregTech
// hardToolArmorRecipes требует для них пластины и стержни вместо голых слитков,
// поэтому металл в сборке сохраняет вес.
//
// Кожаная броня оставлена ручной: это первая защита до всякой промышленности.
ServerEvents.recipes((event) => {
  const ARMOUR = /_(helmet|chestplate|leggings|boots)$/
  const KEEP = /^leather_/

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    if (output.split(':')[0] !== 'minecraft') return
    const path = output.split(':')[1]
    if (!ARMOUR.test(path) || KEEP.test(path)) return
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

    event.recipes.create.mechanical_crafting(Item.of(output, 1), pattern, key)
    event.remove({ type: 'minecraft:crafting_shaped', output: output })
    handed += 1
  })

  console.info('[Recast] P2 armour: ' + handed + ' armour pieces moved to the mechanical crafter')
})
