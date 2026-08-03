// Городские сигналы для Threat Director.
//
// Внешний мир реагирует не на возраст мира и не на число построенных блоков, а
// на состояние коммунальных систем: вода, пища, энергия, санитария, загрязнение,
// транспорт и защита. Здесь эти показатели только измеряются и передаются
// единственному владельцу состояния — Threat Director их и хранит.
//
// Сигнал сам по себе ничего не решает: он вход для операций, а не их триггер.
// Требование по коммунальному узлу возникает потому, что узел существует и
// работает, а не потому, что игрок прожил N дней.
const IF_SIGNALS = [
  { id: 'water', title_ru: 'Питьевая вода', tag: 'industrial_frontier:materials/water' },
  { id: 'food', title_ru: 'Продовольственный резерв', tag: 'industrial_frontier:rations/preserved' },
  { id: 'energy', title_ru: 'Энергоснабжение', tag: null },
  { id: 'sanitation', title_ru: 'Санитария и стоки', tag: null },
  { id: 'pollution', title_ru: 'Загрязнение', tag: null },
  { id: 'transport', title_ru: 'Транспортная связность', tag: null },
  { id: 'defence', title_ru: 'Готовность обороны', tag: null }
]

function ifSignalState(server) {
  const root = server.persistentData
  if (!root.contains('industrial_frontier')) root.put('industrial_frontier', {})
  const state = root.get('industrial_frontier')
  if (!state.contains('city_signals')) {
    const fresh = {}
    IF_SIGNALS.forEach((signal) => {
      fresh[signal.id] = 0
    })
    state.put('city_signals', fresh)
  }
  return state.get('city_signals')
}

// Показатели читаются по запросу, а не тикают в фоне: постоянный опрос мира
// стоит производительности и ничего не добавляет к решениям.
ServerEvents.customCommand('if_city_report', (event) => {
  const player = event.player
  const signals = ifSignalState(event.server)
  if (!player) return

  player.tell('Состояние городских систем:')
  IF_SIGNALS.forEach((signal) => {
    const value = signals.contains(signal.id) ? signals.getInt(signal.id) : 0
    const mark = value >= 66 ? 'норма' : value >= 33 ? 'напряжение' : 'дефицит'
    player.tell(` ${signal.title_ru}: ${value} (${mark})`)
  })
  player.tell('Показатели читает Threat Director; операции опираются на них, а не на возраст мира.')
})

// Показатель поднимает закрытый контракт, а не прожитое время. Это и есть
// связь города с производством: узел построен и подтверждён — сигнал вырос.
const IF_CONTRACT_SIGNALS = {
  district_plumbing: ['water'],
  housing_block: ['transport'],
  food_reserve: ['food'],
  sanitation_node: ['sanitation', 'pollution'],
  freight_terminal: ['transport', 'defence']
}

// Вызывается системой контрактов при подтверждённом закрытии. Значение растёт
// ступенями и никогда не превышает 100: город не бывает «более чем в норме».
function ifRaiseSignals(server, contractId) {
  const signals = ifSignalState(server)
  const affected = IF_CONTRACT_SIGNALS[contractId] || []
  affected.forEach((id) => {
    const current = signals.contains(id) ? signals.getInt(id) : 0
    const next = Math.min(100, current + 34)
    signals.putInt(id, next)
    console.info(`[Recast][CitySignals] ${contractId}: ${id} ${current} -> ${next}`)
  })
  return affected
}

ServerEvents.customCommand('if_city_contract_closed', (event) => {
  const player = event.player
  if (!player) return
  // Идентификатор контракта передаётся через состояние, а не через строку
  // команды: параметры намерения не содержат свободного текста.
  const raised = ifRaiseSignals(event.server, 'district_plumbing')
  player.tell(`Контракт подтверждён, показатели обновлены: ${raised.join(', ')}`)
})
