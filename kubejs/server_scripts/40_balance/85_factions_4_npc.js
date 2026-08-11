// Модуль фракций, часть 4: живые люди фракций.
//
// До этого места фракции были числами. Здесь у них появляются посланники —
// те, с кем можно поговорить, договориться и, если очень захотеть, поссориться
// навсегда.
//
// Посланники описаны пресетами в kubejs/data/industrial_frontier/preset и
// собираются генератором tools/generate_faction_npc.py. Разговор у них не
// декоративный: кнопка «предложить союз» появляется, только когда отношения
// действительно дозрели, потому что условие кнопки читает то же табло, в
// которое ядро зеркалит репутацию и эпоху. Решает сервер, а не текст.
//
// Убийство переговорщика стоит восемнадцати пунктов и не забывается. Это не
// наказание ради наказания: без цены разговор перестаёт быть выбором, потому
// что молча убить всегда было бы выгоднее.

// Пресет посланника в датапаке сборки.
function ifEnvoyPreset(factionId) {
  return `industrial_frontier:preset/${factionId}_envoy.npc.snbt`
}

// Появление посланника в точке. Используется базами фракций и операторской
// командой проверки.
function ifSpawnEnvoy(server, factionId, x, y, z) {
  if (!IF_FACTION_DATA[factionId]) {
    console.error(`[Recast][Фракции] попытка призвать посланника неизвестной фракции: ${factionId}`)
    return false
  }
  server.runCommandSilent(`easy_npc preset import_new data ${ifEnvoyPreset(factionId)} ${x} ${y} ${z}`)
  console.info(`[Recast][Фракции] посланник ${factionId} размещён: ${x} ${y} ${z}`)
  return true
}

// Кто именно погиб. Easy NPC хранит принадлежность строковым тегом, поэтому
// фракцию убитого можно узнать, не заводя собственного учёта существ.
function ifEntityFaction(entity) {
  if (!entity) return null
  const nbt = entity.nbt
  if (!nbt || !nbt.contains('FactionName')) return null
  const factionId = nbt.getString('FactionName')
  return IF_FACTION_DATA[factionId] ? factionId : null
}

EntityEvents.death((event) => {
  const factionId = ifEntityFaction(event.entity)
  if (!factionId) return

  const source = event.source
  const attacker = source ? source.getEntity() : null
  if (!attacker || !attacker.isPlayer()) return

  // Пока фракции представлены только переговорщиками, и все они мирные.
  // Отряды получают свою причину в части про развитие фракций.
  ifApplyReputation(event.server, attacker.username, factionId, 'civilian_killed', null, attacker)
  ifFactBrand(event.server, attacker.username, `envoy_killed/${factionId}`)
})

ServerEvents.commandRegistry((event) => {
  const commands = event.commands

  // Вызов посланника к себе. Команда операторская: это средство проверки и
  // аварийного восстановления, а не способ получить переговоры без базы.
  const envoyNode = commands.literal('envoy').requires((source) => source.hasPermission(2))
  IF_FACTION_LIST.forEach((factionId) => {
    envoyNode.then(
      commands.literal(factionId).executes((context) => {
        const source = context.source
        const actor = source.getEntity()
        if (!actor) return 0
        const position = actor.block
        ifSpawnEnvoy(source.getServer(), factionId, position.x, position.y, position.z)
        if (actor.isPlayer()) actor.tell(`Посланник вызван: ${IF_FACTION_DATA[factionId].ru}`)
        return 1
      })
    )
  })

  event.register(commands.literal('if_threat').then(envoyNode))
})
