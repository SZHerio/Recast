// Ограничение боезапаса Create Big Cannons.
//
// Штатные снаряды мода стоят железа и деревянной плиты, то есть тяжёлая
// артиллерия доступна в P1 — раньше стали, раньше пороховой химии и намного
// раньше того, как у игрока появится что защищать.
//
// Разделение по разрушительности, а не запрет мода:
//
//   ядро, картечь, дымовой   остаются железными — пушка работает с P2
//   фугасный, бронебойный,   переносятся за сталь P2 и капсюльную химию,
//   осколочный, жидкостный   то есть в ту же эпоху, что и городские узлы
//
// Так пушка остаётся ранней игрушкой ближнего боя, а способность сносить
// укрепление приходит вместе с промышленностью, которая её объясняет.
ServerEvents.recipes((event) => {
  const heavyShells = [
    'createbigcannons:he_shell',
    'createbigcannons:ap_shell',
    'createbigcannons:shrapnel_shell',
    'createbigcannons:fluid_shell'
  ]
  heavyShells.forEach((recipeId) => event.remove({ id: recipeId }))

  // Форма рецептов сохранена от мода: те же четыре ряда механической сборки,
  // железо заменено на стальную пластину эпохи P2.
  event.custom({
    type: 'create:mechanical_crafting',
    acceptMirrored: true,
    key: {
      I: { item: 'gtceu:steel_plate' },
      S: { tag: 'minecraft:wooden_slabs' },
      T: { tag: 'createbigcannons:high_explosive_materials' }
    },
    pattern: [' I ', 'ITI', 'ITI', ' S '],
    result: { item: 'createbigcannons:he_shell' }
  }).id('industrial_frontier:ordnance/he_shell')

  event.custom({
    type: 'create:mechanical_crafting',
    acceptMirrored: true,
    key: {
      C: { item: 'gtceu:steel_ingot' },
      I: { item: 'gtceu:steel_plate' },
      S: { tag: 'minecraft:wooden_slabs' },
      T: { tag: 'createbigcannons:high_explosive_materials' }
    },
    pattern: [' C ', 'ICI', 'ITI', ' S '],
    result: { item: 'createbigcannons:ap_shell' }
  }).id('industrial_frontier:ordnance/ap_shell')

  event.custom({
    type: 'create:mechanical_crafting',
    acceptMirrored: true,
    key: {
      I: { item: 'gtceu:steel_plate' },
      L: { item: 'createbigcannons:shot_balls' },
      P: { tag: 'createbigcannons:gunpowder' },
      S: { tag: 'minecraft:wooden_slabs' }
    },
    pattern: [' I ', 'ILI', 'IPI', ' S '],
    result: { item: 'createbigcannons:shrapnel_shell' }
  }).id('industrial_frontier:ordnance/shrapnel_shell')

  event.custom({
    type: 'create:mechanical_crafting',
    acceptMirrored: true,
    key: {
      I: { item: 'gtceu:steel_plate' },
      P: { item: 'create:fluid_pipe' },
      S: { tag: 'minecraft:wooden_slabs' }
    },
    pattern: [' I ', 'IPI', 'IPI', ' S '],
    result: { item: 'createbigcannons:fluid_shell' }
  }).id('industrial_frontier:ordnance/fluid_shell')

  console.info(
    `[Recast] Боезапас CBC: ${heavyShells.length} разрушительных снарядов перенесены за сталь P2; ядро, картечь и дымовой остались ранними.`
  )
})
