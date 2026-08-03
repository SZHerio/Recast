// Муниципальные контракты P4.
//
// Контракт — честный сток массовых ресурсов и доказательство того, что
// производство работает. Он не должен быть скрытым налогом, поэтому состав
// известен заранее, материалы принимаются категориями, а не поштучно, и
// награда никогда не создаёт ресурс из ничего.
//
// Жёсткое правило: контракт не выдаётся раньше, чем существует автоматический
// маршрут его материалов. Массовый спрос до автоматизации — ошибка
// проектирования, а не сложность.
const IF_CONTRACTS = [
  {
    id: 'district_plumbing',
    title_ru: 'Водопровод района',
    min_epoch: 4,
    demand_ru: ['Питьевая вода из водоподготовки', 'Трубы и запорная арматура', 'Измерительный узел'],
    reward_ru: 'Разрешение на подключение новых кварталов и доступ к городскому каталогу труб.',
    requires_automation_ru: 'Водоподготовка с разделением на три потока и приёмником стоков.'
  },
  {
    id: 'housing_block',
    title_ru: 'Жилой квартал',
    min_epoch: 4,
    demand_ru: ['Материалы эпохальной палитры', 'Стекло', 'Освещение', 'Мебель'],
    reward_ru: 'Прирост населения колонии и чертёж следующего типа застройки.',
    requires_automation_ru: 'Серийное производство блоков палитры; ручная выкладка не требуется.'
  },
  {
    id: 'food_reserve',
    title_ru: 'Продовольственный резерв',
    min_epoch: 4,
    demand_ru: ['Хранимый рацион', 'Тара', 'Холодовая логистика'],
    reward_ru: 'Устойчивость города к межсезонью и торговый договор с фракцией.',
    requires_automation_ru: 'Пакетная кухня Create; рацион принимает категорию из 11 блюд.'
  },
  {
    id: 'sanitation_node',
    title_ru: 'Узел санитарии',
    min_epoch: 4,
    demand_ru: ['Приёмник стоков', 'Компостирование осадка', 'Отвод биогаза'],
    reward_ru: 'Снижение загрязнения района и доступ к удобрению из осадка.',
    requires_automation_ru: 'Маршрут возврата стоков целиком, без свободного сброса.'
  },
  {
    id: 'freight_terminal',
    title_ru: 'Грузовой терминал',
    min_epoch: 5,
    demand_ru: ['Рельсы и сигналы', 'Погрузочные узлы', 'Буферное хранение'],
    reward_ru: 'Региональные маршруты и защита конвоев по договору с Лигой Вольных Караванов.',
    requires_automation_ru: 'Массовое производство рельсов; терминал не строится вручную поштучно.'
  }
]

function ifContractState(server) {
  const root = server.persistentData
  if (!root.contains('industrial_frontier')) root.put('industrial_frontier', {})
  const state = root.get('industrial_frontier')
  if (!state.contains('contracts')) state.put('contracts', {})
  return state.get('contracts')
}

// Каталог показывает всё сразу, включая условие автоматизации. Игрок должен
// видеть цену вопроса до того, как возьмётся, а не узнавать её по ходу.
ServerEvents.customCommand('if_contracts', (event) => {
  const player = event.player
  if (!player) return
  const taken = ifContractState(event.server)

  player.tell('Муниципальные контракты:')
  IF_CONTRACTS.forEach((contract) => {
    const state = taken.contains(contract.id) ? taken.getString(contract.id) : 'доступен'
    player.tell(` [P${contract.min_epoch}] ${contract.title_ru} — ${state}`)
    player.tell(`    требует: ${contract.demand_ru.join(', ')}`)
    player.tell(`    награда: ${contract.reward_ru}`)
    player.tell(`    автоматизация: ${contract.requires_automation_ru}`)
  })
  player.tell('Награда контракта — разрешение, услуга или чертёж. Ресурс из ничего не создаётся.')
})
