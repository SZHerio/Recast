// Ворота поздних эпох P8–P9: высокоэнергетические циклы.
//
// Шестая эпоха отложила восемь установок NuclearCraft «до своих эпох». Эпоха
// пришла. Семь из восьми возвращаются здесь, восьмая не возвращается вовсе.
//
// Не возвращается ядро синтеза. Решение владельца от 4 августа 2026: синтезом
// в сборке владеют двое, и у каждого своя роль. Реактор синтеза GregTech —
// станок: в нём делают материалы, которых не существует больше нигде. Лазерная
// установка HBM — электростанция: десятки блоков, выстроенных по чертежу, и
// главный источник энергии финала. Третья копия того же самого сделала бы
// одну из двух бессмысленной.
//
// Семь установок возвращаются с добавленным узлом GregTech уровня IV. Причина
// не в цене: их собственные материалы — экстремальный сплав, нейтрониевая рама
// и пространственная смесь — и так делают их поздними. Узел IV нужен, чтобы
// рубеж был виден в самом рецепте, как это сделано у всех входов в домены,
// начиная с пятой эпохи.
//
// Термоядерная ветка HBM воротами не закрывается, и это проверено, а не
// предположено: её плазменная печь требует сверхпроводящей проволоки BSCCO,
// турбина — проволоки из шрабидия и квантовых схем. Лестница уже внутри мода,
// второй замок поверх неё был бы дублем — тот же вывод, что и по GCYR в M7.
//
// Все ID GregTech сверены с живой переписью kubejs/exported/gtceu_item_census.json,
// все ID и рецепты NuclearCraft — с data/nuclearcraft/recipes/ в JAR 1.2.33.
ServerEvents.recipes((event) => {
  // --- Ускорительный комплекс. ---
  //
  // Линейный ускоритель разгоняет частицы, кольцевой делает то же по кругу и
  // мощнее, отклонитель уводит луч в сторону, камеры принимают удар. Вместе
  // это единственный в сборке способ получить то, что не рождается ни в одном
  // реакторе и ни в одной печи.

  event.shaped('nuclearcraft:linear_accelerator_controller', [
    'PEP',
    'BFB',
    'PSP'
  ], {
    P: 'nuclearcraft:plate_elite',
    E: '#forge:ingots/extreme',
    B: 'nuclearcraft:basic_processor',
    F: 'nuclearcraft:accelerator_casing',
    S: 'gtceu:iv_sensor'
  }).id('industrial_frontier:m8/nuclearcraft/linear_accelerator')

  // В NuclearCraft 1.2.33 источник Ca-48 зарегистрирован и работает в
  // ускорителе, но ни один survival-рецепт его не производит. Без этого моста
  // ветвь Copernicium физически непроходима. IV-центрифуга моделирует одну
  // промышленную каскадную сепарацию: стек кальция проходит через четыре
  // расходных фильтра, десять обогащённых источников уходят в ускоритель, а
  // основная масса кальция возвращается в оборот. Один запуск даёт ровно
  // 50 000 000 ионов — точный расход одной мишени, поэтому ручного гринда нет.
  event.recipes.gtceu.centrifuge('industrial_frontier:m8/isotopes/calcium_48_source_batch')
    .itemInputs('64x gtceu:calcium_dust', '4x gtceu:item_filter')
    .itemOutputs('10x nuclearcraft:source_calcium_48', '54x gtceu:calcium_dust')
    .duration(2400)
    .EUt(7680)

  event.shaped('nuclearcraft:ring_accelerator_controller', [
    'PEP',
    'AFA',
    'PSP'
  ], {
    P: 'nuclearcraft:plate_elite',
    E: '#forge:ingots/extreme',
    A: 'nuclearcraft:advanced_processor',
    F: 'nuclearcraft:accelerator_casing',
    S: 'gtceu:iv_emitter'
  }).id('industrial_frontier:m8/nuclearcraft/ring_accelerator')

  event.shaped('nuclearcraft:beam_diverter_controller', [
    'PEP',
    'BFB',
    'PSP'
  ], {
    P: 'nuclearcraft:plate_elite',
    E: 'minecraft:compass',
    B: 'nuclearcraft:basic_processor',
    F: 'nuclearcraft:accelerator_casing',
    S: 'gtceu:iv_robot_arm'
  }).id('industrial_frontier:m8/nuclearcraft/beam_diverter')

  // --- Камеры. ---
  //
  // Камера мишеней принимает разогнанный луч, камера столкновений сводит два
  // луча навстречу. Это разные задачи и разная стоимость промаха.

  event.shaped('nuclearcraft:target_chamber_controller', [
    'PTP',
    'BFB',
    'PSP'
  ], {
    P: 'nuclearcraft:plate_elite',
    T: '#forge:ingots/tough_alloy',
    B: 'nuclearcraft:basic_processor',
    F: 'nuclearcraft:target_chamber_casing',
    S: 'gtceu:iv_field_generator'
  }).id('industrial_frontier:m8/nuclearcraft/target_chamber')

  event.shaped('nuclearcraft:collision_chamber_controller', [
    'PTP',
    'BFB',
    'PSP'
  ], {
    P: 'nuclearcraft:plate_elite',
    T: '#forge:plates/tough_alloy',
    B: 'nuclearcraft:basic_processor',
    F: 'nuclearcraft:target_chamber_casing',
    S: 'gtceu:luv_field_generator'
  }).id('industrial_frontier:m8/nuclearcraft/collision_chamber')

  event.shaped('nuclearcraft:chamber_terminal', [
    'CPC',
    'ENE',
    'CSC'
  ], {
    C: 'nuclearcraft:basic_electric_circuit',
    P: 'nuclearcraft:plate_extreme',
    E: '#forge:ingots/extreme',
    N: 'nuclearcraft:neutronium_frame',
    S: 'gtceu:iv_sensor'
  }).id('industrial_frontier:m8/nuclearcraft/chamber_terminal')

  // --- Вершина ускорительной ветки. ---
  //
  // Квантовый трансформатор превращает энергию в вещество. Он стоит дороже
  // всего остального в этой ветке и открывается последним — уже в девятой
  // эпохе, вместе с финальными мегапроектами.
  event.shaped('nuclearcraft:quantum_transformer', [
    'DCD',
    'ENE',
    'DGD'
  ], {
    D: '#forge:dusts/dimensional_blend',
    C: 'nuclearcraft:basic_electric_circuit',
    E: 'nuclearcraft:plate_extreme',
    N: 'nuclearcraft:neutronium_frame',
    G: 'gtceu:zpm_field_generator'
  }).id('industrial_frontier:m8/nuclearcraft/quantum_transformer')

  console.info(
    '[Recast] Ворота P8–P9: ускорительный комплекс открыт семью рецептами, ядро синтеза NuclearCraft не возвращается — синтезом владеют реактор GregTech и лазерная установка HBM.'
  )
})
