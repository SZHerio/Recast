// Модуль фракций, часть 2: ядро состояния.
//
// Что здесь появляется впервые за девять волн: репутация начинает меняться, а
// договоры вообще начинают существовать. До этого состояние умело только
// показывать себя и повышать эпоху вручную.
//
// Правило, ради которого всё написано именно так: репутация не может
// измениться «просто так». Каждое изменение приходит с причиной из известного
// списка, величина берётся из таблицы, а игрок видит не только новое число, но
// и то, за что оно изменилось. Произвольного setter нет ни для одной системы.
//
// Состояние живёт там же, где и раньше — в сохранённых данных сервера, ключ
// industrial_frontier. Ядро Threat Director остаётся единственным владельцем.
//
// Движок фракций берётся у Easy NPC 7.4.1: у него есть сохраняемый список
// фракций, цвета и взаимная вражда, а его NPC умеют цель «атаковать
// враждебные фракции». Мы объявляем ему наши шесть фракций и матрицу вражды
// из досье — дальше он сам следит, кто кому противник.

// Отметка о том, что причина уже засчитана. Без неё один и тот же разговор
// приносил бы репутацию сколько угодно раз.
function ifReputationLedger(team) {
  if (!team.contains('rep_ledger')) team.put('rep_ledger', {})
  return team.get('rep_ledger')
}

// Изменение репутации. Единственный способ её сдвинуть.
//
// reasonCode обязан быть из таблицы причин; targetKey — то, к чему причина
// привязана: узел разговора, операция, договор. Для причин, которые
// засчитываются однократно, пара «причина + цель» запоминается.
function ifApplyReputation(server, teamId, factionId, reasonCode, targetKey, player) {
  const reason = IF_REPUTATION_REASONS[reasonCode]
  if (!reason) {
    console.error(`[Recast][Фракции] неизвестная причина изменения репутации: ${reasonCode}`)
    return 0
  }
  if (!IF_FACTION_DATA[factionId]) {
    console.error(`[Recast][Фракции] неизвестная фракция: ${factionId}`)
    return 0
  }

  const team = ifTeamState(server, teamId)
  const ledgerKey = `${factionId}|${reasonCode}|${targetKey || 'general'}`
  if (reason.once) {
    const ledger = ifReputationLedger(team)
    if (ledger.contains(ledgerKey)) return 0
    ledger.putBoolean(ledgerKey, true)
  }

  const field = 'rep_' + factionId
  const before = team.getInt(field)
  const after = ifClamp(before + reason.delta, IF_REP_MIN, IF_REP_MAX)
  team.putInt(field, after)

  // Связанные фракции. Матрица отношений объявлена заранее и работает только
  // на заметные события: мелкая торговля не пересказывается по всему миру.
  if (Math.abs(reason.delta) >= 10) {
    ifSpreadReputation(server, teamId, factionId, reason.delta)
  }

  ifSyncMirrors(server, teamId, team)
  ifAudit(server, teamId, `reputation ${factionId} ${before} -> ${after} (${reasonCode})`)

  if (player) {
    const name = IF_FACTION_DATA[factionId].short_ru
    const sign = after > before ? '+' : ''
    player.tell(`${name}: ${sign}${after - before} → ${after} (${ifReputationTier(after)}). Причина: ${reason.ru}.`)
  }
  return after - before
}

// Последствия для союзников и противников. Половина величины союзникам с тем
// же знаком, треть противникам с обратным: враг моего врага замечает.
function ifSpreadReputation(server, teamId, factionId, delta) {
  const team = ifTeamState(server, teamId)
  const data = IF_FACTION_DATA[factionId]

  data.allies.forEach((ally) => {
    const allyField = 'rep_' + ally
    team.putInt(allyField, ifClamp(team.getInt(allyField) + Math.round(delta / 2), IF_REP_MIN, IF_REP_MAX))
  })
  data.hostile.forEach((foe) => {
    const foeField = 'rep_' + foe
    team.putInt(foeField, ifClamp(team.getInt(foeField) - Math.round(delta / 3), IF_REP_MIN, IF_REP_MAX))
  })
}

// Договоры команды с фракцией.
function ifTreaties(team) {
  if (!team.contains('treaties')) team.put('treaties', {})
  return team.get('treaties')
}

function ifTreatySign(server, teamId, factionId, treatyType, player) {
  const treaty = IF_TREATY_TYPES[treatyType]
  if (!treaty || !IF_FACTION_DATA[factionId]) {
    if (player) player.tell('Такого договора не существует.')
    return false
  }

  const team = ifTeamState(server, teamId)
  const treaties = ifTreaties(team)
  if (treaties.contains(`${factionId}|${treatyType}`)) {
    if (player) player.tell(`Такой договор уже действует: ${treaty.ru}.`)
    return false
  }

  const reputation = team.getInt('rep_' + factionId)
  const epoch = team.getInt('tech_epoch')
  const name = IF_FACTION_DATA[factionId].short_ru

  if (reputation < treaty.min_reputation) {
    if (player) {
      player.tell(
        `${name} не станет обсуждать «${treaty.ru}»: нужно отношение не ниже ${treaty.min_reputation}, сейчас ${reputation}.`
      )
    }
    return false
  }
  if (epoch < treaty.min_epoch) {
    if (player) player.tell(`«${treaty.ru}» обсуждают не раньше эпохи P${treaty.min_epoch}. Сейчас P${epoch}.`)
    return false
  }

  treaties.putBoolean(`${factionId}|${treatyType}`, true)
  ifApplyReputation(server, teamId, factionId, 'treaty_signed', treatyType, null)
  ifAudit(server, teamId, `treaty signed ${factionId}/${treatyType}`)
  if (player) player.tell(`Договор заключён: ${name}, ${treaty.ru}. ${treaty.effect_ru}`)
  return true
}

// Разрыв договора. Это единственное действие модуля, у которого нет дешёвого
// исхода: нарушение стоит сорок пунктов и запоминается фактом навсегда.
function ifTreatyBreak(server, teamId, factionId, treatyType, player) {
  const treaty = IF_TREATY_TYPES[treatyType]
  if (!treaty || !IF_FACTION_DATA[factionId]) return false

  const team = ifTeamState(server, teamId)
  const treaties = ifTreaties(team)
  const key = `${factionId}|${treatyType}`
  if (!treaties.contains(key)) {
    if (player) player.tell('Такого договора нет.')
    return false
  }

  treaties.remove(key)
  ifFactBrand(server, teamId, `treaty_broken/${factionId}/${treatyType}`)
  ifApplyReputation(server, teamId, factionId, 'treaty_broken', null, player)
  ifAudit(server, teamId, `treaty broken ${factionId}/${treatyType}`)
  if (player) player.tell(`Договор разорван: ${IF_FACTION_DATA[factionId].short_ru}, ${treaty.ru}. Это запомнят.`)
  return true
}

// Факты. То, что нельзя стереть торговлей: предательство, спасение командира,
// раскрытая ложь. Хранятся отдельно от чисел, потому что число можно отыграть
// обратно, а факт — нет.
function ifFactBrand(server, teamId, factId) {
  const team = ifTeamState(server, teamId)
  if (!team.contains('facts')) team.put('facts', {})
  team.get('facts').putBoolean(factId, true)
  ifAudit(server, teamId, `fact ${factId}`)
}

function ifFactKnown(server, teamId, factId) {
  const team = ifTeamState(server, teamId)
  if (!team.contains('facts')) return false
  return team.get('facts').contains(factId)
}

// Объявление наших фракций движку Easy NPC.
//
// Делается один раз при загрузке мира. Команды идемпотентны: повторное
// создание существующей фракции движок игнорирует, поэтому проверять его
// состояние не нужно.
function ifDeclareFactions(server) {
  IF_FACTION_LIST.forEach((factionId) => {
    const data = IF_FACTION_DATA[factionId]
    server.runCommandSilent(`easy_npc faction create ${factionId}`)
    server.runCommandSilent(`easy_npc faction color ${factionId} ${data.color}`)
  })

  // Вражда объявляется взаимной: в досье обеих сторон причина названа.
  IF_FACTION_LIST.forEach((factionId) => {
    IF_FACTION_DATA[factionId].hostile.forEach((foe) => {
      server.runCommandSilent(`easy_npc faction hostile add ${factionId} ${foe} mutual`)
    })
  })

  console.info(`[Recast][Фракции] объявлено движку: ${IF_FACTION_LIST.length} фракций и матрица вражды`)
}

ServerEvents.loaded((event) => {
  ifDeclareFactions(event.server)
})
