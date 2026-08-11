// Стенд сборки ступени и станция обслуживания роя.
//
// Две машины поздних эпох, обе закрывают обещание, данное текстом.
//
// Седьмая эпоха: космодром выдан городским контрактом из шести требований, но
// сборочного цеха ступеней в сборке не было — «сборочный цех с автоматической
// подачей корпусов и двигателей» оставался словами в описании контракта.
// Стенд превращает контракт в место, куда приходят корпус, бак и двигатель и
// откуда выходит готовая ступень.
//
// Девятая эпоха: мы написали, что сфера Дайсона изнашивается и что брошенная
// разрушается. Значит нужно место, где её чинят. Станция принимает изношенные
// секции роя и возвращает восстановленные — это и есть та самая ремонтная
// линия, которую требует мегапроект.
//
// Все имена блоков, текстур, звуков и наложений сверены с JAR gtceu 7.5.3.

// --- Стенд сборки ступени, P7 ---
GTCEuStartupEvents.registry('gtceu:recipe_type', (event) => {
  event.create('stage_assembly')
    .category('stage_assembly_category')
    .setEUIO('in')
    // Шесть входных предметов — потому что ступень и есть сборка из многих
    // крупных узлов: корпус, бак, двигатель, управление, теплозащита, кабель.
    // Две жидкости — топливо и рабочее тело для испытания. Один выход: ступень
    // либо собрана целиком, либо не собрана вовсе.
    .setMaxIOSize(6, 2, 1, 0)
    .setSlotOverlay(false, false, GuiTextures.FILTER_SLOT_OVERLAY)
    .setProgressBar(GuiTextures.PROGRESS_BAR_ARROW_MULTIPLE, FillDirection.LEFT_TO_RIGHT)
    .setSound(GTSoundEntries.ASSEMBLER)
})

GTCEuStartupEvents.registry('gtceu:machine', (event) => {
  event.create('stage_assembly_stand', 'multiblock')
    .rotationState(RotationState.NON_Y_AXIS)
    .recipeType('stage_assembly')
    .appearanceBlock(GTBlocks.CASING_ASSEMBLY_LINE)
    .recipeModifier(GTRecipeModifiers.OC_NON_PERFECT)
    // Стенд вертикальный и высокий: ступень собирается стоя, как на настоящем
    // космодроме. Пять уровней в высоту — это заметное сооружение, и оно
    // должно быть заметным: космодром по контракту стоит в зоне отчуждения, а
    // не прячется в подвале.
    .pattern((definition) =>
      FactoryBlockPattern.start()
        .aisle('AAA', 'AGA', 'AGA', 'AGA', 'AAA')
        .aisle('AGA', 'G#G', 'G#G', 'G#G', 'AGA')
        .aisle('AEA', 'AGA', 'AGA', 'AGA', 'AAA')
        .where('E', Predicates.controller(Predicates.blocks(definition.get())))
        .where('G', Predicates.blocks('gtceu:assembly_line_grating'))
        .where('#', Predicates.air())
        .where('A', Predicates.blocks('gtceu:assembly_line_casing')
          .setMinGlobalLimited(16)
          .or(Predicates.autoAbilities(definition.getRecipeTypes())))
        .build()
    )
    .workableCasingModel(
      'gtceu:block/casings/mechanic/machine_casing_assembly_line',
      'gtceu:block/multiblock/assembly_line'
    )
})

// --- Станция обслуживания роя, P9 ---
GTCEuStartupEvents.registry('gtceu:recipe_type', (event) => {
  event.create('swarm_servicing')
    .category('swarm_servicing_category')
    .setEUIO('in')
    // Вход: изношенная секция и ремонтный комплект. Выход: восстановленная
    // секция и невосстановимый остаток. Второй выход обязателен — иначе
    // ремонт становится бесплатным, а обслуживание сферы перестаёт быть
    // обязательством и превращается в формальность.
    .setMaxIOSize(2, 1, 2, 0)
    .setSlotOverlay(false, false, GuiTextures.FILTER_SLOT_OVERLAY)
    .setProgressBar(GuiTextures.PROGRESS_BAR_ARROW, FillDirection.LEFT_TO_RIGHT)
    .setSound(GTSoundEntries.MOTOR)
})

GTCEuStartupEvents.registry('gtceu:machine', (event) => {
  event.create('swarm_service_station', 'multiblock')
    .rotationState(RotationState.NON_Y_AXIS)
    .recipeType('swarm_servicing')
    .appearanceBlock(GTBlocks.CASING_PALLADIUM_SUBSTATION)
    .recipeModifier(GTRecipeModifiers.OC_NON_PERFECT)
    // Плоская широкая площадка с вычислительным ядром в центре: станция не
    // столько чинит руками, сколько считает, какие секции пора снимать с
    // орбиты. Отсюда компьютерные корпуса внутри и силовые по периметру.
    .pattern((definition) =>
      FactoryBlockPattern.start()
        .aisle('PPPPP', 'PPPPP')
        .aisle('PCCCP', 'P###P')
        .aisle('PCACP', 'P###P')
        .aisle('PCCCP', 'P###P')
        .aisle('PPEPP', 'PPPPP')
        .where('E', Predicates.controller(Predicates.blocks(definition.get())))
        .where('A', Predicates.blocks('gtceu:advanced_computer_casing'))
        .where('C', Predicates.blocks('gtceu:computer_casing'))
        .where('#', Predicates.air())
        .where('P', Predicates.blocks('gtceu:high_power_casing')
          .setMinGlobalLimited(20)
          .or(Predicates.autoAbilities(definition.getRecipeTypes())))
        .build()
    )
    .workableCasingModel(
      'gtceu:block/casings/hpca/high_power_casing',
      'gtceu:block/multiblock/power_substation'
    )
})
