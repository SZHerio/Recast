// Установка дезактивации и пост радиационного контроля.
//
// Шестая эпоха дала игроку регламент из пяти пунктов. Два из них до сих пор
// были обещаниями без механики:
//
//   «Загрязнение снимается, а не пережидается. Заражённые предметы и блоки
//    обрабатываются, а не выбрасываются в мир и не закапываются.»
//   «Дозиметр носится с собой, счётчик Гейгера стоит на входе в зону.»
//
// Снимать загрязнение было нечем, а «счётчик на входе в зону» существовал как
// пожелание. Здесь появляется и то, и другое.
//
// Дезактивация — мультиблок, потому что это участок, а не прибор: грязное
// заходит с одной стороны, чистое выходит с другой, а отход остаётся здесь и
// требует места. Контроль — простая машина: пост на входе, а не сооружение.
//
// Все имена блоков, текстур, звуков и наложений сверены с JAR gtceu 7.5.3.

// --- Дезактивация ---
GTCEuStartupEvents.registry('gtceu:recipe_type', (event) => {
  event.create('decontamination')
    .category('decontamination_category')
    .setEUIO('in')
    // Вход: загрязнённый предмет и дезактивирующий раствор. Выход: чистый
    // предмет и два потока отхода — жидкий и твёрдый концентрат. Ровно то, о
    // чём говорит регламент: загрязнение никуда не исчезает, оно
    // концентрируется и получает своё место хранения.
    .setMaxIOSize(2, 2, 1, 2)
    .setSlotOverlay(false, false, GuiTextures.FILTER_SLOT_OVERLAY)
    .setProgressBar(GuiTextures.PROGRESS_BAR_BATH, FillDirection.LEFT_TO_RIGHT)
    .setSound(GTSoundEntries.CHEMICAL)
})

GTCEuStartupEvents.registry('gtceu:machine', (event) => {
  event.create('decontamination_unit', 'multiblock')
    .rotationState(RotationState.NON_Y_AXIS)
    .recipeType('decontamination')
    .appearanceBlock(GTBlocks.CASING_STAINLESS_CLEAN)
    .recipeModifier(GTRecipeModifiers.OC_NON_PERFECT)
    // Шлюзовая схема: два отсека, разделённые фильтром. Грязная сторона —
    // свинцовые стены атомного корпуса, чистая — нержавейка. Так участок
    // читается с одного взгляда, и это не украшение: игрок должен видеть, где
    // проходит граница.
    .pattern((definition) =>
      FactoryBlockPattern.start()
        .aisle('AAA', 'AAA', 'AAA')
        .aisle('AFA', 'F#F', 'AFA')
        .aisle('CEC', 'CGC', 'CCC')
        .where('E', Predicates.controller(Predicates.blocks(definition.get())))
        .where('F', Predicates.blocks('gtceu:filter_casing'))
        .where('G', Predicates.blocks('gtceu:tempered_glass'))
        .where('#', Predicates.air())
        .where('A', Predicates.blocks('gtceu:atomic_casing')
          .setMinGlobalLimited(8))
        .where('C', Predicates.blocks('gtceu:clean_machine_casing')
          .setMinGlobalLimited(4)
          .or(Predicates.autoAbilities(definition.getRecipeTypes())))
        .build()
    )
    .workableCasingModel(
      'gtceu:block/casings/solid/machine_casing_clean_stainless_steel',
      'gtceu:block/multiblock/cleanroom'
    )
})

// --- Пост радиационного контроля ---
GTCEuStartupEvents.registry('gtceu:recipe_type', (event) => {
  event.create('radiation_survey')
    .category('radiation_survey_category')
    .setEUIO('in')
    // Один предмет входит, тот же выходит: пост ничего не производит и ничего
    // не расходует, кроме энергии и времени. Он отвечает на единственный
    // вопрос — можно ли это выносить из зоны.
    .setMaxIOSize(1, 0, 1, 0)
    .setSlotOverlay(false, false, GuiTextures.FILTER_SLOT_OVERLAY)
    .setProgressBar(GuiTextures.PROGRESS_BAR_ARROW, FillDirection.LEFT_TO_RIGHT)
    .setSound(GTSoundEntries.SCIENCE)
})

GTCEuStartupEvents.registry('gtceu:machine', (event) => {
  // Простая машина трёх тиров, а не мультиблок: это прибор на входе в зону.
  // Тир определяет скорость проверки — на большом объекте очередь у поста
  // становится заметной, и это правильное давление в сторону второго поста.
  event.create('radiation_checkpoint', 'simple')
    .tiers(GTValues.LV, GTValues.MV, GTValues.HV)
    .definition((tier, builder) =>
      builder
        .rotationState(RotationState.NON_Y_AXIS)
        .workableTieredHullModel('gtceu:block/machines/scanner')
        .recipeType('radiation_survey')
    )
})
