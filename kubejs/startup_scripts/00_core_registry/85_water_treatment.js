GTCEuStartupEvents.registry('gtceu:machine', (event) => {
  // Цепочка вызовов здесь намеренно разорвана.
  //
  // Первая сборка этой машины валила игру на запуске: GregTech сообщал
  // «missing pattern while creating multiblock water_treatment_plant», хотя
  // схема была задана. Причина в том, что методы билдера возвращают обобщённый
  // тип, и в длинной цепочке Rhino теряет его — часть вызовов уходит впустую.
  // Отдельные вызовы на переменной такого не допускают.
  // Схема задаётся в одной цепочке от event.create до pattern.
  //
  // Прежняя версия разбивала вызовы на отдельные строки по переменной machine,
  // предполагая, что Rhino теряет тип в длинной цепочке. Причина оказалась
  // обратной: построитель GregTech возвращает на каждом шаге новый объект,
  // поэтому pattern применялся не к тому экземпляру, который потом
  // регистрировался. Схема задавалась и уходила в пустоту — отсюда дословное
  // «missing pattern while creating multiblock».
  event.create('water_treatment_plant', 'multiblock')
    .rotationState(RotationState.NON_Y_AXIS)
    .recipeType('water_treatment')
    // Причина четырёх неудачных попыток найдена бинарным поиском по пробнику:
    // ломался именно этот вызов. Поле GTBlocks.CASING_WATERTIGHT в моде есть,
    // но к моменту регистрации машины оно ещё не готово, и построитель молча
    // теряет схему — отсюда «missing pattern» при верном во всём остальном коде.
    //
    // Корпус внешнего вида отвечает только за то, как машина выглядит в
    // собранном виде, поэтому берётся проверенный сплошной стальной. Сама
    // постройка по-прежнему требует водонепроницаемых корпусов: они заданы
    // предикатом схемы ниже и на них ничего не менялось.
    .appearanceBlock(GTBlocks.CASING_STEEL_SOLID)
    .recipeModifier(GTRecipeModifiers.OC_NON_PERFECT)
    .pattern((definition) =>
    FactoryBlockPattern.start()
      .aisle('CCC', 'CGC', 'CCC')
      .aisle('CGC', 'GFG', 'CGC')
      .aisle('CEC', 'CGC', 'CCC')
      .where('E', Predicates.controller(Predicates.blocks(definition.get())))
      .where('F', Predicates.blocks('gtceu:filter_casing'))
      .where('G', Predicates.blocks('gtceu:tempered_glass'))
      .where('C', Predicates.blocks('gtceu:watertight_casing')
        .setMinGlobalLimited(12)
        .or(Predicates.autoAbilities(definition.getRecipeTypes())))
      .build()
    )
    .workableCasingModel(
      'gtceu:block/casings/pipe/machine_casing_pipe_steel',
      'gtceu:block/multiblock/evaporation_plant'
    )
})
