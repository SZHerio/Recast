// P2 «Оборудование экономики»: торговые устройства собирает машина.
//
// Валюта принята проектом как пилот городской экономики: деньги служат стоком
// ресурсов и слоем услуг. Но банкомат, терминал, витрина и торговый автомат —
// это оборудование, а не поделка на верстаке.
//
// Владелец — механический сборщик, выкладка берётся из самого рецепта.
//
// Монеты намеренно остаются ручными: с них начинается экономика, и запирать её
// за фабрикой значит не дать ей запуститься вовсе.
//
// AE2 в этой волне отсутствует сознательно: он уже заперт за пятой эпохой
// тремя отдельными скриптами, и его ручные рецепты — часть собственной
// инженерной логики мода. Единообразие не стоит сломанных ворот.
ServerEvents.recipes((event) => {
  const COIN = /(coin|banknote|ticket|token)/

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    if (output.split(':')[0] !== 'lightmanscurrency') return
    if (COIN.test(output.split(':')[1])) return
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

  console.info('[Recast] P2 currency: ' + handed + ' trading devices moved to the mechanical crafter')
})
