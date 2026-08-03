// Ступени AE2 после входа в домен.
//
// Контракт входа (m5_ae2_entry_contract.js) открывает хранение и терминал в
// эпоху P5 по цене MV. Но AE2 — не один переключатель: между «вижу свои сундуки
// одним списком» и «система собирает за меня всё» лежит настоящая дистанция,
// и документ требует пройти её ступенями, а не одним рецептом.
//
//   P5 / MV   хранение, терминал, шины, сеть        открыто контрактом входа
//   HV        автосборка: процессор крафта и сборщик
//   EV        ускорение: параллельные потоки сборки
//
// Смысл ступеней простой. Хранение убирает беготню по сундукам — это честная
// награда за электрификацию. Автосборка убирает сам крафт, и её нельзя выдавать
// одновременно с хранением, иначе поезда, трубы и буферы теряют смысл в тот же
// вечер, когда игрок собрал первый терминал.
ServerEvents.recipes((event) => {
  // --- Ступень HV. Автосборка. ---

  // Процессор крафта. Штатный стоит железа; здесь — алюминий эпохи, оба
  // процессора AE2 и датчик HV в сердцевине.
  event.remove({ id: 'ae2:network/crafting/cpu_crafting_unit' })
  event.shaped('ae2:crafting_unit', [
    'ABA',
    'CDC',
    'ABA'
  ], {
    A: 'gtceu:aluminium_plate',
    B: 'ae2:calculation_processor',
    C: 'ae2:logic_processor',
    D: 'gtceu:hv_sensor'
  }).id('industrial_frontier:m5/ae2_stage/crafting_unit')

  // Молекулярный сборщик — рука, которая собирает вместо игрока. Верстак в
  // центре заменён на манипулятор HV: это машина, а не стол.
  event.remove({ id: 'ae2:network/crafting/molecular_assembler' })
  event.shaped('ae2:molecular_assembler', [
    'ABA',
    'CDE',
    'ABA'
  ], {
    A: 'gtceu:aluminium_plate',
    B: 'ae2:quartz_glass',
    C: 'ae2:annihilation_core',
    D: 'gtceu:hv_robot_arm',
    E: 'ae2:formation_core'
  }).id('industrial_frontier:m5/ae2_stage/molecular_assembler')

  // --- Ступень EV. Ускорение. ---
  //
  // Ускоритель не обязателен: без него автосборка работает, просто по одному
  // заданию за раз. Поэтому он и стоит эпоху дороже — это плата за параллельность
  // уже работающей фабрики, а не за вход в неё.
  event.remove({ id: 'ae2:network/crafting/cpu_crafting_accelerator' })
  event.shapeless('ae2:crafting_accelerator', [
    'ae2:crafting_unit',
    'ae2:engineering_processor',
    'gtceu:ev_emitter'
  ]).id('industrial_frontier:m5/ae2_stage/crafting_accelerator')

  console.info(
    '[Recast] Ступени AE2: хранение P5/MV открыто входным контрактом, автосборка перенесена за HV, ускорение — за EV.'
  )
})
