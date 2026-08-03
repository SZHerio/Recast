// M2 process-ownership gates.
//
// Create keeps its visible mechanical processing, but its stock ore recipes
// cannot turn unified GTCEu raw materials into a parallel beneficiation line.
// Curated Create -> concentrate hand-offs will be introduced with the P0-P3
// vertical slice after their yields and automation points are specified.
ServerEvents.recipes((event) => {
  const rawMetalFamilies = [
    'aluminum',
    'copper',
    'gold',
    'iron',
    'lead',
    'nickel',
    'osmium',
    'platinum',
    'quicksilver',
    'silver',
    'tin',
    'uranium',
    'zinc'
  ]

  const directOreFamilies = rawMetalFamilies.concat([
    'coal',
    'diamond',
    'emerald',
    'lapis',
    'redstone'
  ])

  directOreFamilies.forEach((material) => {
    event.remove({ id: `create:crushing/${material}_ore` })
    event.remove({ id: `create:crushing/deepslate_${material}_ore` })
  })

  rawMetalFamilies.forEach((material) => {
    event.remove({ id: `create:crushing/raw_${material}` })
    event.remove({ id: `create:crushing/raw_${material}_block` })
  })

  ;[
    'create:crushing/nether_gold_ore',
    'create:crushing/nether_quartz_ore',
    'create:crushing/tuff',
    'create:crushing/tuff_recycling',
    'create:splashing/crushed_raw_copper',
    'create:splashing/crushed_raw_gold',
    'create:splashing/crushed_raw_iron',
    'create:splashing/crushed_raw_zinc',
    'create:smelting/copper_ingot_from_crushed',
    'create:smelting/gold_ingot_from_crushed',
    'create:smelting/iron_ingot_from_crushed',
    'create:smelting/zinc_ingot_from_crushed',
    'create:blasting/copper_ingot_from_crushed',
    'create:blasting/gold_ingot_from_crushed',
    'create:blasting/iron_ingot_from_crushed',
    'create:blasting/zinc_ingot_from_crushed',
    'create:smelting/zinc_ingot_from_ore',
    'create:smelting/zinc_ingot_from_raw_ore',
    'create:blasting/zinc_ingot_from_ore',
    'create:blasting/zinc_ingot_from_raw_ore',
    'create:splashing/immersiveengineering/crushed_raw_aluminum',
    'create:splashing/immersiveengineering/crushed_raw_lead',
    'create:splashing/immersiveengineering/crushed_raw_nickel',
    'create:splashing/immersiveengineering/crushed_raw_silver',
    'create:splashing/immersiveengineering/crushed_raw_uranium'
  ].forEach((recipeId) => event.remove({ id: recipeId }))

  // The stock recipe models brass as 1 Cu + 1 Zn. GTCEu's canonical brass
  // composition is 3 Cu + 1 Zn, so the Create route is retained with honest
  // stoichiometry and a canonical GTCEu output.
  event.remove({ id: 'create:mixing/brass_ingot' })
  event.recipes.create
    .mixing('4x gtceu:brass_ingot', [
      '3x #forge:ingots/copper',
      '#forge:ingots/zinc'
    ])
    .heated()
    .id('industrial_frontier:m2/create/brass_from_copper_zinc')
})
