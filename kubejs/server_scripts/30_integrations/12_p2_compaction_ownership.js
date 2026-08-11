// P2 «Уплотнение»: сборка мелочи в блок принадлежит машине.
//
// Решение владельца от 9 августа 2026 года: ручной рецепт снимается полностью.
// Линия — docs/registries/recipe_devolution.json, страж — tools/validate_recipe_devolution.py.
//
// Порядок обязателен: сначала операция отдаётся чаше под прессом, только потом
// снимается ручной рецепт. Иначе предмет исчезает из игры, а не переезжает.
//
// В набор взяты только строительные и хозяйственные уплотнения. Слитки, руды и
// редстоун сюда не входят: ручное сжатие металлов уже отключено настройкой
// GregTech, и рудной линией владеет он же.
ServerEvents.recipes((event) => {
  // выход, сколько единиц входа, вход
  const compactions = [
    ['minecraft:bricks', 4, 'minecraft:brick'],
    ['minecraft:nether_bricks', 4, 'minecraft:nether_brick'],
    ['minecraft:quartz_block', 4, 'minecraft:quartz'],
    ['minecraft:prismarine', 4, 'minecraft:prismarine_shard'],
    ['minecraft:sandstone', 4, 'minecraft:sand'],
    ['minecraft:red_sandstone', 4, 'minecraft:red_sand'],
    ['minecraft:hay_block', 9, 'minecraft:wheat'],
    ['minecraft:snow_block', 4, 'minecraft:snowball'],
    ['minecraft:clay', 4, 'minecraft:clay_ball'],
    ['minecraft:glowstone', 4, 'minecraft:glowstone_dust'],
    ['minecraft:slime_block', 9, 'minecraft:slime_ball'],
    ['minecraft:honeycomb_block', 4, 'minecraft:honeycomb'],
    ['minecraft:dried_kelp_block', 9, 'minecraft:dried_kelp'],
    ['minecraft:bone_block', 9, 'minecraft:bone_meal'],
    ['minecraft:mud_bricks', 4, 'minecraft:packed_mud']
  ]

  compactions.forEach(([output, count, input]) => {
    // Чаша под прессом: материал сдавливают в блок.
    event.recipes.create.compacting(output, [Item.of(input, count)])
    // Ручная выкладка той же операции больше не существует.
    event.remove({ type: 'minecraft:crafting_shaped', output: output })
    event.remove({ type: 'minecraft:crafting_shapeless', output: output })
  })

  // Латиница намеренно: журнал KubeJS пишется не в UTF-8.
  console.info('[Recast] P2 compaction: ' + compactions.length + ' blocks moved to the basin under a press')
})
