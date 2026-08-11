// Ворота космической эпохи P7: два стека, две разные проблемы.
//
// GCYR трогать не нужно, и это установлено разбором, а не предположением.
// Мод является аддоном GregTech и раздаёт свои рецепты через его лестницу
// напряжений: скафандр и его ткань стоят схем EV, базовый мотор — силового
// толкателя, продвинутый — усиленного, элитный — гравитационного двигателя,
// фотоэлемент — схем LuV, контроллер сферы Дайсона — схем UHV. То есть
// эпохальный замок у GCYR уже свой собственный и совпадает с лестницей
// сборки. Второй замок поверх него был бы дублем.
//
// Creating Space — обратный случай. Его стол проектирования двигателя стоит
// шести досок и гладкого камня, корпус — алюминия и кобальта, управление —
// механизмов Create. Космос открывался в первой эпохе: до стали, до
// электричества, до города и до атомной программы. Глубокий добровольный путь
// оставался глубоким, но переставал быть поздним.
//
// Поэтому здесь восемь рецептов входа. Они не отменяют конструктор двигателя
// и не упрощают его: 223 рецепта Creating Space, включая 97 последовательных
// сборок и всю химию газов, остаются нетронутыми. Меняется только момент,
// когда игрок к ним подходит.
//
// Характер мода сохранён намеренно: в каждом рецепте остаётся механизм Create,
// а эпоху обозначает один узел GregTech уровня EV. Ракета Creating Space
// по-прежнему собирается руками инженера, а не покупается за схему.
//
// Все ID GregTech сверены с живой переписью kubejs/exported/gtceu_item_census.json,
// ID Create — с assets/create/lang/en_us.json в JAR 6.0.8, ID Creating Space —
// с data/creatingspace/recipes/ в JAR 1.7.13.
ServerEvents.recipes((event) => {
  // --- Проектирование и корпус. ---

  // Стол проектирования — вход в конструктор двигателя. Штатно это доски и
  // гладкий камень; здесь это рабочее место инженера с измерительным трактом.
  event.remove({ id: 'creatingspace:rocket_engineer_table' })
  event.shaped('creatingspace:rocket_engineer_table', [
    'TTT',
    'MSM',
    'PPP'
  ], {
    T: 'gtceu:titanium_plate',
    M: 'create:precision_mechanism',
    S: 'gtceu:ev_sensor',
    P: 'create:sturdy_sheet'
  }).id('industrial_frontier:creating_space/rocket_engineer_table')

  // Корпус ступени. Алюминий остаётся несущим материалом, титан добавляет то,
  // без чего корпус не держит ни давление, ни нагрев.
  event.remove({ id: 'creatingspace:rocket_casing' })
  event.shaped('creatingspace:rocket_casing', [
    'TAT',
    'ATA',
    'TAT'
  ], {
    T: 'gtceu:titanium_plate',
    A: 'gtceu:aluminium_plate'
  }).id('industrial_frontier:creating_space/rocket_casing')

  // Управление. Форма рецепта сохранена, электронные лампы заменены
  // излучателями EV: ракетой управляет телеметрия, а не редстоун-сигнал.
  event.remove({ id: 'creatingspace:rocket_controls' })
  event.shaped('creatingspace:rocket_controls', [
    'ERE',
    'ECE',
    'TTT'
  ], {
    E: 'gtceu:ev_emitter',
    R: 'create:redstone_link',
    C: 'create:controls',
    T: 'gtceu:titanium_plate'
  }).id('industrial_frontier:creating_space/rocket_controls')

  // Бортовой генератор ступени.
  event.remove({ id: 'creatingspace:rocket_generator' })
  event.shaped('creatingspace:rocket_generator', [
    'TAT',
    'TPT',
    'THT'
  ], {
    T: 'gtceu:titanium_plate',
    A: 'create:shaft',
    P: 'creatingspace:sturdy_propeller',
    H: 'gtceu:ev_machine_hull'
  }).id('industrial_frontier:creating_space/rocket_generator')

  // --- Газы, криогеника и герметизация. ---
  //
  // Это второй вход в тот же домен: без кислорода и жидкого топлива ракета
  // не летит, а без герметизатора нет обитаемого объёма. Закрыть только
  // корпус и оставить открытой химию значило бы закрыть половину двери.

  // Сжижение воздуха — источник кислорода и азота.
  event.remove({ id: 'creatingspace:air_liquefier' })
  event.shaped('creatingspace:air_liquefier', [
    ' T ',
    'CFC',
    ' P '
  ], {
    T: 'gtceu:titanium_plate',
    C: 'create:brass_casing',
    F: 'create:encased_fan',
    P: 'gtceu:ev_electric_pump'
  }).id('industrial_frontier:creating_space/air_liquefier')

  // Механический электролиз воды: водород и кислород.
  event.remove({ id: 'creatingspace:mechanical_electrolyzer' })
  event.shaped('creatingspace:mechanical_electrolyzer', [
    'XSX',
    'VVV',
    'GHG'
  ], {
    X: 'create:copper_casing',
    S: 'create:shaft',
    V: 'gtceu:ev_voltage_coil',
    G: 'create:golden_sheet',
    H: 'gtceu:ev_machine_hull'
  }).id('industrial_frontier:creating_space/mechanical_electrolyzer')

  // Криогенный бак. Изоляция — фторопласт: холод держит не шерсть, а
  // материал, который не течёт и не намокает.
  event.remove({ id: 'creatingspace:cryogenic_tank' })
  event.shaped('creatingspace:cryogenic_tank', [
    'TFT',
    'FKF',
    'TFT'
  ], {
    T: 'gtceu:titanium_plate',
    F: 'gtceu:polytetrafluoroethylene_plate',
    K: 'create:fluid_tank'
  }).id('industrial_frontier:creating_space/cryogenic_tank')

  // Герметизатор объёма. Он же — первая машина внеземной базы.
  event.remove({ id: 'creatingspace:oxygen_sealer' })
  event.shaped('creatingspace:oxygen_sealer', [
    'TRT',
    'CPC',
    'CCC'
  ], {
    T: 'gtceu:titanium_plate',
    R: 'create:propeller',
    C: 'create:copper_casing',
    P: 'gtceu:ev_electric_pump'
  }).id('industrial_frontier:creating_space/oxygen_sealer')

  console.info(
    '[Recast] Ворота P7: восемь узлов Creating Space перенесены за титан и электронику EV; GCYR не тронут — его лестница уже принадлежит GregTech.'
  )
})
