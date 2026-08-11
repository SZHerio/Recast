// Ворота сетевого хранения.
//
// Tom's Simple Storage закрывает настоящую дыру: из всего хранения в сборке
// стоял только AE2, а он открывается лишь в пятой эпохе. До этого игрок
// половину прохождения живёт на сундуках и ручной сортировке.
//
// Но из коробки мод отдаёт всё сразу. Разбор его рецептов показал: терминал
// собирается из сундука, компаратора, стекла и светокамня — это первый игровой
// день. Беспроводной терминал стоит подзорной трубы и жемчуга Края. То есть без
// вмешательства сетевое хранение и беспроводной доступ приходят раньше первого
// слитка стали и обесценивают половину AE2.
//
// Здесь всё это разложено по эпохам. Правило простое и то же, что и в
// остальной сборке: инструмент появляется тогда, когда задача, которую он
// решает, уже начала болеть.
//
//   P1 — коннектор и терминал после первой механической линии. Сортировка
//        сундуков уже мешает производству, но дальние зоны ещё не нужны.
//   P2 — стальные кабели и удалённые складские участки.
//   P3 — крафт из сети. Это удобство эпохи электричества, а не выживания.
//   P4 — фильтры и эмиттер уровня, то есть автоматизация по количеству.
//   P5 — беспроводной доступ, и не раньше AE2: дальняя связь остаётся его
//        привилегией, а не заменой ему.
//   P6 — продвинутый беспроводной терминал как поздняя награда.
//
// Стоимость тоже переписана. Мод просил алмазы и жемчуг Края — материалы, к
// которым сборка относится иначе; вместо них идут андезитовый сплав, сталь,
// медь и схемы своей эпохи — то, что игрок к этому моменту уже производит.

const IF_STORAGE_GATE = [
  {
    id: 'toms_storage:ts.inventory_connector',
    epoch_ru: 'P1',
    pattern: ['ACA', 'PBP', 'ACA'],
    key: {
      A: 'create:andesite_alloy',
      C: 'create:cogwheel',
      P: '#minecraft:planks',
      B: '#forge:chests/wooden',
    },
  },
  {
    id: 'toms_storage:ts.storage_terminal',
    epoch_ru: 'P1',
    pattern: ['AGA', 'CBC', 'ARA'],
    key: {
      A: 'create:andesite_alloy',
      G: '#forge:glass',
      C: 'create:cogwheel',
      B: 'toms_storage:ts.inventory_connector',
      R: 'minecraft:redstone',
    },
  },
  {
    id: 'toms_storage:ts.inventory_cable',
    epoch_ru: 'P2',
    count: 8,
    pattern: ['SPS'],
    key: { S: 'gtceu:steel_plate', P: '#minecraft:planks' },
  },
  {
    id: 'toms_storage:ts.inventory_cable_connector',
    epoch_ru: 'P2',
    pattern: ['SCS', 'PMP', 'SCS'],
    key: {
      S: 'gtceu:steel_plate',
      C: 'gtceu:copper_single_cable',
      P: '#minecraft:planks',
      M: 'toms_storage:ts.inventory_cable',
    },
  },
  {
    id: 'toms_storage:ts.crafting_terminal',
    epoch_ru: 'P3',
    pattern: [' T ', 'CWC', ' M '],
    key: {
      T: 'toms_storage:ts.storage_terminal',
      C: 'gtceu:basic_electronic_circuit',
      W: 'minecraft:crafting_table',
      M: 'gtceu:lv_electric_motor',
    },
  },
  {
    id: 'toms_storage:ts.item_filter',
    epoch_ru: 'P4',
    pattern: ['RPR', 'PCP', 'RPR'],
    key: { R: 'minecraft:redstone', P: 'gtceu:steel_plate', C: 'gtceu:good_electronic_circuit' },
  },
  {
    id: 'toms_storage:ts.level_emitter',
    epoch_ru: 'P4',
    pattern: ['SCS', 'TMT', 'SCS'],
    key: {
      S: 'gtceu:steel_plate',
      C: 'gtceu:good_electronic_circuit',
      T: 'minecraft:redstone_torch',
      M: 'toms_storage:ts.inventory_cable',
    },
  },
  {
    id: 'toms_storage:ts.wireless_terminal',
    epoch_ru: 'P5',
    pattern: ['ACA', 'CTC', 'ACA'],
    key: {
      A: 'gtceu:aluminium_plate',
      C: 'gtceu:basic_integrated_circuit',
      T: 'toms_storage:ts.storage_terminal',
    },
  },
  {
    id: 'toms_storage:ts.adv_wireless_terminal',
    epoch_ru: 'P6',
    pattern: ['SCS', 'CTC', 'SCS'],
    key: {
      S: 'gtceu:stainless_steel_plate',
      C: 'gtceu:good_integrated_circuit',
      T: 'toms_storage:ts.wireless_terminal',
    },
  },
]

ServerEvents.recipes((event) => {
  let replaced = 0
  let failed = 0

  IF_STORAGE_GATE.forEach((entry) => {
    // Заводской рецепт снимается точным идентификатором предмета: удаление по
    // шаблону — зарегистрированное исключение и здесь не нужно.
    event.remove({ output: entry.id })

    try {
      event
        .shaped(Item.of(entry.id, entry.count || 1), entry.pattern, entry.key)
        .id(`industrial_frontier:storage/${entry.id.split(':')[1].replace('ts.', '')}`)
      replaced += 1
    } catch (error) {
      console.error(`[Recast] ОШИБКА ворот хранения: ${entry.id} (${entry.epoch_ru}) не пересобран: ${error}`)
      failed += 1
    }
  })

  // Остальное мод отдаёт по своим рецептам: рамки, покраска, ящик и прокси
  // ничего не открывают и на прогрессию не влияют.
  console.info(`[Recast] ворота хранения: пересобрано ${replaced} рецептов, отказов ${failed}`)
})
