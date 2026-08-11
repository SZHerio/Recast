// P2 «Помол и смеси»: бетонный порошок готовит смеситель, а не ладони.
//
// Решение владельца от 9 августа 2026 года: ручной рецепт снимается полностью.
// Линия — docs/registries/recipe_devolution.json, страж — tools/validate_recipe_devolution.py.
// Порядок обязателен: рецепт смесителя создаётся до снятия ручного.
ServerEvents.recipes((event) => {
  const powders = [
    ['minecraft:white_concrete_powder', 'minecraft:white_dye'],
    ['minecraft:orange_concrete_powder', 'minecraft:orange_dye'],
    ['minecraft:magenta_concrete_powder', 'minecraft:magenta_dye'],
    ['minecraft:light_blue_concrete_powder', 'minecraft:light_blue_dye'],
    ['minecraft:yellow_concrete_powder', 'minecraft:yellow_dye'],
    ['minecraft:lime_concrete_powder', 'minecraft:lime_dye'],
    ['minecraft:pink_concrete_powder', 'minecraft:pink_dye'],
    ['minecraft:gray_concrete_powder', 'minecraft:gray_dye'],
    ['minecraft:light_gray_concrete_powder', 'minecraft:light_gray_dye'],
    ['minecraft:cyan_concrete_powder', 'minecraft:cyan_dye'],
    ['minecraft:purple_concrete_powder', 'minecraft:purple_dye'],
    ['minecraft:blue_concrete_powder', 'minecraft:blue_dye'],
    ['minecraft:brown_concrete_powder', 'minecraft:brown_dye'],
    ['minecraft:green_concrete_powder', 'minecraft:green_dye'],
    ['minecraft:red_concrete_powder', 'minecraft:red_dye'],
    ['minecraft:black_concrete_powder', 'minecraft:black_dye']
  ]

  powders.forEach(([powder, dye]) => {
    // Чаша со смесителем: песок, гравий и краситель размешивают в партию.
    event.recipes.create.mixing(Item.of(powder, 8), [
      Item.of('minecraft:sand', 4),
      Item.of('minecraft:gravel', 4),
      dye
    ])
    event.remove({ type: 'minecraft:crafting_shaped', output: powder })
    event.remove({ type: 'minecraft:crafting_shapeless', output: powder })
  })

  // Латиница намеренно: журнал KubeJS пишется не в UTF-8.
  console.info('[Recast] P2 mixing: ' + powders.length + ' concrete powders moved to the mechanical mixer')
})
