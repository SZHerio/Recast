// Material-equivalent KubeJS Create smoke recipe: the vanilla 4:1 clay
// compression remains available as a mixer batch operation.
ServerEvents.recipes((event) => {
  event.recipes.create
    .mixing('minecraft:clay', ['4x minecraft:clay_ball'])
    .id('industrial_frontier:m1/create/batch_clay_block')
})
