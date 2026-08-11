// P2 «Броня модов»: правило брони одинаково для всей сборки.
//
// Ванильные комплекты уже собирает механический сборщик. Оставить доспехи чужих
// модов ручными значит дать игроку обход: та же защита без фабрики.
//
// Владелец прежний — механический сборщик, выкладка берётся из самого рецепта.
//
// Исключения:
// - GregTech: его снаряжение живёт в собственной материальной лестнице, и
//   вмешиваться в неё нельзя без разбора всей ветки;
// - кожаная и тканевая защита любых модов: это первая броня до промышленности;
// - TaCZ и Create Big Cannons: огнестрел и артиллерия заперты эпохой отдельно,
//   их снаряжение относится к боевым воротам, а не к производственной линии.
ServerEvents.recipes((event) => {
  const ARMOUR = /_(helmet|chestplate|leggings|boots|cuirass|greaves|gauntlets|pauldrons)$/
  const SOFT = /(leather|cloth|padded|linen|wool)/
  const SKIP_NS = ['minecraft', 'gtceu', 'gtnn', 'tacz', 'createbigcannons']

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    const parts = output.split(':')
    if (SKIP_NS.indexOf(parts[0]) >= 0) return
    if (!ARMOUR.test(parts[1]) || SOFT.test(parts[1])) return
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

  console.info('[Recast] P2 mod armour: ' + handed + ' pieces moved to the mechanical crafter')
})
