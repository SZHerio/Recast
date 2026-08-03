// Операции, отряды и договоры P5.
//
// К пятой эпохе у игрока появляется то, что можно перерезать: магистраль,
// порт, склад и пассажирская линия. Внешний мир реагирует именно на это, а не
// на количество прожитых дней.
//
// Три вещи, которые здесь заводятся:
//   1. Комплекты отрядов: чем вооружён NPC, определяется тройкой
//      «фракция + эпоха + роль» и ничем больше.
//   2. Комплексы B4 и пять новых операций вокруг логистики.
//   3. Договоры, последствия и восстановление после операции.
//
// Правило снаряжения без исключений: потолок отряда — эпоха его команды.
// Патруль P5 не носит того, чего игрок ещё не может произвести, и не роняет
// это в лут. Архетипы берутся из m2_extended_domains.json, а не выдумываются.
// Комплекты живут в config/tacznpc_loadouts.json: TACZ: NPCs читает шаблоны
// оттуда при запуске сервера. Здесь хранится только их описание для игрока —
// два источника одной правды не заводятся.
const IF_M5_FACTIONS = [
  { id: 'zemlemer', title_ru: 'Землемеры' },
  { id: 'meridian', title_ru: 'Меридиан' },
  { id: 'free_caravans', title_ru: 'Лига Вольных Караванов' },
  { id: 'helios', title_ru: 'Гелиос' },
  { id: 'ash_root', title_ru: 'Пепельный Корень' },
  { id: 'scar', title_ru: 'Шрам' }
]

const IF_M5_EPOCH_BANDS = [
  { band: 'p2', title_ru: 'P2–P3', weapons_ru: 'револьверы, двустволки и болтовая винтовка, кожаная защита' },
  { band: 'p4', title_ru: 'P4', weapons_ru: 'помповое ружьё и самозарядный пистолет, железная защита' },
  { band: 'p5', title_ru: 'P5', weapons_ru: 'автоматическая винтовка и пистолет, железная защита' }
]

// Уровень базы ограничен эпохой цели: комплекс B4 не появляется у команды,
// которая ещё не дошла до P5, даже если мир старый.
const IF_M5_BASE_LEVEL = { level: 'B4', title_ru: 'Военный комплекс', min_epoch: 5, max_epoch: 6 }

// Пять операций. У каждой обязательное окно переговоров, обратимый ущерб и
// прописанное восстановление: базу игрока нельзя потерять безвозвратно.
const IF_M5_OPERATIONS = [
  {
    id: 'train_escort',
    title_ru: 'Защита состава',
    trigger_ru: 'Закрыт контракт «Грузовой коридор», по плечу пошёл регулярный груз.',
    stake_ru: 'Состав и груз на маршруте.',
    negotiation_ru: 'Договор о проходе с Лигой Вольных Караванов снимает операцию до её начала.',
    recovery_ru: 'Потерянный состав восстанавливается на депо; путь и сигналы не разрушаются.'
  },
  {
    id: 'blockade',
    title_ru: 'Блокада плеча',
    trigger_ru: 'Транспортная связность выше 66 при враждебной репутации хотя бы одной фракции.',
    stake_ru: 'Пропускная способность одного плеча, а не всей сети.',
    negotiation_ru: 'Пошлина или встречная поставка снимают блокаду без боя.',
    recovery_ru: 'Плечо открывается само через договор или после снятия поста; рельсы остаются на месте.'
  },
  {
    id: 'industrial_sabotage',
    title_ru: 'Промышленный саботаж',
    trigger_ru: 'Взято обязательство по потоку, и линия работает без резерва.',
    stake_ru: 'Один узел линии выходит из строя, продукция на складе не трогается.',
    negotiation_ru: 'Резерв на складе и охрана узла делают операцию невыгодной и отменяют её.',
    recovery_ru: 'Узел чинится штатным ремонтом; чертежи и настройки сохраняются.'
  },
  {
    id: 'port_raid',
    title_ru: 'Налёт на порт',
    trigger_ru: 'Закрыт контракт «Речной порт», через него идёт тяжёлый или жидкий груз.',
    stake_ru: 'Груз на причале и одна баржа.',
    negotiation_ru: 'Портовый сбор или доля в маршруте снимают налёт.',
    recovery_ru: 'Баржа восстанавливается у причала, причал не разрушается.'
  },
  {
    id: 'joint_defence',
    title_ru: 'Совместная оборона',
    trigger_ru: 'Дружественная фракция теряет свой узел на общем маршруте.',
    stake_ru: 'Репутация и будущие условия торговли, а не имущество игрока.',
    negotiation_ru: 'Отказ допустим и не делает фракцию врагом — он стоит уважения, а не мира.',
    recovery_ru: 'Успех даёт договор и снижение риска операций на этом маршруте.'
  }
]

// Договор — это состояние, а не разовая награда. У него есть цена, срок и
// последствие для соседей: союз с одной фракцией виден остальным.
const IF_M5_TREATIES = [
  {
    id: 'transit_pact',
    title_ru: 'Договор о проходе',
    price_ru: 'Доля с плеча или регулярная поставка материала эпохи.',
    grants_ru: 'Снимает «Защиту состава» и «Блокаду плеча» на согласованных маршрутах.',
    consequence_ru: 'Фракции, враждебные подписанту, считают маршрут его интересом.'
  },
  {
    id: 'port_charter',
    title_ru: 'Портовая хартия',
    price_ru: 'Портовый сбор и приоритет разгрузки чужого груза.',
    grants_ru: 'Снимает «Налёт на порт», открывает водные торговые строки.',
    consequence_ru: 'Обязывает пропускать чужие баржи в очередь наравне со своими.'
  },
  {
    id: 'mutual_defence',
    title_ru: 'Договор о взаимной обороне',
    price_ru: 'Обязательство прийти на «Совместную оборону» дважды подряд.',
    grants_ru: 'Ответная помощь при саботаже и налёте на ваши узлы.',
    consequence_ru: 'Нарушение обязательства снимает договор и стоит больше, чем отказ подписывать.'
  }
]

function ifM5OperationState(server) {
  const root = server.persistentData
  if (!root.contains('industrial_frontier')) root.put('industrial_frontier', {})
  const state = root.get('industrial_frontier')
  if (!state.contains('m5_operations')) state.put('m5_operations', {})
  return state.get('m5_operations')
}

ServerEvents.customCommand('if_operations', (event) => {
  const player = event.player
  if (!player) return
  const state = ifM5OperationState(event.server)

  player.tell(`Операции вокруг логистики (комплекс ${IF_M5_BASE_LEVEL.level} — ${IF_M5_BASE_LEVEL.title_ru}, эпохи P${IF_M5_BASE_LEVEL.min_epoch}–P${IF_M5_BASE_LEVEL.max_epoch}):`)
  IF_M5_OPERATIONS.forEach((operation) => {
    const status = state.contains(operation.id) ? state.getString(operation.id) : 'не начата'
    player.tell(` ${operation.title_ru} — ${status}`)
    player.tell(`    начинается: ${operation.trigger_ru}`)
    player.tell(`    на кону: ${operation.stake_ru}`)
    player.tell(`    переговоры: ${operation.negotiation_ru}`)
    player.tell(`    восстановление: ${operation.recovery_ru}`)
  })
  player.tell('Окно переговоров есть всегда. Необратимой потери базы игрока нет ни в одной операции.')
})

ServerEvents.customCommand('if_treaties', (event) => {
  const player = event.player
  if (!player) return
  player.tell('Договоры и их последствия:')
  IF_M5_TREATIES.forEach((treaty) => {
    player.tell(` ${treaty.title_ru}`)
    player.tell(`    цена: ${treaty.price_ru}`)
    player.tell(`    даёт: ${treaty.grants_ru}`)
    player.tell(`    последствие: ${treaty.consequence_ru}`)
  })
  player.tell('Договор — состояние, а не разовая награда: его можно потерять поведением.')
})

ServerEvents.customCommand('if_squad_loadout', (event) => {
  const player = event.player
  if (!player) return
  player.tell('Комплект отряда задаётся тройкой «фракция + эпоха + роль». Всего 18 шаблонов:')
  IF_M5_EPOCH_BANDS.forEach((band) => {
    player.tell(` Эпоха ${band.title_ru}: ${band.weapons_ru}`)
  })
  IF_M5_FACTIONS.forEach((faction) => {
    const names = IF_M5_EPOCH_BANDS.map((band) => `if_${faction.id}_${band.band}`).join(', ')
    player.tell(` ${faction.title_ru}: ${names}`)
  })
  player.tell('Роль внутри комплекта задаётся оружием: основное — линейный боец, запасное — разведчик и сопровождение.')
  player.tell('Потолок снаряжения и лута — эпоха команды цели. Патруль не носит и не роняет оружие будущей эпохи, шанс выпадения оружия 15%.')
  player.tell('Спавн у структур выключен намеренно: массовые отряды включаются только после пользовательского теста производительности на 20/40/80 единицах.')
})
