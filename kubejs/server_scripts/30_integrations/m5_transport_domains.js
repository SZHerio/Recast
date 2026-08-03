// Разделение транспортных доменов P5.
//
// Решение от 1 августа 2026 года: груз — Create и Steam 'n' Rails, пассажиры —
// MTR, вода — Little Logistics. Здесь это решение перестаёт быть текстом и
// становится правилом игры.
//
// Четыре слоя и их границы:
//
//   грузовая магистраль   Create + Steam 'n' Rails, рельсы и составы
//   пассажирский транспорт MTR, узлы, платформы и расписание
//   водные пути           Little Logistics, буксиры, баржи и причалы
//   последняя миля        Ultimate Car Mod и ручная логистика внутри района
//
// Пересечений было два, и оба закрываются.
ServerEvents.recipes((event) => {
  // --- 1. Little Logistics не держит вторую наземную железную дорогу. ---
  //
  // Мод поставляет собственные локомотивы и вагоны на ванильных рельсах. Это
  // третья рельсовая система рядом с Create и MTR: те же задачи, свои рецепты,
  // свой перевод и своя нагрузка. Документ домена решает это прямо: «её рецепты
  // скрываются» (GLOBAL_TECH_CITY_CURSEFORGE_AUDIT §3.5).
  //
  // Удаляются только транспортные средства и их выделенные рельсы. Водная
  // часть — буксир, баржи, причалы, направляющие рельсы буксира, насосы и
  // маршрутизаторы — остаётся целиком: это и есть суверенная роль мода.
  const landRailRoutes = [
    'littlelogistics:seater_car',
    'littlelogistics:chest_car',
    'littlelogistics:fluid_car',
    'littlelogistics:barrel_car',
    'littlelogistics:steam_locomotive',
    'littlelogistics:energy_locomotive',
    'littlelogistics:locomotive_route',
    'littlelogistics:locomotive_dock_rail',
    'littlelogistics:car_dock_rail'
  ]
  landRailRoutes.forEach((recipeId) => event.remove({ id: recipeId }))

  // --- 2. MTR — городская система пятой эпохи, а не постройка первого дня. ---
  //
  // Штатные рецепты MTR стоят железа, брёвен и стекла, то есть вся пассажирская
  // сеть собирается в P0. Вход в систему — ровно два предмета: узел пути
  // (mtr:rail) и пульт (mtr:dashboard). Без узлов путь не проложить, без пульта
  // маршрут не запустить, поэтому эпоху держат они, а не двадцать рецептов
  // соединителей.
  //
  // Новая цена говорит, что это муниципальная инфраструктура: сталь эпохи P2,
  // электрический двигатель MV и датчик MV для сигнализации.
  event.remove({ id: 'mtr:rail_node' })
  event.remove({ id: 'mtr:railway_dashboard' })

  event.shaped(Item.of('mtr:rail', 32), [
    'AAA',
    'BCB',
    'AAA'
  ], {
    A: 'gtceu:steel_plate',
    B: 'gtceu:steel_rod',
    C: 'gtceu:mv_electric_motor'
  }).id('industrial_frontier:m5/mtr/rail_node')

  event.shaped('mtr:dashboard', [
    'AAA',
    'BCD',
    'AAA'
  ], {
    A: 'gtceu:steel_plate',
    B: 'gtceu:mv_sensor',
    C: 'minecraft:glass_pane',
    D: 'gtceu:mv_emitter'
  }).id('industrial_frontier:m5/mtr/railway_dashboard')

  console.info(
    `[Recast] Транспортные домены P5: снято ${landRailRoutes.length} наземных рельсовых маршрутов Little Logistics, вход MTR перенесён за сталь и электронику MV.`
  )
})
