// Модуль фракций, часть 6: операции, которые действительно происходят.
//
// Пятнадцать операций были написаны за пять волн и все пять волн оставались
// текстом: команда печатала описание, и на этом всё заканчивалось. Здесь
// операция становится событием со временем, предупреждением и последствием.
//
// Главное правило взято из спецификации и не нарушается ни разу: до ACTIVE
// нельзя добраться, минуя окно переговоров. Игрок обязан получить возможность
// договориться раньше, чем к нему кто-то придёт. Второе правило оттуда же —
// операция начинается только при игроке в сети, поэтому никакого разорения
// базы за время отсутствия не бывает.
//
// Третье правило добавлено сборкой и стоит того, чтобы назвать его отдельно:
// операция не приходит из ниоткуда. Фракция должна быть недовольна — при
// нейтральном и хорошем отношении никто ничего не планирует.

// Отношение, ниже которого фракция начинает действовать.
const IF_OPERATION_TRIGGER_REPUTATION = -11

// Сколько времени занимает каждая стадия. Числа выбраны так, чтобы у игрока
// был вечер на подготовку, а не пять секунд на панику.
const IF_OPERATION_STAGE_TICKS = {
  PLANNED: 2400,
  RECON: 3600,
  WARNED: 2400,
  NEGOTIATION_WINDOW: 4800,
  PREPARATION: 1800,
  ACTIVE: 6000,
  RECOVERY: 2400,
  COOLDOWN: 72000,
}

// Как часто модуль вспоминает о своих операциях.
const IF_OPERATION_TICK_INTERVAL = 100

// Операции по эпохам. Определения лежат в threat_director/definitions;
// здесь только то, что нужно на ходу, и линтер сверяет пары чисел.
const IF_OPERATIONS = [
  {
    id: 'survey',
    ru: 'Разведка района',
    min_epoch: 0,
    max_epoch: 3,
    warning_ru: 'У границы замечена группа с инструментами съёмки.',
    negotiation_ru: 'Их можно пропустить открыто или выдворить.',
    squad: 0,
  },
  {
    id: 'caravan',
    ru: 'Торговый караван',
    min_epoch: 1,
    max_epoch: 6,
    warning_ru: 'К вам идёт караван и рассчитывает на честный приём.',
    negotiation_ru: 'Можно торговать, а можно и не пустить.',
    squad: 0,
  },
  {
    id: 'utility_claim',
    ru: 'Требование по коммунальному узлу',
    min_epoch: 4,
    max_epoch: 9,
    warning_ru: 'Фракция считает ваш узел своим и прислала требование.',
    negotiation_ru: 'Можно уступить долю, откупиться или отказать.',
    squad: 2,
  },
  {
    id: 'blockade',
    ru: 'Блокада маршрута',
    min_epoch: 5,
    max_epoch: 9,
    warning_ru: 'Ваш маршрут снабжения перекрывают.',
    negotiation_ru: 'Можно договориться о пошлине или прорываться.',
    squad: 3,
  },
  {
    id: 'sabotage',
    ru: 'Промышленный саботаж',
    min_epoch: 6,
    max_epoch: 9,
    warning_ru: 'К вашему производству идёт группа с зарядами.',
    negotiation_ru: 'Ещё можно откупиться. Потом будет поздно.',
    squad: 4,
  },
]

// Как стадия называется для игрока. Служебные имена автомата в отчёт не
// выносятся: игроку важно, что происходит, а не как это записано.
const IF_OPERATION_STAGE_NAMES = {
  PLANNED: 'решение принято, но вам ещё не сообщили',
  RECON: 'вас изучают',
  WARNED: 'вам объявили',
  NEGOTIATION_WINDOW: 'идут переговоры',
  PREPARATION: 'они готовятся',
  ACTIVE: 'происходит сейчас',
  RECOVERY: 'всё кончилось, идёт разбор',
  COOLDOWN: 'пауза',
}

function ifOperationState(server) {
  const state = ifState(server)
  if (!state.contains('operations')) state.put('operations', {})
  return state.get('operations')
}

// Отряд по эпохе: та же боевая лестница, что у пресетов.
function ifSquadTierForEpoch(epoch) {
  if (epoch <= 2) return 'early'
  if (epoch <= 5) return 'mid'
  return 'late'
}

function ifOperationForEpoch(epoch) {
  const suitable = IF_OPERATIONS.filter((operation) => epoch >= operation.min_epoch && epoch <= operation.max_epoch)
  if (suitable.length === 0) return null
  return suitable[Math.floor(Math.random() * suitable.length)]
}

// Кто именно недоволен. Берём фракцию с худшим отношением: у мира должна быть
// причина, а не жребий.
function ifMostOffendedFaction(team) {
  let worstId = null
  let worstValue = IF_OPERATION_TRIGGER_REPUTATION
  IF_FACTION_LIST.forEach((factionId) => {
    const value = team.getInt('rep_' + factionId)
    if (value <= worstValue) {
      worstValue = value
      worstId = factionId
    }
  })
  return worstId
}

// Договор останавливает операцию. Перемирие и союз существуют именно для
// этого, иначе их незачем заключать.
function ifOperationBlocked(team, factionId) {
  const treaties = ifTreaties(team)
  return (
    treaties.contains(`${factionId}|truce`) ||
    treaties.contains(`${factionId}|alliance`) ||
    treaties.contains(`${factionId}|tribute`)
  )
}

function ifOperationPlan(server, player) {
  const operations = ifOperationState(server)
  const teamId = player.username
  if (operations.contains(teamId)) return false

  const team = ifTeamState(server, teamId)
  const factionId = ifMostOffendedFaction(team)
  if (!factionId) return false
  if (ifOperationBlocked(team, factionId)) return false

  const epoch = team.getInt('tech_epoch')
  const definition = ifOperationForEpoch(epoch)
  if (!definition) return false

  const record = {}
  record.putString('faction', factionId)
  record.putString('definition', definition.id)
  record.putString('stage', 'PLANNED')
  record.putInt('ticks', IF_OPERATION_STAGE_TICKS.PLANNED)
  record.putBoolean('negotiated', false)
  operations.put(teamId, record)

  ifAudit(server, teamId, `operation planned ${factionId}/${definition.id}`)
  return true
}

function ifOperationDefinition(id) {
  return IF_OPERATIONS.filter((operation) => operation.id === id)[0] || null
}

// Появление отряда. Отряд приходит на расстоянии, а не в лицо: у игрока должно
// остаться место для решения даже здесь.
function ifOperationSendSquad(server, player, factionId, count) {
  if (count <= 0) return
  const tier = ifSquadTierForEpoch(ifTeamState(server, player.username).getInt('tech_epoch'))
  const block = player.block
  for (let index = 0; index < count; index++) {
    const offsetX = block.x + 24 + index * 2
    const offsetZ = block.z + 24
    server.runCommandSilent(
      `easy_npc preset import_new data industrial_frontier:preset/${factionId}_squad_${tier}.npc.snbt ${offsetX} ${block.y} ${offsetZ}`
    )
  }
  console.info(`[Recast][Фракции] отряд ${factionId}/${tier} выслан: ${count}`)
}

// Переход на следующую стадию.
function ifOperationAdvance(server, player, record) {
  const teamId = player.username
  const factionId = record.getString('faction')
  const definition = ifOperationDefinition(record.getString('definition'))
  const data = IF_FACTION_DATA[factionId]
  if (!definition || !data) {
    ifOperationState(server).remove(teamId)
    return
  }

  const stage = record.getString('stage')
  const nextIndex = IF_OPERATION_LIFECYCLE.indexOf(stage) + 1
  const nextStage = IF_OPERATION_LIFECYCLE[nextIndex]

  if (!nextStage || nextStage === 'CLOSED') {
    ifOperationState(server).remove(teamId)
    ifAudit(server, teamId, `operation closed ${factionId}/${definition.id}`)
    return
  }

  record.putString('stage', nextStage)
  record.putInt('ticks', IF_OPERATION_STAGE_TICKS[nextStage] || 1200)

  if (nextStage === 'RECON') {
    player.tell(`§e${data.short_ru}: ${definition.warning_ru}§r`)
  } else if (nextStage === 'WARNED') {
    player.tell(`§6${data.ru} объявляет: «${definition.ru}».§r`)
    player.tell(definition.negotiation_ru)
  } else if (nextStage === 'NEGOTIATION_WINDOW') {
    player.tell('§eОкно переговоров открыто. Договориться можно прямо сейчас.§r')
    player.tell('Команда: /if_threat operation negotiate — или найдите посланника.')
  } else if (nextStage === 'PREPARATION') {
    if (record.getBoolean('negotiated')) {
      player.tell(`§a${data.short_ru} отзывает операцию: договорённость достигнута.§r`)
      ifApplyReputation(server, teamId, factionId, 'operation_passed', definition.id, player)
      ifOperationState(server).remove(teamId)
      return
    }
    player.tell(`§c${data.short_ru} готовится. Время договориться вышло.§r`)
  } else if (nextStage === 'ACTIVE') {
    ifOperationSendSquad(server, player, factionId, definition.squad)
    if (definition.squad > 0) {
      player.tell(`§cОтряд ${data.short_ru} на подходе.§r`)
    } else {
      player.tell(`§e${data.short_ru} действует в вашем районе.§r`)
    }
  } else if (nextStage === 'RECOVERY') {
    player.tell(`§7${data.short_ru} сворачивает работу. Последствия можно исправить.§r`)
    ifApplyReputation(server, teamId, factionId, 'operation_repelled', definition.id, player)
  } else if (nextStage === 'COOLDOWN') {
    player.tell(`§7${data.short_ru} берёт паузу.§r`)
  }

  ifAudit(server, teamId, `operation ${factionId}/${definition.id} -> ${nextStage}`)
}

function ifOperationTick(server) {
  const players = server.getPlayers()
  if (!players || players.length === 0) return
  const operations = ifOperationState(server)

  players.forEach((player) => {
    const teamId = player.username
    if (!operations.contains(teamId)) {
      // Планирование редкое: примерно раз в двадцать минут игры и только при
      // испорченных отношениях.
      if (Math.random() < 0.01) ifOperationPlan(server, player)
      return
    }

    const record = operations.get(teamId)
    const left = record.getInt('ticks') - IF_OPERATION_TICK_INTERVAL
    if (left > 0) {
      record.putInt('ticks', left)
      return
    }
    ifOperationAdvance(server, player, record)
  })
}

let ifOperationCountdown = IF_OPERATION_TICK_INTERVAL

ServerEvents.tick((event) => {
  ifOperationCountdown -= 1
  if (ifOperationCountdown > 0) return
  ifOperationCountdown = IF_OPERATION_TICK_INTERVAL
  ifOperationTick(event.server)
})

ServerEvents.commandRegistry((event) => {
  const commands = event.commands
  const operationNode = commands.literal('operation')

  operationNode.then(
    commands.literal('status').executes((context) => {
      const actor = context.source.getEntity()
      if (!actor || !actor.isPlayer()) return 0
      const operations = ifOperationState(context.source.getServer())
      if (!operations.contains(actor.username)) {
        actor.tell('Против вас никто ничего не готовит.')
        return 1
      }
      const record = operations.get(actor.username)
      const definition = ifOperationDefinition(record.getString('definition'))
      const data = IF_FACTION_DATA[record.getString('faction')]
      actor.tell(`${data.ru}: «${definition ? definition.ru : record.getString('definition')}»`)
      const stageName = IF_OPERATION_STAGE_NAMES[record.getString('stage')]
      actor.tell(`Сейчас: ${stageName || 'неизвестно'}`)
      return 1
    })
  )

  // Переговоры. Работают только в своё окно: договариваться, когда отряд уже
  // вышел, поздно — и это то, ради чего окно вообще существует.
  operationNode.then(
    commands.literal('negotiate').executes((context) => {
      const actor = context.source.getEntity()
      if (!actor || !actor.isPlayer()) return 0
      const server = context.source.getServer()
      const operations = ifOperationState(server)
      if (!operations.contains(actor.username)) {
        actor.tell('Договариваться не о чем.')
        return 1
      }
      const record = operations.get(actor.username)
      if (record.getString('stage') !== 'NEGOTIATION_WINDOW') {
        actor.tell('§cСейчас не время для разговоров.§r')
        return 1
      }
      record.putBoolean('negotiated', true)
      actor.tell('§aВы дали понять, что готовы договариваться. Ответ придёт скоро.§r')
      ifAudit(server, actor.username, `operation negotiation accepted`)
      return 1
    })
  )

  event.register(commands.literal('if_threat').then(operationNode))
})
