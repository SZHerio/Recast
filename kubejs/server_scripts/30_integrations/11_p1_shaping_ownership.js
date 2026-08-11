// P1 «Форма»: операции обработки принадлежат машинам Create, а не верстаку.
//
// Решение владельца от 9 августа 2026 года: ручной рецепт снимается полностью,
// а не ослабляется. Линия и её правила — docs/registries/recipe_devolution.json,
// проверка — tools/validate_recipe_devolution.py.
//
// В список попадает только настоящий дубль: машина Create даёт тот же результат
// из того же сырья. Переработка (кожа из конской брони), обесцвечивание (мытьё
// шерсти и стекла) и рудная линия сюда не входят — это другие операции, и рудой
// владеет GregTech.
//
// Доски остаются ручными: верстак делается из досок, а пила делается на верстаке.
// Полное снятие сделало бы игру незапускаемой, поэтому ручной выход уменьшен
// настройкой nerfWoodCrafting, а пила остаётся выгодным маршрутом.
ServerEvents.recipes((event) => {
  const dropCrafting = (output) => {
    event.remove({ type: 'minecraft:crafting_shaped', output: output })
    event.remove({ type: 'minecraft:crafting_shapeless', output: output })
  }

  // Пресс: волокно расплющивают под давлением.
  dropCrafting('minecraft:paper')

  // Пресс владеет листами. Ручных дублей сейчас нет; снятие защищает от того,
  // что их добавит обновление Create или чужая совместимость.
  ;['create:iron_sheet', 'create:copper_sheet', 'create:golden_sheet', 'create:brass_sheet'].forEach(dropCrafting)

  // Мельница: истирание в порошок. Красители из цветов, чернил и угля, сахар из
  // тростника и костная мука из кости — это помол, а не складывание в сетке.
  ;[
    'minecraft:black_dye', 'minecraft:blue_dye', 'minecraft:brown_dye', 'minecraft:cyan_dye',
    'minecraft:gray_dye', 'minecraft:light_blue_dye', 'minecraft:light_gray_dye', 'minecraft:lime_dye',
    'minecraft:magenta_dye', 'minecraft:orange_dye', 'minecraft:pink_dye', 'minecraft:purple_dye',
    'minecraft:red_dye', 'minecraft:white_dye', 'minecraft:yellow_dye'
  ].forEach(dropCrafting)
  dropCrafting('minecraft:sugar')
  dropCrafting('minecraft:bone_meal')

  // Дробилки: пруток ифрита разбивают, а не растирают в ладонях.
  dropCrafting('minecraft:blaze_powder')

  // Развёртыватель: воск наносится инструментом на блок, а не смешивается с ним
  // в сетке крафта. Вся семья вощёной меди уходит к машине целиком.
  ;[
    'minecraft:waxed_copper_block', 'minecraft:waxed_cut_copper', 'minecraft:waxed_cut_copper_slab',
    'minecraft:waxed_cut_copper_stairs', 'minecraft:waxed_exposed_copper', 'minecraft:waxed_exposed_cut_copper',
    'minecraft:waxed_exposed_cut_copper_slab', 'minecraft:waxed_exposed_cut_copper_stairs',
    'minecraft:waxed_oxidized_copper', 'minecraft:waxed_oxidized_cut_copper',
    'minecraft:waxed_oxidized_cut_copper_slab', 'minecraft:waxed_oxidized_cut_copper_stairs',
    'minecraft:waxed_weathered_copper', 'minecraft:waxed_weathered_cut_copper',
    'minecraft:waxed_weathered_cut_copper_slab', 'minecraft:waxed_weathered_cut_copper_stairs'
  ].forEach(dropCrafting)

  // Одержимость душевым огнём: обычный источник света переделывает пламя, а не
  // рецепт с песком душ.
  ;['minecraft:soul_torch', 'minecraft:soul_lantern', 'minecraft:soul_campfire'].forEach(dropCrafting)

  // Промывка: лёд уплотняют потоком, а не давлением ладоней.
  dropCrafting('minecraft:packed_ice')

  // Журнал KubeJS пишется не в UTF-8: кириллица в нём превращается в кашу,
  // поэтому строки отчёта латинские.
  console.info('[Recast] P1 shaping: hand recipes removed for paper, sheets, dyes, sugar, bone meal, blaze powder, waxed copper, soul lights, packed ice')
})
