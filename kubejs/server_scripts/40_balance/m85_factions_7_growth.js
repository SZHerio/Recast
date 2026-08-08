// Модуль фракций, часть 7: фракции растут вместе с игроком.
//
// Это правило действует уже во всех предыдущих частях, и здесь оно просто
// собрано в одном месте и показано игроку. Ничего нового модуль тут не решает —
// он объясняет то, что и так происходит:
//
//   * уровень базы считается по эпохе команды, а не по возрасту мира;
//   * снаряжение отряда берётся с той же ступени, что доступна игроку;
//   * набор возможных операций открывается по эпохе.
//
// Смысл в том, что мир не убегает вперёд и не отстаёт. Фракция никогда не
// приходит с тем, чего игрок ещё не видел, и никогда не остаётся с каменными
// мечами, когда у игрока реактор.
//
// Обратное тоже верно и стоит сказать прямо: развитие фракций нельзя
// остановить, отсиживаясь в первой эпохе. Оно привязано к вам, а не к часам.

// Человеческие названия ступеней снаряжения. Совпадают с пресетами отрядов.
const IF_SQUAD_TIER_NAMES = {
  early: 'простое снаряжение: кожа, камень и щит',
  mid: 'железо, выучка и строй',
  late: 'алмазная защита и подготовленные оперативники',
}

ServerEvents.commandRegistry((event) => {
  const commands = event.commands

  const growthNode = commands.literal('growth').executes((context) => {
    const actor = context.source.getEntity()
    if (!actor || !actor.isPlayer()) return 0

    const server = context.source.getServer()
    const team = ifTeamState(server, actor.username)
    const epoch = team.getInt('tech_epoch')
    const tier = ifBaseTierForEpoch(epoch)
    const squadTier = ifSquadTierForEpoch(epoch)

    actor.tell('§6— Как далеко зашли фракции —')
    actor.tell(`Ваша эпоха: §eP${epoch}§r. Фракции равняются на неё.`)
    actor.tell(`Их базы сейчас: ${tier.ru.toLowerCase()}.`)
    actor.tell(`Их отряды носят: ${IF_SQUAD_TIER_NAMES[squadTier]}.`)

    const available = IF_OPERATIONS.filter(
      (operation) => epoch >= operation.min_epoch && epoch <= operation.max_epoch
    ).map((operation) => operation.ru)
    actor.tell(available.length ? `Что они могут предпринять: ${available.join(', ')}.` : 'Пока ничего не предпринимают.')

    const upcoming = IF_OPERATIONS.filter((operation) => operation.min_epoch > epoch)
    if (upcoming.length) {
      const next = upcoming[0]
      actor.tell(`§7Дальше, с P${next.min_epoch}: ${next.ru}.§r`)
    }

    actor.tell('§7Развитие фракций привязано к вам, а не к возрасту мира.§r')
    return 1
  })

  event.register(commands.literal('if_threat').then(growthNode))
})
