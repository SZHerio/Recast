// Региональные контракты P5.
//
// Муниципальные контракты P4 доказывали, что район живёт. Региональные
// доказывают, что районы связаны: склад принимает поток, магистраль его везёт,
// порт разгружает, а линия возит людей.
//
// Два новых класса, которых не было в P4:
//   производительность — держать заданный поток, а не сдать разовую партию;
//   устойчивость — держать его же, ничего не выбрасывая наружу.
//
// Правила прежние и не смягчаются: состав виден заранее, материал принимается
// категорией, награда — разрешение или услуга, и контракт не выдаётся раньше,
// чем существует автоматический маршрут его материалов.
const IF_M5_CONTRACTS = [
  {
    id: 'regional_warehouse',
    title_ru: 'Региональный склад',
    kind_ru: 'складской',
    min_epoch: 5,
    demand_ru: [
      'Резерв длительного хранения (industrial_frontier:storage/long_term_reserve)',
      'Материалы палитры P5',
      'Возвратная тара из городского пищевого цикла'
    ],
    reward_ru: 'Право размещать буферные склады у чужих узлов и доступ к каталогу складских разрешений.',
    requires_automation_ru: 'Массовое производство тары и блоков палитры; ручная набивка сундуков не требуется.'
  },
  {
    id: 'rail_corridor',
    title_ru: 'Грузовой коридор',
    kind_ru: 'транспортный',
    min_epoch: 5,
    demand_ru: [
      'Пути и сигналы Create/Steam «n» Rails',
      'Погрузочные и разгрузочные узлы на обоих концах',
      'Буферное хранение на промежуточной станции'
    ],
    reward_ru: 'Междурайонный маршрут под охраной договора и снижение риска блокады на этом плече.',
    requires_automation_ru: 'Серийное производство путей; коридор не собирается поштучно вручную.'
  },
  {
    id: 'river_port',
    title_ru: 'Речной порт',
    kind_ru: 'транспортный',
    min_epoch: 5,
    demand_ru: [
      'Причал и направляющие буксира Little Logistics',
      'Баржи под груз и под жидкость',
      'Подъездной путь до склада'
    ],
    reward_ru: 'Водное плечо для тяжёлых и жидких грузов и торговый выход к Лиге Вольных Караванов.',
    requires_automation_ru: 'Наливные и сыпучие грузы перегружаются механизмами, а не вёдрами.'
  },
  {
    id: 'transit_line',
    title_ru: 'Пассажирская линия',
    kind_ru: 'транспортный',
    min_epoch: 5,
    demand_ru: [
      'Узлы пути и пульт MTR',
      'Две станции с платформами палитры P5',
      'Энергоснабжение депо'
    ],
    reward_ru: 'Покрытие жилого и промышленного районов, рост показателя транспортной связности.',
    requires_automation_ru: 'Сталь и электроника MV производятся линией, а не собираются под каждую станцию.'
  },
  {
    id: 'throughput_pledge',
    title_ru: 'Обязательство по потоку',
    kind_ru: 'производительность',
    min_epoch: 5,
    demand_ru: [
      'Заявленный поток одного массового материала',
      'Измерительный узел на выходе линии',
      'Резерв на складе на случай остановки'
    ],
    reward_ru: 'Статус надёжного поставщика: длинные заказы вместо разовых и лучшие условия торговли.',
    requires_automation_ru: 'Поток держит производство, а не игрок: ручное пополнение обязательства не засчитывается.'
  },
  {
    id: 'closed_loop_pledge',
    title_ru: 'Обязательство по замкнутости',
    kind_ru: 'устойчивость',
    min_epoch: 5,
    demand_ru: [
      'Возврат тары в производственный цикл',
      'Приём побочных продуктов линии без свободного сброса',
      'Отсутствие роста загрязнения района при выполненном потоке'
    ],
    reward_ru: 'Экологический допуск района и снижение поводов для операций вокруг ваших узлов.',
    requires_automation_ru: 'Возвратные потоки идут механизмами; ручная утилизация обязательством не считается.'
  }
]

function ifM5ContractState(server) {
  const root = server.persistentData
  if (!root.contains('industrial_frontier')) root.put('industrial_frontier', {})
  const state = root.get('industrial_frontier')
  if (!state.contains('regional_contracts')) state.put('regional_contracts', {})
  return state.get('regional_contracts')
}

// Каталог показывает всё сразу, включая условие автоматизации: игрок должен
// видеть цену вопроса до того, как возьмётся.
ServerEvents.customCommand('if_regional_contracts', (event) => {
  const player = event.player
  if (!player) return
  const taken = ifM5ContractState(event.server)

  player.tell('Региональные контракты P5:')
  IF_M5_CONTRACTS.forEach((contract) => {
    const state = taken.contains(contract.id) ? taken.getString(contract.id) : 'доступен'
    player.tell(` [P${contract.min_epoch}] ${contract.title_ru} (${contract.kind_ru}) — ${state}`)
    contract.demand_ru.forEach((line) => player.tell(`    требует: ${line}`))
    player.tell(`    награда: ${contract.reward_ru}`)
    player.tell(`    автоматизация: ${contract.requires_automation_ru}`)
  })
  player.tell('Награда контракта — разрешение, услуга или маршрут. Ресурс из ничего не создаётся.')
})

// Связь с городскими показателями. Значение поднимает подтверждённое закрытие,
// а не прожитое время: узел построен и работает — показатель вырос.
const IF_M5_CONTRACT_SIGNALS = {
  regional_warehouse: ['food', 'transport'],
  rail_corridor: ['transport'],
  river_port: ['transport'],
  transit_line: ['transport', 'energy'],
  throughput_pledge: ['energy'],
  closed_loop_pledge: ['sanitation', 'pollution']
}

ServerEvents.customCommand('if_regional_contract_signals', (event) => {
  const player = event.player
  if (!player) return
  player.tell('Какой контракт какой показатель поднимает:')
  IF_M5_CONTRACTS.forEach((contract) => {
    const affected = IF_M5_CONTRACT_SIGNALS[contract.id] || []
    player.tell(` ${contract.title_ru}: ${affected.join(', ')}`)
  })
  player.tell('Показатели хранит Threat Director; операции опираются на них, а не на возраст мира.')
})
