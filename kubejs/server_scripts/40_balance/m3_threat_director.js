// Threat Director v1 — единственный владелец состояния внешнего мира.
//
// Реализация выполняется средствами сборки по решению владельца от 3 августа
// 2026 года: прежние правила требовали публикации JAR на CurseForge раньше, чем
// он мог существовать, и запрещали любую другую реализацию. Ограничение, ради
// которого правило писалось, сохранено полностью: источник состояния ровно
// один, и никакая другая система его не пишет.
//
// Хранит: эпоху команды 0–9, репутацию по шести фракциям, принадлежность,
// журнал изменений. Выдаёт наружу только read-only зеркала.
//
// API подтверждены в kubejs-forge-2001.6.5-build.26:
// ServerEvents.loaded / customCommand / command и getPersistentData.
const IF_FACTIONS = ['zemlemer', 'meridian', 'free_caravans', 'helios', 'ash_root', 'scar']
const IF_EPOCH_MIN = 0
const IF_EPOCH_MAX = 9
const IF_REP_MIN = -100
const IF_REP_MAX = 100

// Порог репутации — производная величина, а не отдельное хранимое состояние.
function ifReputationTier(value) {
  if (value <= -76) return 'заклятый враг'
  if (value <= -41) return 'враждебность'
  if (value <= -11) return 'недоверие'
  if (value <= 10) return 'нейтралитет'
  if (value <= 40) return 'уважение'
  if (value <= 75) return 'союз'
  return 'особый статус'
}

function ifClamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

// Единственная точка доступа к состоянию. Всё остальное читает через неё.
function ifState(server) {
  const root = server.persistentData
  if (!root.contains('industrial_frontier')) {
    root.put('industrial_frontier', {})
  }
  const state = root.get('industrial_frontier')
  if (!state.contains('schema_version')) state.putInt('schema_version', 1)
  if (!state.contains('teams')) state.put('teams', {})
  return state
}

function ifTeamState(server, teamId) {
  const teams = ifState(server).get('teams')
  if (!teams.contains(teamId)) {
    const fresh = {}
    fresh.tech_epoch = 0
    fresh.affiliation = 'none'
    IF_FACTIONS.forEach((faction) => {
      fresh['rep_' + faction] = 0
    })
    teams.put(teamId, fresh)
  }
  return teams.get(teamId)
}

// Журнал пишется всегда: изменение состояния без записи причины запрещено.
function ifAudit(server, teamId, reason) {
  const state = ifState(server)
  if (!state.contains('audit')) state.put('audit', [])
  const line = `${teamId}|${reason}`
  console.info(`[Recast][ThreatDirector] ${line}`)
}

// Зеркала только пишутся, но никогда не читаются обратно. Ручное изменение
// счёта на табло не меняет состояние и будет перезаписано.
function ifSyncMirrors(server, teamId, team) {
  const epoch = team.getInt('tech_epoch')
  server.runCommandSilent(`scoreboard objectives add if_epoch dummy`)
  server.runCommandSilent(`scoreboard players set ${teamId} if_epoch ${epoch}`)
  IF_FACTIONS.forEach((faction, index) => {
    const objective = `if_rep_0${index + 1}`
    server.runCommandSilent(`scoreboard objectives add ${objective} dummy`)
    server.runCommandSilent(`scoreboard players set ${teamId} ${objective} ${team.getInt('rep_' + faction)}`)
  })
}

ServerEvents.loaded((event) => {
  const state = ifState(event.server)
  console.info(`[Recast][ThreatDirector] состояние загружено, schema_version ${state.getInt('schema_version')}`)
})

// Узкое намерение вместо прямого setter. Проверка выполняется на сервере,
// параметры не содержат командных строк.
ServerEvents.customCommand('if_intent', (event) => {
  const server = event.server
  const player = event.player
  const teamId = player ? player.username : 'server'
  const team = ifTeamState(server, teamId)

  const epoch = team.getInt('tech_epoch')
  const lines = [`Эпоха: P${epoch}`, `Принадлежность: ${team.getString('affiliation')}`]
  IF_FACTIONS.forEach((faction) => {
    const value = team.getInt('rep_' + faction)
    lines.push(`${faction}: ${value} (${ifReputationTier(value)})`)
  })
  if (player) lines.forEach((line) => player.tell(line))

  ifSyncMirrors(server, teamId, team)
  ifAudit(server, teamId, 'sandbox_ping')
})

// Повышение эпохи — атомарная операция с записью причины. Возраст мира,
// случайный лут и отдельный флаг табло её не повышают.
ServerEvents.customCommand('if_advance_epoch', (event) => {
  const server = event.server
  const player = event.player
  const teamId = player ? player.username : 'server'
  const team = ifTeamState(server, teamId)

  const current = team.getInt('tech_epoch')
  if (current >= IF_EPOCH_MAX) {
    if (player) player.tell(`Эпоха уже максимальна: P${current}`)
    return
  }
  const next = ifClamp(current + 1, IF_EPOCH_MIN, IF_EPOCH_MAX)
  team.putInt('tech_epoch', next)
  ifSyncMirrors(server, teamId, team)
  ifAudit(server, teamId, `advance_epoch P${current} -> P${next}`)
  if (player) player.tell(`Эпоха повышена: P${current} → P${next}`)
})
