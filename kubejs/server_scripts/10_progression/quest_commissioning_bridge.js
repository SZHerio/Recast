// Quest commissioning → authoritative tech_epoch bridge.
//
// FTB XMod Compat публикует событие completed отдельно для каждого quest tag.
// Компилятор Quest Source v2 обязан дать ровно одному commissioning-квесту
// каждой эпохи tag if_commissioning_pN. Minecraft этим файлом не запускается;
// фактическое срабатывание остаётся пользовательским runtime-gate.

function ifCommissioningTeamId(event) {
  try {
    return String(event.data.getData().getTeamId())
  } catch (error) {
    console.error(`[Recast][QuestBridge] не удалось получить UUID команды: ${error}`)
    return null
  }
}

function ifNotifyCommissioningMembers(event, message) {
  try {
    event.onlineMembers.forEach((member) => member.tell(message))
  } catch (error) {
    if (event.player) event.player.tell(message)
  }
}

function ifHandleCommissioning(event, completedEpoch) {
  const teamId = ifCommissioningTeamId(event)
  if (!teamId || !event.player) return
  const server = event.server
  ifMigrateLegacyTeamState(server, teamId, event.player.username)
  const result = ifSetEpochAfterCommissioning(
    server,
    teamId,
    completedEpoch,
    `quest commissioning tag if_commissioning_p${completedEpoch}`
  )

  if (result.changed && completedEpoch < 9) {
    ifNotifyCommissioningMembers(
      event,
      `§aЭпоха P${completedEpoch} введена в эксплуатацию. Команда переходит к P${result.next}.`
    )
  } else if (result.changed) {
    ifNotifyCommissioningMembers(event, '§aФинальная система P9 введена в эксплуатацию.')
  } else if (result.reason === 'OUT_OF_ORDER') {
    ifNotifyCommissioningMembers(
      event,
      `§cПереход не выполнен: текущая эпоха команды P${result.current}, а завершён commissioning P${completedEpoch}. Сообщите об этом как об ошибке миграции.`
    )
  }
}

for (let epoch = 0; epoch <= 9; epoch++) {
  const commissioningEpoch = epoch
  FTBQuestsEvents.completed(`#if_commissioning_p${commissioningEpoch}`, (event) => {
    ifHandleCommissioning(event, commissioningEpoch)
  })
}
