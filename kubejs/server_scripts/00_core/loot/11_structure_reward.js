// Положительная роль структур: зачем в них вообще лезть.
//
// Дисциплина лута убрала из перестроенных структур то, что обгоняло прогрессию.
// Но убрать мало: если в подземелье нечего искать, оно превращается в декорацию,
// а мастер-документ обещает структурам роль источника образцов и сокращений.
//
// Что кладём и почему именно это. Оба предмета стали в сборке машинными: бумагу
// теперь делает только пресс, андезитовый сплав — основа всей ранней механики.
// Найти их до постройки первой линии — настоящее сокращение пути, но не обход:
// количество маленькое, на фабрику не заменяет и ни одну эпоху не открывает.
//
// Вызовы обёрнуты в защиту: если LootJS этой версии не примет добавление, скрипт
// сообщит об этом в журнал, а не уронит загрузку мира.
LootJS.modifiers((event) => {
  const tables = [
    'minecraft:chests/simple_dungeon',
    'minecraft:chests/desert_pyramid',
    'minecraft:chests/jungle_temple',
    'minecraft:chests/nether_bridge',
    'minecraft:chests/stronghold_corridor',
    'minecraft:chests/stronghold_crossing'
  ]

  // Добавление в этой версии LootJS недоступно: модификатор без действий
  // отвергается целиком. Поэтому используется единственный доказанный вызов —
  // замена. Гниль и тетива меняются на то, что в сборке стало машинным: бумагу
  // и андезитовый сплав. Мусор превращается в повод заглянуть в сундук.
  let done = 0
  tables.forEach((table) => {
    const rule = event.addLootTableModifier(table)
    rule.replaceLoot('minecraft:rotten_flesh', 'minecraft:paper')
    rule.replaceLoot('minecraft:string', 'create:andesite_alloy')
    done += 1
  })

  console.info('[Recast] structure reward: junk turned into pack materials in ' + done + ' tables')
})
