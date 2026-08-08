// Модуль фракций, часть 5: базы, которые живут.
//
// Постройки фракций расставляет генерация мира — это файлы датапака, собранные
// tools/generate_faction_bases.py. Но постройка сама по себе мертва: в ней
// никого нет и ничего не происходит.
//
// Здесь база оживает. Когда игрок впервые приходит на неё, сборка решает, кто
// его встретит: уровень базы считается по эпохе команды, а не по возрасту
// мира. Тысяча дней в первой эпохе не превращает лагерь в военный комплекс —
// это прямое требование спецификации, и оно единственное, что отделяет живой
// мир от лавины.
//
// Проверка присутствия сделана предикатами датапака: сборка спрашивает у мира
// один вопрос — стоит ли игрок сейчас на базе такой-то фракции. Другого
// способа узнать о приходе игрока в структуру у сборки нет.

// Как часто спрашивать. Раз в десять секунд: достаточно, чтобы встреча
// казалась мгновенной, и достаточно редко, чтобы ничего не нагружать.
const IF_BASE_SCAN_INTERVAL_TICKS = 200

// Уровень базы по эпохе команды.
//
// В таблице у каждого уровня записан свой потолок эпохи: ранний лагерь живёт
// до P0, укреплённый до P2, и так далее. Значит нужный уровень — первый, чей
// потолок ещё не пройден. В восьмой эпохе это высокотехнологичный объект, а не
// военный комплекс, который к тому времени уже устарел.
function ifBaseTierForEpoch(epoch) {
  for (let index = 0; index < IF_BASE_LEVELS.length; index++) {
    if (IF_BASE_LEVELS[index].max_epoch >= epoch) return IF_BASE_LEVELS[index]
  }
  return IF_BASE_LEVELS[IF_BASE_LEVELS.length - 1]
}

// Уже обжитые базы. Ключ — фракция и участок мира, чтобы одна и та же база не
// заселялась дважды, а соседняя всё же заселилась.
function ifSettledBases(server) {
  const state = ifState(server)
  if (!state.contains('settled_bases')) state.put('settled_bases', {})
  return state.get('settled_bases')
}

function ifBaseKey(factionId, block) {
  const sectorX = Math.floor(block.x / 128)
  const sectorZ = Math.floor(block.z / 128)
  return `${factionId}|${block.level.dimension}|${sectorX}|${sectorZ}`
}

// Заселение базы. Посланник появляется всегда: с фракцией должно быть кому
// говорить. Всё остальное зависит от уровня.
function ifSettleBase(server, player, factionId) {
  const settled = ifSettledBases(server)
  const block = player.block
  const key = ifBaseKey(factionId, block)
  if (settled.contains(key)) return false

  const team = ifTeamState(server, player.username)
  const epoch = team.getInt('tech_epoch')
  const tier = ifBaseTierForEpoch(epoch)

  settled.putString(key, tier.id)
  ifSpawnEnvoy(server, factionId, block.x, block.y + 1, block.z)
  ifAudit(server, player.username, `base settled ${factionId} ${tier.id} at ${block.x} ${block.z}`)

  const data = IF_FACTION_DATA[factionId]
  player.tell(`§6${data.ru}§r. Это их ${tier.ru.toLowerCase()}.`)
  player.tell(`${data.focus_ru} Здесь есть с кем поговорить.`)

  const reputation = team.getInt('rep_' + factionId)
  if (reputation <= IF_TRADE_CLOSED_AT_OR_BELOW) {
    player.tell('§cВас узнали. Разговора не будет.§r')
  }
  return true
}

// Опрос: кто из игроков стоит на чьей базе.
function ifScanBases(server) {
  const players = server.getPlayers()
  if (!players || players.length === 0) return

  players.forEach((player) => {
    IF_FACTION_LIST.forEach((factionId) => {
      const inside = server.runCommandSilent(
        `execute as ${player.username} at @s if predicate industrial_frontier:in_base_${factionId}`
      )
      if (inside > 0) ifSettleBase(server, player, factionId)
    })
  })
}

let ifBaseScanCountdown = IF_BASE_SCAN_INTERVAL_TICKS

ServerEvents.tick((event) => {
  ifBaseScanCountdown -= 1
  if (ifBaseScanCountdown > 0) return
  ifBaseScanCountdown = IF_BASE_SCAN_INTERVAL_TICKS
  ifScanBases(event.server)
})
