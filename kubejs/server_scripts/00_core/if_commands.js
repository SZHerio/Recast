// Команды сборки под теми именами, под которыми они обещаны игроку.
//
// Все справочные и служебные команды Recast написаны через
// ServerEvents.customCommand. Это самый короткий способ их объявить, но
// вызываются такие команды не своим именем, а длинной служебной формой
// «/kubejs custom_command <имя>». Книга заданий, протоколы проверки и
// документация при этом обещают короткое «/if_operations».
//
// Расхождение было найдено разбором JAR: в KubeJS 2001.6.5 ветка
// custom_command объявлена без требования прав и принимает имя как аргумент,
// то есть короткого имени у неё нет и быть не может.
//
// Здесь эти короткие имена регистрируются по-настоящему, через
// ServerEvents.commandRegistry. Каждая команда передаёт управление своему
// обработчику, поэтому логика остаётся ровно в одном месте — там, где
// написана. Ни одного поведения этот файл не меняет: он только даёт игроку
// возможность набрать то, что написано в книге.
//
// Права. Разбор показал, что ветка KubeJS доступна любому игроку. Справочные
// команды такими и остаются: они ничего не меняют, а только рассказывают.
// Две команды меняют состояние мира, и они требуют прав оператора.

// Справочные команды: показывают правила, списки и состояние.
const IF_INFO_COMMANDS = [
  'if_intent',
  'if_contracts',
  'if_city_report',
  'if_regional_contracts',
  'if_regional_contract_signals',
  'if_operations',
  'if_treaties',
  'if_squad_loadout',
  'if_nuclear_contract',
  'if_nuclear_operations',
  'if_nuclear_safety',
  'if_spaceport_contract',
  'if_spaceport_signals',
  'if_launch_checklist',
  'if_offworld_base',
  'if_space_lessons',
  'if_strategic_links',
  'if_strategic_rules',
  'if_strategic_zone',
  'if_late_bases',
  'if_late_operations',
  'if_late_squads',
  'if_planetary_network',
  'if_planetary_processes',
  'if_renewables',
  'if_megaprojects',
  'if_endgame_bases',
  'if_endgame_operations',
  'if_endgame_resolutions',
]

// Команды, меняющие состояние: только для оператора.
const IF_OPERATOR_COMMANDS = ['if_city_contract_closed']

// Передача управления обработчику. Выполняется от лица того, кто набрал
// команду, иначе обработчик не увидит игрока и промолчит.
function ifDelegate(context, id) {
  const source = context.source
  const entity = source.getEntity()
  if (entity) {
    entity.runCommandSilent(`kubejs custom_command ${id}`)
  } else {
    source.getServer().runCommandSilent(`kubejs custom_command ${id}`)
  }
  return 1
}

ServerEvents.commandRegistry((event) => {
  const commands = event.commands

  IF_INFO_COMMANDS.forEach((id) => {
    event.register(commands.literal(id).executes((context) => ifDelegate(context, id)))
  })

  IF_OPERATOR_COMMANDS.forEach((id) => {
    event.register(
      commands
        .literal(id)
        .requires((source) => source.hasPermission(2))
        .executes((context) => ifDelegate(context, id))
    )
  })

  // Единственная рабочая административная точка повышения эпохи. Она не
  // делегирует в публичный custom_command и поэтому не обходится длинной
  // командой KubeJS без проверки прав.
  event.register(
    commands
      .literal('if_advance_epoch')
      .requires((source) => source.hasPermission(2))
      .executes((context) => {
        const source = context.source
        const actor = source.getEntity()
        if (!actor) return 0
        return ifAdminAdvanceEpoch(source.getServer(), actor, 'manual operator command')
      })
  )

  console.info(
    `[Recast] команды сборки зарегистрированы: ${IF_INFO_COMMANDS.length} справочных, ${IF_OPERATOR_COMMANDS.length + 1} операторских`
  )
})
