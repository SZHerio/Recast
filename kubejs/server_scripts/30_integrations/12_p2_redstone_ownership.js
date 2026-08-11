// P2 «Редстоун и механизмы»: автоматика собирается машиной, а не руками.
//
// Решение владельца от 9 августа 2026 года. Линия — docs/registries/recipe_devolution.json.
//
// Список построен по выгрузке рецептов из запущенной игры: это ванильные
// механизмы, у которых не было ни одного машинного маршрута. Владельцем
// становится механический сборщик Create — способ, уже проверенный волнами
// света и обихода: 787 сборок без единой ошибки.
//
// Рецепт не выписывается вручную: сборщик получает ту же выкладку, что была на
// верстаке. Сначала операция отдаётся машине, только потом снимается ручная.
//
// Намеренно оставлены ручными рычаг, кнопка, нажимная плита и редстоуновый
// факел: это переключатели, а не механизмы, и без них нельзя запустить первую
// же линию, которая соберёт всё остальное.
ServerEvents.recipes((event) => {
  const mechanisms = [
    'minecraft:comparator',
    'minecraft:repeater',
    'minecraft:observer',
    'minecraft:dispenser',
    'minecraft:dropper',
    'minecraft:piston',
    'minecraft:sticky_piston',
    'minecraft:hopper',
    'minecraft:rail',
    'minecraft:powered_rail',
    'minecraft:detector_rail',
    'minecraft:activator_rail',
    'minecraft:daylight_detector',
    'minecraft:target',
    'minecraft:tripwire_hook',
    'minecraft:note_block',
    'minecraft:jukebox'
  ]

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    if (mechanisms.indexOf(output) < 0) return
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

  console.info('[Recast] P2 redstone: ' + handed + ' mechanisms moved to the mechanical crafter')
})
