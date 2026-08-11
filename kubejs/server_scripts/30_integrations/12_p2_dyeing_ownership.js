// P2 «Окраска»: перекрашивание материала — работа смесителя.
//
// Решение владельца от 9 августа 2026 года. Линия — docs/registries/recipe_devolution.json.
//
// Механический сборщик умеет только шаблонную выкладку, поэтому окраска мимо
// него прошла: у ванили это бесформенный рецепт — краситель и блок в любом
// порядке. Настоящая операция здесь — размешивание, и владельцем становится
// смеситель Create.
//
// Список не выписывается: скрипт берёт сами бесформенные рецепты как источник
// истины, зеркалит их в смеситель и только потом снимает ручные.
ServerEvents.recipes((event) => {
  const TAKE = /(_wool|_carpet|_terracotta|_candle|_glass|_glass_pane|_shulker_box)$/

  let handed = 0
  let skipped = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shapeless' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    if (output.split(':')[0] !== 'minecraft') return
    if (!TAKE.test(output.split(':')[1])) return
    if (!json.has('ingredients')) return

    const inputs = []
    json.get('ingredients').getAsJsonArray().forEach(function (one) {
      inputs.push(Ingredient.of(one))
    })
    if (inputs.length === 0 || inputs.length > 9) {
      skipped += 1
      return
    }
    const count = result.getAsJsonObject().has('count')
      ? result.getAsJsonObject().get('count').getAsInt() : 1

    try {
      event.recipes.create.mixing(Item.of(output, count), inputs)
      event.remove({ type: 'minecraft:crafting_shapeless', output: output })
      handed += 1
    } catch (error) {
      skipped += 1
    }
  })

  console.info('[Recast] P2 dyeing: ' + handed + ' colouring recipes moved to the mechanical mixer, skipped ' + skipped)
})
