// Дисциплина лута новых структур.
//
// Пять модов структур принесли около четырёхсот построек — и вместе с ними
// сундуки, которые ломают боевую лестницу сборки. Проверка их таблиц показала:
// 26 алмазных нагрудников, 20 алмазных мечей, 14 кирок, незеритовые слиток и
// шлем, 4 элитры, 2 тотема бессмертия и 74 зачарованных золотых яблока.
//
// Почему это нарушение, а не удача. У сборки есть правило: высокий лут состоит
// из сведений, чертежей, повреждённых деталей, инструментов, валюты и
// образцов, но не из готового снаряжения будущей эпохи. На нём держится вся
// боевая лестница: отряды пятой эпохи носят железо, седьмой — алмаз, и это
// осмысленно ровно до тех пор, пока игрок не находит незеритовый шлем в руинах
// на второй день.
//
// Что делается. Снаряжение не удаляется, а понижается на ступень: незеритовое
// становится алмазным, алмазное — железным. Находка остаётся находкой, но
// перестаёт обгонять прогрессию. Отдельно снимаются три предмета, которые
// понизить нельзя, потому что они не про броню: элитра ломает логистику
// раньше, чем игрок построит хоть один транспорт, тотем отменяет цену ошибки,
// зачарованное золотое яблоко ломает баланс операций внешнего мира.
//
// Сырьё не трогается. Алмаз, изумруд и незеритовый лом — материалы, а не
// изделия; найти их в сундуке нормально и полезно.
//
// Ванильные структуры не затрагиваются: правило вводится вместе с новыми
// модами и применяется только к их таблицам.
LootJS.modifiers((event) => {
  // Пространства имён лут-таблиц пяти установленных модов структур. Обратите
  // внимание на kaisyn: Towns and Towers объявляет мод как t_and_t, но свои
  // таблицы кладёт в другое пространство. Проверено по содержимому JAR, а не
  // по имени файла — иначе фильтр молча не совпал бы ни с чем.
  const structureTables = /^(repurposed_structures|kaisyn|mvs|mes|philipsruins):/

  // Понижение на ступень: незеритовое снаряжение становится алмазным.
  const netheriteToDiamond = {
    'minecraft:netherite_helmet': 'minecraft:diamond_helmet',
    'minecraft:netherite_chestplate': 'minecraft:diamond_chestplate',
    'minecraft:netherite_leggings': 'minecraft:diamond_leggings',
    'minecraft:netherite_boots': 'minecraft:diamond_boots',
    'minecraft:netherite_sword': 'minecraft:diamond_sword',
    'minecraft:netherite_pickaxe': 'minecraft:diamond_pickaxe',
    'minecraft:netherite_axe': 'minecraft:diamond_axe',
    'minecraft:netherite_shovel': 'minecraft:diamond_shovel',
    'minecraft:netherite_hoe': 'minecraft:diamond_hoe'
  }

  // Понижение на ступень: алмазное снаряжение становится железным.
  const diamondToIron = {
    'minecraft:diamond_helmet': 'minecraft:iron_helmet',
    'minecraft:diamond_chestplate': 'minecraft:iron_chestplate',
    'minecraft:diamond_leggings': 'minecraft:iron_leggings',
    'minecraft:diamond_boots': 'minecraft:iron_boots',
    'minecraft:diamond_sword': 'minecraft:iron_sword',
    'minecraft:diamond_pickaxe': 'minecraft:iron_pickaxe',
    'minecraft:diamond_axe': 'minecraft:iron_axe',
    'minecraft:diamond_shovel': 'minecraft:iron_shovel',
    'minecraft:diamond_hoe': 'minecraft:iron_hoe',
    'minecraft:diamond_horse_armor': 'minecraft:iron_horse_armor'
  }

  // Порядок важен: сначала незеритовое опускается до алмазного, потом всё
  // алмазное — до железного. Одним проходом незерит ушёл бы только на ступень.
  const modifier = event.addLootTableModifier(structureTables)
  Object.keys(netheriteToDiamond).forEach((from) =>
    modifier.replaceLoot(from, netheriteToDiamond[from]))
  Object.keys(diamondToIron).forEach((from) =>
    modifier.replaceLoot(from, diamondToIron[from]))

  // Зачарованное золотое яблоко — обычным: 74 вхождения на пять модов делают
  // его рядовой находкой, а оно рассчитано на редкость.
  modifier.replaceLoot('minecraft:enchanted_golden_apple', 'minecraft:golden_apple')

  // Три предмета, которые нельзя понизить, потому что у них нет ступени ниже.
  const removedOutright = [
    // Полёт раньше любого построенного транспорта обесценивает четыре слоя
    // логистики пятой эпохи разом.
    'minecraft:elytra',
    // Отмена цены ошибки ломает операции внешнего мира: у каждой прописано
    // восстановление, а не бессмертие.
    'minecraft:totem_of_undying',
    // Шаблон незеритового улучшения без незеритовой брони бесполезен, а с
    // ней возвращает ровно то, что мы только что понизили.
    'minecraft:netherite_upgrade_smithing_template'
  ]
  removedOutright.forEach((item) => modifier.removeLoot(item))

  console.info(
    `[Recast] Лут структур: ${Object.keys(netheriteToDiamond).length + Object.keys(diamondToIron).length + 1} видов снаряжения понижено на ступень, ${removedOutright.length} сняты полностью. Сырьё и валюта не тронуты.`
  )
})
