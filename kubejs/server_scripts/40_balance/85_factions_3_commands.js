// Модуль фракций, часть 3: как игрок со всем этим разговаривает.
//
// Спецификация запрещает давать внешним системам прямой доступ к состоянию:
// вместо setter принимается узкое намерение, а сервер сам выводит, кто его
// подал, за какую команду и в какой эпохе. Здесь этот вход и сделан.
//
// Команды собраны из готовых слов, а не из свободного текста. Причина не в
// удобстве: свободная строка означала бы, что имя фракции или тип договора
// приходят снаружи и их нужно проверять. Готовые слова проверять не нужно —
// невозможное просто не набирается, а игрок получает подсказку прямо в строке
// ввода.

// Полная карточка состояния: эпоха, отношения со всеми шестью, действующие
// договоры и то, что уже никогда не забудется.
function ifThreatStatus(server, teamId, player) {
  if (!player) return 1
  const team = ifTeamState(server, teamId)

  player.tell('§6— Положение дел —')
  player.tell(`Эпоха: §eP${team.getInt('tech_epoch')}§r`)

  IF_FACTION_LIST.forEach((factionId) => {
    const value = team.getInt('rep_' + factionId)
    player.tell(`${IF_FACTION_DATA[factionId].ru}: §e${value}§r (${ifReputationTier(value)})`)
  })

  const treaties = ifTreaties(team)
  const signed = []
  IF_FACTION_LIST.forEach((factionId) => {
    Object.keys(IF_TREATY_TYPES).forEach((treatyType) => {
      if (treaties.contains(`${factionId}|${treatyType}`)) {
        signed.push(`${IF_FACTION_DATA[factionId].short_ru} — ${IF_TREATY_TYPES[treatyType].ru}`)
      }
    })
  })
  player.tell(signed.length ? `Договоры: ${signed.join('; ')}` : 'Договоров нет.')

  if (team.contains('facts')) {
    const facts = team.get('facts').getAllKeys()
    if (facts.size() > 0) player.tell(`§cЗа вами помнят: ${facts.size()} ${facts.size() === 1 ? 'случай' : 'случая'}.§r`)
  }
  return 1
}

// Досье фракции: чем живёт, как воюет, что считает победой, с кем дружит и с
// кем нет. Плюс то, что для игрока важнее всего — открыт ли прилавок.
function ifThreatDossier(server, teamId, factionId, player) {
  if (!player) return 1
  const data = IF_FACTION_DATA[factionId]
  const team = ifTeamState(server, teamId)
  const reputation = team.getInt('rep_' + factionId)

  player.tell(`§6— ${data.ru} —`)
  player.tell(`Занимается: ${data.focus_ru}`)
  player.tell(`В бою: ${data.doctrine_ru}`)
  player.tell(`Победой считает: ${data.victory_ru}`)
  player.tell(`Отношение к вам: §e${reputation}§r (${ifReputationTier(reputation)})`)

  const allies = data.allies.map((id) => IF_FACTION_DATA[id].short_ru)
  const foes = data.hostile.map((id) => IF_FACTION_DATA[id].short_ru)
  player.tell(allies.length ? `Считает своими: ${allies.join(', ')}` : 'Постоянных союзников нет.')
  player.tell(foes.length ? `§cВ открытой вражде: ${foes.join(', ')}§r` : 'Ни с кем не воюет.')

  if (reputation <= IF_TRADE_CLOSED_AT_OR_BELOW) {
    player.tell('§cТорговать с вами отказываются.§r')
  }

  const available = []
  Object.keys(IF_TREATY_TYPES).forEach((treatyType) => {
    const treaty = IF_TREATY_TYPES[treatyType]
    if (reputation >= treaty.min_reputation && team.getInt('tech_epoch') >= treaty.min_epoch) {
      available.push(treaty.ru)
    }
  })
  player.tell(available.length ? `Готовы обсуждать: ${available.join(', ')}` : 'Обсуждать что-либо пока отказываются.')
  return 1
}

function ifThreatTreatyList(server, teamId, player) {
  if (!player) return 1
  player.tell('§6— Договоры, которые бывают —')
  Object.keys(IF_TREATY_TYPES).forEach((treatyType) => {
    const treaty = IF_TREATY_TYPES[treatyType]
    player.tell(
      `§e${treaty.ru}§r — от ${treaty.min_reputation} отношения и с эпохи P${treaty.min_epoch}. ${treaty.effect_ru}`
    )
  })
  return 1
}

function ifThreatActor(context) {
  const entity = context.source.getEntity()
  return entity && entity.isPlayer() ? entity : null
}

ServerEvents.commandRegistry((event) => {
  const commands = event.commands

  const statusNode = commands.literal('status').executes((context) => {
    const actor = ifThreatActor(context)
    return ifThreatStatus(context.source.getServer(), actor ? actor.username : 'server', actor)
  })

  const factionNode = commands.literal('faction')
  IF_FACTION_LIST.forEach((factionId) => {
    factionNode.then(
      commands.literal(factionId).executes((context) => {
        const actor = ifThreatActor(context)
        return ifThreatDossier(context.source.getServer(), actor ? actor.username : 'server', factionId, actor)
      })
    )
  })

  const treatyNode = commands.literal('treaty')
  treatyNode.then(
    commands.literal('list').executes((context) => {
      const actor = ifThreatActor(context)
      return ifThreatTreatyList(context.source.getServer(), actor ? actor.username : 'server', actor)
    })
  )

  const signNode = commands.literal('sign')
  const breakNode = commands.literal('break')
  IF_FACTION_LIST.forEach((factionId) => {
    const signFaction = commands.literal(factionId)
    const breakFaction = commands.literal(factionId)

    Object.keys(IF_TREATY_TYPES).forEach((treatyType) => {
      signFaction.then(
        commands.literal(treatyType).executes((context) => {
          const actor = ifThreatActor(context)
          if (!actor) return 0
          ifTreatySign(context.source.getServer(), actor.username, factionId, treatyType, actor)
          return 1
        })
      )
      breakFaction.then(
        commands.literal(treatyType).executes((context) => {
          const actor = ifThreatActor(context)
          if (!actor) return 0
          ifTreatyBreak(context.source.getServer(), actor.username, factionId, treatyType, actor)
          return 1
        })
      )
    })

    signNode.then(signFaction)
    breakNode.then(breakFaction)
  })
  treatyNode.then(signNode)
  treatyNode.then(breakNode)

  event.register(commands.literal('if_threat').then(statusNode).then(factionNode).then(treatyNode))
})
