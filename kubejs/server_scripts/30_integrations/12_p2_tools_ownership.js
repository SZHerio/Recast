// P2 «Инструменты»: у железного набора один владелец — GregTech.
//
// После включения hardToolArmorRecipes ванильный железный инструмент получил тот
// же рецепт, что и инструмент GregTech: два одинаковых крафта на один результат.
// Это прямое нарушение правила линии — у операции должен быть один владелец.
//
// Ванильный набор снят, остаётся набор GregTech: он живёт дольше, чинится и
// встроен в материальную лестницу сборки.
//
// Деревянные и каменные оставлены: это первые часы, до всякой промышленности.
// Алмазные и незеритовые тоже остаются — у них аналога в GregTech нет, и снятие
// оставило бы игрока без верхней ступени.
ServerEvents.recipes((event) => {
  const removed = [
    'minecraft:iron_pickaxe',
    'minecraft:iron_axe',
    'minecraft:iron_shovel',
    'minecraft:iron_hoe',
    'minecraft:iron_sword',
    'minecraft:golden_pickaxe',
    'minecraft:golden_axe',
    'minecraft:golden_shovel',
    'minecraft:golden_hoe',
    'minecraft:golden_sword'
  ]

  removed.forEach((item) => {
    event.remove({ type: 'minecraft:crafting_shaped', output: item })
  })

  console.info('[Recast] P2 tools: ' + removed.length + ' vanilla metal tools removed, GregTech set is the single owner')
})
