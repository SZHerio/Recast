// Ворота стратегической эпохи P7: домен HBM-NTM Rebirth.
//
// Статический разбор JAR hbm_ntm_rebirth-0.4.1beta показал две вещи, которые
// определили всю форму этих ворот.
//
// Первая: домен машин мода физически недостижим. Из 704 блоков рецепт имеют
// 145. Сборочная машина — корень 586 рецептов, из которых собираются пресс,
// шреддер, химзавод, центрифуга, пурекс и всё остальное, — производится
// только сама собой: data/hbm_ntm_rebirth/recipes/assembly_machine/assembler.json
// требует hbm_ntm_rebirth:motor и hbm_ntm_rebirth:circuit_analog, а те делаются
// прессом, который делается сборочной машиной. Другого рецепта на неё в JAR
// нет. Поэтому сборка не «переносит» вход в домен, а создаёт его впервые.
//
// Вторая: то, что доступно без сборочной машины, доступно слишком рано.
// Наковальня стоит железа и открывает 52 рецепта собственной металлургии
// HBM — печи, дукты, кабели — в первой эпохе. Это вход в домен седьмой эпохи
// через верстак первой.
//
// Отсюда три рецепта входа: две наковальни и сборочная машина. Все три
// переписаны на титан, вольфрамовую сталь и электронику EV — это седьмая
// эпоха и ничто раньше. Остальные 2357 рецептов мода не тронуты.
//
// Оружейный слой снят решением владельца от 3 августа 2026: 121 рецепт
// стрелкового оружия и 112 брони собирались в обычном верстаке и дублировали
// TaCZ и Epic Knights по более дешёвой цене — верстак против стального
// верстака P2 и эпохальных замков. Боевые роли остаются за существующим
// стеком Better Combat + Epic Knights + TaCZ + Create Big Cannons.
//
// Вместе с оружием снято всё, что вело только к нему: 89 рецептов боеприпасов,
// 45 модулей брони, две оставшиеся станции и 14 рецептов боезапаса в самой
// сборочной машине. Проверено обходом графа: ядерная ветка — заряды, шахтные
// пусковые, станция сборки ракет и боевые части — не проходит ни через
// патронный пресс, ни через оружейный или бронетехнический стол. Её 72
// предмета собираются сборочной машиной, солидификатором, шреддером, пурексом,
// химзаводом, прессом и камерой облучения. Мёртвая ветка в JEI хуже, чем её
// отсутствие: игрок тратит время на то, что никуда не ведёт.
//
// Стратегический заряд, шахтные пусковые и станция сборки ракет НЕ снимаются:
// это единственное, что даёт HBM уникальную роль рядом с NuclearCraft, и
// именно поэтому седьмая эпоха стратегическая, а не вторая атомная. Правила
// его применения живут в m7_strategic_programme.js.
//
// Все ID GregTech сверены с живой переписью kubejs/exported/gtceu_item_census.json,
// все ID и пути рецептов HBM — с data/hbm_ntm_rebirth/ внутри JAR 0.4.1beta.

// Удаление по шаблону — зарегистрированное исключение из правила сборки
// «удаляем явным списком ID, сверенным с JAR»: выписывать 367 идентификаторов
// нереально, а папка рецептов у мода и есть его собственная граница слоя.
// Плата за исключение — обязательная сверка с числом из JAR. Обновление мода
// поменяет набор молча, и без счётчика об этом сообщил бы игрок, а не проверка.
function ifRemoveFolder(event, folder, expected) {
  let removed = -1
  try {
    removed = event.remove({ id: new RegExp(`^hbm_ntm_rebirth:${folder}/`) })
  } catch (error) {
    console.error(
      `[Recast] ОШИБКА ворот P7: фильтр по шаблону не принят для hbm_ntm_rebirth:${folder}/ (${error}). Слой НЕ снят.`
    )
    return -1
  }
  if (removed !== expected) {
    console.error(
      `[Recast] ВНИМАНИЕ ворот P7: из hbm_ntm_rebirth:${folder}/ снято ${removed} рецептов вместо ожидаемых ${expected}. Набор рецептов мода изменился — сверьте JAR и обновите число.`
    )
  }
  return removed
}

ServerEvents.recipes((event) => {
  // --- Вход в домен: кузнечный слой. ---
  //
  // Наковальня в HBM — не средневековый инструмент, а первая ступень его
  // металлургии: через неё идут печи, жидкостные дукты и силовые кабели.
  // Штатно железная стоит девяти слитков железа, то есть первого дня.
  event.remove({ id: 'hbm_ntm_rebirth:machines/anvil_iron' })
  event.shaped('hbm_ntm_rebirth:anvil_iron', [
    'TTT',
    ' W ',
    'TTT'
  ], {
    T: 'gtceu:titanium_plate',
    W: 'gtceu:tungsten_steel_plate'
  }).id('industrial_frontier:m7/hbm/anvil_iron')

  // Свинцовая наковальня — следующий тир того же слоя. Она обязана стоить
  // дороже железной, иначе тир перестаёт что-либо значить.
  event.remove({ id: 'hbm_ntm_rebirth:machines/anvil_lead' })
  event.shaped('hbm_ntm_rebirth:anvil_lead', [
    'WWW',
    ' H ',
    'WWW'
  ], {
    W: 'gtceu:tungsten_steel_plate',
    H: 'gtceu:ev_machine_hull'
  }).id('industrial_frontier:m7/hbm/anvil_lead')

  // --- Вход в домен: сборочная машина. ---
  //
  // Рецепт создаётся, а не переписывается: в моде его нет вовсе. Цена
  // назначена по седьмой эпохе, потому что за этой машиной стоит весь
  // остальной мод — 586 рецептов, включая пурекс, РБМК и стратегический слой.
  event.shaped('hbm_ntm_rebirth:machine_assembly_machine', [
    'PCP',
    'MHM',
    'PRP'
  ], {
    P: 'gtceu:titanium_plate',
    C: 'gtceu:ev_voltage_coil',
    M: 'gtceu:ev_electric_motor',
    H: 'gtceu:ev_machine_hull',
    R: 'gtceu:ev_robot_arm'
  }).id('industrial_frontier:m7/hbm/assembly_machine')

  // --- Оружейный слой. ---
  //
  // Четыре папки — четыре границы слоя, и каждая проверена на связи наружу.
  // Единственные выходы, которые потреблялись за их пределами, — миномётный
  // заряд, свинцовая обшивка и чёрный алмаз, — уходили внутрь того же слоя.
  const removedWeapons = ifRemoveFolder(event, 'weapon', 121)
  const removedArmour = ifRemoveFolder(event, 'armor', 112)
  const removedAmmo = ifRemoveFolder(event, 'ammo_press', 89)
  const removedModules = ifRemoveFolder(event, 'armor_modules', 45)

  // Две станции этого слоя. Третья — оружейный стол — снята вместе с папкой
  // weapon/, потому что её собственный рецепт лежит именно там.
  event.remove({ id: 'hbm_ntm_rebirth:machines/ammo_press' })
  event.remove({ id: 'hbm_ntm_rebirth:machines/armor_table' })

  // Боезапас, который делается не на станции, а в сборочной машине, и потому
  // пережил бы удаление папок: крупный калибр, реактивные снаряды РСЗО,
  // химические артиллерийские снаряды и урановый сердечник ядерного снаряда.
  // РСЗО и химическая артиллерия — не шахтная пусковая: роль полевой
  // артиллерии в сборке принадлежит Create Big Cannons с волны M5.
  const assemblerAmmunition = [
    '50bmgbypass', '50bmgsm', 'boybullet',
    'himarslarge', 'himarslargetb', 'himarssmall', 'himarssmallhe',
    'himarssmalllava', 'himarssmallnuke', 'himarssmalltb', 'himarssmallwp',
    'shell_chlorine', 'shell_mustard', 'shell_phosgene'
  ]
  assemblerAmmunition.forEach((name) =>
    event.remove({ id: `hbm_ntm_rebirth:assembly_machine/${name}` }))

  // --- Приборы, у которых уже есть владелец. ---
  //
  // Детектор загрязнения читает pollution HBM, который выключен вместе с его
  // мировой радиацией: экологией сборки владеют Pollution of the Realms и
  // Advanced Chimneys.
  // Сканер плотности руд и детектор нефти читают геологию HBM, которая
  // отключена датапаком: рудами владеет GregTech, нефтью — Immersive Petroleum.
  const replacedInstruments = [
    'pollution_detector',
    'ore_density_scanner',
    'oil_detector'
  ]
  replacedInstruments.forEach((name) => event.remove({ id: `hbm_ntm_rebirth:tools/${name}` }))

  // Счётчик Гейгера HBM — второй радиационный прибор, и единой моделью дозы
  // решением владельца остаётся NuclearCraft. Снимать его, однако, почти нечего:
  // в JAR предмет делается только из блока, а блок — только из предмета, и
  // третьего рецепта нет. Это тот же замкнутый круг, что и у сборочной машины,
  // то есть прибор недостижим сам по себе. Обе половины цикла сняты, чтобы он
  // не ожил, если блок когда-нибудь попадёт в руки другим путём.
  event.remove({ id: 'hbm_ntm_rebirth:tools/geiger_counter_from_block' })
  event.remove({ id: 'hbm_ntm_rebirth:blocks/geiger' })

  console.info(
    `[Recast] Ворота P7: домен HBM открыт тремя рецептами входа на электронике EV; снято оружия ${removedWeapons}/121, брони ${removedArmour}/112, боеприпасов ${removedAmmo}/89, модулей брони ${removedModules}/45, плюс две станции и ${assemblerAmmunition.length} рецептов боезапаса в сборочной машине; ${replacedInstruments.length} прибора отданы своим владельцам, замкнутый цикл счётчика Гейгера разорван.`
  )
})
