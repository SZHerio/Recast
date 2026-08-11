// Дисциплина лута перестроенных ванильных структур.
//
// Восемь модов YUNG's перестраивают подземелья, храмы, крепости, цитадели и
// остров Края, но пользуются ванильными таблицами лута. Прежнее правило
// (85_structure_loot_discipline.js) намеренно ваниль не трогало, поэтому эти
// структуры остались единственным местом в сборке, где находка обгоняет
// прогрессию на несколько эпох.
//
// Здесь то же правило применяется точечно: только к таблицам, которые
// перестраивают моды YUNG's, а не ко всему ванильному луту. Снаряжение не
// исчезает, а понижается на ступень — находка остаётся находкой, но перестаёт
// отменять фабрику.
//
// Отдельно снимаются три предмета, которые понизить нельзя: элитра ломает
// логистику раньше первого транспорта, тотем отменяет цену ошибки, зачарованное
// золотое яблоко ломает баланс операций внешнего мира.
//
// Сырьё не трогается: алмаз, изумруд и незеритовый лом — материалы, а не
// изделия, и найти их в сундуке нормально и полезно.
LootJS.modifiers((event) => {
  const tables = [
    'minecraft:chests/simple_dungeon',
    'minecraft:chests/desert_pyramid',
    'minecraft:chests/jungle_temple',
    'minecraft:chests/jungle_temple_dispenser',
    'minecraft:chests/nether_bridge',
    'minecraft:chests/stronghold_corridor',
    'minecraft:chests/stronghold_crossing',
    'minecraft:chests/stronghold_library',
    'minecraft:chests/end_city_treasure'
  ]

  const downgrade = {
    'minecraft:netherite_helmet': 'minecraft:diamond_helmet',
    'minecraft:netherite_chestplate': 'minecraft:diamond_chestplate',
    'minecraft:netherite_leggings': 'minecraft:diamond_leggings',
    'minecraft:netherite_boots': 'minecraft:diamond_boots',
    'minecraft:netherite_sword': 'minecraft:diamond_sword',
    'minecraft:netherite_pickaxe': 'minecraft:diamond_pickaxe',
    'minecraft:netherite_axe': 'minecraft:diamond_axe',
    'minecraft:netherite_shovel': 'minecraft:diamond_shovel',
    'minecraft:netherite_hoe': 'minecraft:diamond_hoe',
    'minecraft:diamond_helmet': 'minecraft:iron_helmet',
    'minecraft:diamond_chestplate': 'minecraft:iron_chestplate',
    'minecraft:diamond_leggings': 'minecraft:iron_leggings',
    'minecraft:diamond_boots': 'minecraft:iron_boots',
    'minecraft:diamond_sword': 'minecraft:iron_sword',
    'minecraft:diamond_pickaxe': 'minecraft:iron_pickaxe',
    'minecraft:diamond_axe': 'minecraft:iron_axe',
    'minecraft:diamond_shovel': 'minecraft:iron_shovel',
    'minecraft:diamond_hoe': 'minecraft:iron_hoe'
  }

  // Три предмета, которые нельзя понизить внутри своей ветки, заменяются
  // осмысленным эквивалентом: перепонка вместо элитры, изумруд вместо тотема,
  // обычное яблоко вместо зачарованного.
  const replaced = {
    'minecraft:elytra': 'minecraft:phantom_membrane',
    'minecraft:totem_of_undying': 'minecraft:emerald',
    'minecraft:enchanted_golden_apple': 'minecraft:golden_apple'
  }

  tables.forEach((table) => {
    const rule = event.addLootTableModifier(table)
    Object.keys(downgrade).forEach((from) => {
      rule.replaceLoot(from, downgrade[from])
    })
    Object.keys(replaced).forEach((from) => {
      rule.replaceLoot(from, replaced[from])
    })
  })

  console.info('[Recast] YUNG loot: discipline applied to ' + tables.length + ' rebuilt vanilla structure tables')
})
