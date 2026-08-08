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
const IF_FTBQ_TEAM_DATA = Java.loadClass('dev.ftb.mods.ftbquests.quest.TeamData')
const IF_NBT_STRING_TAG = Java.loadClass('net.minecraft.nbt.StringTag')
const IF_UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const IF_AUDIT_LIMIT = 256

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

// Авторитетный ключ — UUID команды FTB Quests. Имя игрока допустимо только
// как вход старого вызова: для находящегося в сети игрока оно немедленно
// разрешается в командный UUID. Новые данные под username не создаются.
function ifTeamIdForPlayer(player) {
  if (!player) return 'server'
  try {
    const questData = IF_FTBQ_TEAM_DATA.get(player)
    if (questData) return String(questData.getTeamId())
  } catch (error) {
    console.error(`[Recast][ThreatDirector] не удалось получить UUID команды FTB Quests: ${error}`)
  }

  // Аварийный UUID игрока не смешивается с username и остаётся стабильным.
  // При исправной FTB Quests эта ветка никогда не должна использоваться.
  return String(player.uuid)
}

function ifResolveTeamId(server, teamRef) {
  if (!teamRef) return 'server'
  if (typeof teamRef !== 'string') return ifTeamIdForPlayer(teamRef)
  if (teamRef === 'server' || IF_UUID_PATTERN.test(teamRef)) return teamRef

  const online = server.getPlayerList().getPlayerByName(teamRef)
  if (online) return ifTeamIdForPlayer(online)

  // Старые offline-вызовы читают прежний ключ, но не создают под ним новое
  // командное состояние. Все штатные изменения происходят при online actor.
  return `legacy:${teamRef}`
}

function ifMigrateLegacyTeamState(server, teamId, legacyName) {
  if (!legacyName || legacyName === teamId) return
  const teams = ifState(server).get('teams')
  if (!teams.contains(teamId) && teams.contains(legacyName)) {
    teams.put(teamId, teams.get(legacyName).copy())
    ifAudit(server, teamId, `migrated legacy username state ${legacyName}`)
  }
}

function ifTeamState(server, teamRef) {
  const legacyName =
    typeof teamRef === 'string' && teamRef !== 'server' && !IF_UUID_PATTERN.test(teamRef)
      ? teamRef
      : null
  const teamId = ifResolveTeamId(server, teamRef)
  if (legacyName && !teamId.startsWith('legacy:')) {
    ifMigrateLegacyTeamState(server, teamId, legacyName)
  }
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

function ifTeamStateForPlayer(server, player) {
  const teamId = ifTeamIdForPlayer(player)
  ifMigrateLegacyTeamState(server, teamId, player ? player.username : null)
  return ifTeamState(server, teamId)
}

// Журнал пишется всегда: изменение состояния без записи причины запрещено.
function ifAudit(server, teamId, reason) {
  const state = ifState(server)
  if (!state.contains('audit')) state.put('audit', [])
  const line = `${teamId}|${reason}`
  const audit = state.get('audit')
  audit.add(IF_NBT_STRING_TAG.valueOf(line))
  while (audit.size() > IF_AUDIT_LIMIT) audit.remove(0)
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
  const teamId = player ? ifTeamIdForPlayer(player) : 'server'
  const team = player ? ifTeamStateForPlayer(server, player) : ifTeamState(server, teamId)

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

// Recovery-переход вызывается только короткой операторской командой,
// зарегистрированной через commandRegistry. Публичная ветка custom_command
// намеренно ничего не меняет: иначе её можно было бы вызвать напрямую без OP.
ServerEvents.customCommand('if_advance_epoch', (event) => {
  const player = event.player
  if (player) {
    player.tell('§cЭта служебная форма команды отключена. Для восстановления используйте операторскую /if_advance_epoch.')
  }
})

// Атомарное изменение для commissioning-моста и административного recovery.
// expectedCurrent защищает от пропуска эпохи и повторной обработки события.
function ifSetEpochAfterCommissioning(server, teamId, completedEpoch, reason) {
  const team = ifTeamState(server, teamId)
  const current = team.getInt('tech_epoch')

  if (completedEpoch < IF_EPOCH_MIN || completedEpoch > IF_EPOCH_MAX) {
    ifAudit(server, teamId, `commissioning rejected invalid P${completedEpoch}`)
    return { changed: false, current: current, reason: 'INVALID_EPOCH' }
  }

  if (current < completedEpoch) {
    ifAudit(server, teamId, `commissioning rejected out_of_order current=P${current} completed=P${completedEpoch}`)
    return { changed: false, current: current, reason: 'OUT_OF_ORDER' }
  }

  if (current > completedEpoch) {
    ifAudit(server, teamId, `commissioning ignored already_advanced current=P${current} completed=P${completedEpoch}`)
    return { changed: false, current: current, reason: 'ALREADY_ADVANCED' }
  }

  if (completedEpoch === IF_EPOCH_MAX) {
    if (!team.getBoolean('p9_commissioned')) {
      team.putBoolean('p9_commissioned', true)
      ifSyncMirrors(server, teamId, team)
      ifAudit(server, teamId, `${reason}; commissioned P9 finale`)
      return { changed: true, current: current, next: current, reason: 'P9_COMMISSIONED' }
    }
    return { changed: false, current: current, reason: 'ALREADY_COMMISSIONED' }
  }

  const next = completedEpoch + 1
  team.putInt('tech_epoch', next)
  ifSyncMirrors(server, teamId, team)
  ifAudit(server, teamId, `${reason}; advance_epoch P${current} -> P${next}`)
  return { changed: true, current: current, next: next, reason: 'ADVANCED' }
}

function ifAdminAdvanceEpoch(server, player, reason) {
  if (!player) return 0
  const teamId = ifTeamIdForPlayer(player)
  const team = ifTeamStateForPlayer(server, player)

  const current = team.getInt('tech_epoch')
  if (current >= IF_EPOCH_MAX) {
    player.tell(`Эпоха уже максимальна: P${current}`)
    return 0
  }
  const result = ifSetEpochAfterCommissioning(server, teamId, current, `operator recovery: ${reason}`)
  if (result.changed) player.tell(`§6Восстановление прогресса: P${current} → P${result.next}`)
  return result.changed ? 1 : 0
}
