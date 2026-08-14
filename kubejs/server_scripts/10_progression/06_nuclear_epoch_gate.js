// Ворота атомной эпохи P6.
//
// NuclearCraft: Neoteric — это весь гражданский атомный домен: 4331 рецепт,
// топливный цикл, реакторы деления и жидкосолевые, теплообменники, турбины,
// переработка ОЯТ и разделение изотопов. Мод стоял в сборке с волны M4 по
// зарегистрированному отклонению и до сих пор не имел ни ворот, ни рецептов.
//
// Проблема, которую закрывают эти ворота: штатная первая машина мода стоит
// свинца, кремня, поршня и красной пыли. То есть вся атомная промышленность
// открывалась в первую эпоху, до стали, до электричества и до города.
//
// Замок стоит на двух машинах. Manufactory и alloy_smelter — единственные две,
// которые превращают сырьё в собственные детали NuclearCraft; всё остальное
// собирается уже из них. Закрыв эти две, закрываешь домен целиком, не трогая
// 4331 рецепт и не ломая внутреннюю физику мода.
//
// Третий рецепт — контроллер реактора деления. Он не столько дорог, сколько
// обозначает рубеж: до него игрок разбирает вещества, после него запускает
// цепную реакцию.
//
// Все ID GregTech сверены с живой переписью kubejs/exported/gtceu_item_census.json,
// все ID NuclearCraft — с data/nuclearcraft/ внутри установленного JAR 1.2.34.
ServerEvents.recipes((event) => {
  // --- Вход в домен. ---

  // Первая машина переработки. Свинец и кремень заменены сталью и
  // электроникой HV. Точную границу P5 -> P6 задаёт встроенный RecipeJS.stage,
  // который Threat Director синхронизирует из командного tech_epoch.
  event.remove({ id: 'nuclearcraft:manufactory' })
  event.shaped('nuclearcraft:manufactory', [
    'ABA',
    'CDC',
    'ABA'
  ], {
    A: 'gtceu:steel_plate',
    B: 'gtceu:hv_voltage_coil',
    C: 'gtceu:hv_electric_motor',
    D: 'gtceu:hv_machine_hull'
  }).stage('industrial_frontier:p6').id('industrial_frontier:nuclearcraft/manufactory')

  // Сплавная печь. Именно она даёт ферробор, прочный сплав и остальные
  // конструкционные материалы домена.
  event.remove({ id: 'nuclearcraft:alloy_smelter' })
  event.shaped('nuclearcraft:alloy_smelter', [
    'ABA',
    'CDC',
    'ABA'
  ], {
    A: 'gtceu:steel_plate',
    B: 'gtceu:hv_sensor',
    C: 'minecraft:blast_furnace',
    D: 'gtceu:hv_machine_hull'
  }).stage('industrial_frontier:p6').id('industrial_frontier:nuclearcraft/alloy_smelter')

  // --- Рубеж цепной реакции. ---
  //
  // Контроллер собирается из деталей самого NuclearCraft — это его домен, и
  // переписывать реакторную физику сборка не имеет права. Добавлен один узел
  // GregTech: манипулятор HV как символ того, что реактором управляет
  // автоматика, а не рука игрока.
  event.remove({ id: 'nuclearcraft:fission_reactor_controller' })
  event.shaped('nuclearcraft:fission_reactor_controller', [
    'ABA',
    'CDC',
    'ABA'
  ], {
    A: 'nuclearcraft:fission_reactor_casing',
    B: 'nuclearcraft:plate_advanced',
    C: 'nuclearcraft:basic_electric_circuit',
    D: 'gtceu:hv_robot_arm'
  }).stage('industrial_frontier:p6').id('industrial_frontier:nuclearcraft/fission_reactor_controller')

  // --- Полный комплект химической защиты. ---
  //
  // NuclearCraft содержит штатный рецепт сапог, но в живом recipe_index он не
  // зарегистрирован, тогда как остальные три части комплекта доступны. Здесь
  // повторён рецепт из установленного JAR, чтобы обязательная защита до пуска
  // не зависела от пропавшего datapack-рецепта.
  event.remove({ id: 'nuclearcraft:hazmat_boots' })
  event.shaped('nuclearcraft:hazmat_boots', [
    'BIB',
    'YLY',
    'YWY'
  ], {
    B: 'nuclearcraft:bioplastic',
    I: '#forge:ingots/steel',
    L: 'minecraft:leather_boots',
    W: 'minecraft:black_wool',
    Y: 'nuclearcraft:light'
  }).stage('industrial_frontier:p6').id('industrial_frontier:nuclearcraft/hazmat_boots')

  // --- Что НЕ открывается в шестой эпохе. ---
  //
  // NuclearCraft содержит не только деление. В нём есть синтез, линейные и
  // кольцевые ускорители, камера мишеней и кугельблиц — управляемая чёрная
  // дыра. По эпохам сборки это P7 и P8: стратегический комплекс и поздняя
  // энергетика. Открыть их вместе с первой АЭС значило бы отдать три эпохи
  // содержимого за один рубеж.
  //
  // Удаляются только контроллеры — сердце каждой установки. Детали, обмотки и
  // охладители остаются в JEI: игрок видит, что впереди, и понимает, что это
  // впереди, а не недоступно навсегда.
  const laterEpochs = [
    'nuclearcraft:fusion_core',
    'nuclearcraft:linear_accelerator_controller',
    'nuclearcraft:ring_accelerator_controller',
    'nuclearcraft:beam_diverter_controller',
    'nuclearcraft:target_chamber_controller',
    'nuclearcraft:collision_chamber_controller',
    'nuclearcraft:chamber_terminal',
    'nuclearcraft:quantum_transformer'
  ]
  laterEpochs.forEach((recipeId) => event.remove({ id: recipeId }))

  console.info(
    `[Recast] Ворота P6: 3 входных рецепта требуют team stage P6 и электронику HV, ${laterEpochs.length} установок синтеза и ускорителей отложены до своих эпох.`
  )
})
