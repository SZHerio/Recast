// Контракт входа в цифровую фабрику AE2. Первый долг M5.
//
// В M2 были удалены семь штатных входных рецептов AE2 с пометкой «заменяющий
// контракт пишется в M5». Пометка выполняется здесь.
//
// Замок эпохи стоит на трёх блоках, а не на каждом расходнике. Проверка по
// данным AE2 15.4.10 показала, где именно проходит настоящая граница домена:
//
//   * ae2:charged_certus_quartz_crystal производит ровно один рецепт —
//     data/ae2/recipes/charger/charged_certus_quartz_crystal.json типа
//     ae2:charger. Без блока зарядника заряженного кварца не существует, а без
//     него не существует ни fluix, ни кристаллов, ни резонансного генератора;
//   * ae2:printed_silicon и три ae2:printed_*_processor производит только
//     пресс ae2:inscriber;
//   * энергия попадает в сеть AE только через ae2:energy_acceptor.
//
// Поэтому эпоху держат зарядник, пресс и приёмник энергии. Они получают
// промышленную цену уровня MV: сталь эпохи P2 и электрические узлы, которые
// раньше P5 собрать нечем. Остальные четыре рецепта восстанавливаются в
// штатном виде — второй замок на расходнике, стоящем за уже закрытой машиной,
// был бы декоративной сложностью, запрещённой рецептурной конституцией.
//
// Все ID GregTech взяты из живой переписи kubejs/exported/gtceu_item_census.json,
// все ID AE2 — из data/ae2/recipes/ внутри JAR мода. Ничего не выдумано.
ServerEvents.recipes((event) => {
  // --- Ступень 1. Три блока, которые открывают домен. ---
  //
  // Форма рецептов сохранена от AE2: игрок узнаёт знакомую схему и видит, что
  // изменилась именно цена, а не блок. Железо и медь заменены на сталь и
  // электрические узлы MV.

  // Зарядник: корпус из стали и две катушки напряжения вместо медных слитков.
  event.shaped('ae2:charger', [
    'ABA',
    'A  ',
    'ABA'
  ], {
    A: 'gtceu:steel_plate',
    B: 'gtceu:mv_voltage_coil'
  }).id('industrial_frontier:ae2/charger')

  // Пресс печатает кремний и процессоры, поэтому ему нужны настоящие
  // электрические поршни и мотор, а не липкий поршень из красного камня.
  event.shaped('ae2:inscriber', [
    'ABA',
    'C A',
    'ABA'
  ], {
    A: 'gtceu:steel_plate',
    B: 'gtceu:mv_electric_piston',
    C: 'gtceu:mv_electric_motor'
  }).id('industrial_frontier:ae2/inscriber')

  // Приёмник энергии — единственная точка, где FE входит в сеть AE. Корпус
  // машины MV в центре говорит прямо: это стык двух энергетических сетей,
  // а не переходник из слитка меди.
  event.shaped('ae2:energy_acceptor', [
    'ABA',
    'BCB',
    'ABA'
  ], {
    A: 'gtceu:steel_plate',
    B: 'ae2:quartz_glass',
    C: 'gtceu:mv_machine_hull'
  }).id('industrial_frontier:ae2/energy_acceptor')

  // --- Ступень 2. Четыре расходника в штатном виде. ---
  //
  // Fluix. Рецепт требует заряженный кварц, то есть уже стоит за зарядником.
  // Кроме того, Create поставляет ровно этот же процесс в миксере
  // (data/create/recipes/mixing/compat/ae2/fluix_crystal.json, те же входы,
  // тот же выход 2). Пока миксер существует, удаление рецепта AE2 не закрывало
  // ничего — оно лишь прятало ручной вариант первой партии.
  event.custom({
    type: 'ae2:transform',
    circumstance: { type: 'fluid', tag: 'minecraft:water' },
    ingredients: [
      { item: 'ae2:charged_certus_quartz_crystal' },
      { item: 'minecraft:redstone' },
      { item: 'minecraft:quartz' }
    ],
    result: { count: 2, item: 'ae2:fluix_crystal' }
  }).id('industrial_frontier:ae2/fluix_crystals')

  // Три процессора. Пресс уже заперт, а сами процессоры расходуются десятками
  // в каждом устройстве ME, поэтому их цена остаётся штатной.
  // ID выписаны целиком, а не собраны из кусков: линтер сверяет их с реестром
  // стабильных идентификаторов по тексту файла.
  const processors = [
    ['industrial_frontier:ae2/calculation_processor', 'ae2:printed_calculation_processor', 'ae2:calculation_processor'],
    ['industrial_frontier:ae2/engineering_processor', 'ae2:printed_engineering_processor', 'ae2:engineering_processor'],
    ['industrial_frontier:ae2/logic_processor', 'ae2:printed_logic_processor', 'ae2:logic_processor']
  ]

  processors.forEach(([recipeId, printed, result]) => {
    event.custom({
      type: 'ae2:inscriber',
      ingredients: {
        bottom: { item: 'ae2:printed_silicon' },
        middle: { item: 'minecraft:redstone' },
        top: { item: printed }
      },
      mode: 'press',
      result: { item: result }
    }).id(recipeId)
  })

  // --- Ступень 3. Владение доменом. ---
  //
  // Сборщик NuclearCraft собирает те же три процессора AE2 из тех же печатных
  // пластин (data/nuclearcraft/recipes/assembler/ae2_*_processor.json). Это
  // второй владелец чужого домена и обход пресса AE2. NuclearCraft, кроме
  // того, стоит в сборке по зарегистрированному отклонению
  // industrial_frontier:deviation/nuclear_installed_early, условие которого —
  // «до своей волны он не получает ни рецептов, ни квестов». Маршрут удаляется
  // до M6, где атомный домен разбирается целиком.
  const foreignProcessorRoutes = [
    'nuclearcraft:assembler/ae2_calculation_processor',
    'nuclearcraft:assembler/ae2_engineering_processor',
    'nuclearcraft:assembler/ae2_logic_processor'
  ]
  foreignProcessorRoutes.forEach((recipeId) => event.remove({ id: recipeId }))

  console.info(
    `[Recast] Контракт входа AE2 (P5): 3 блока по цене MV, 4 штатных расходника, ${foreignProcessorRoutes.length} чужих маршрута к процессорам удалены.`
  )
})
