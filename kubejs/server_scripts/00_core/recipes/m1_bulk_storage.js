// Recast M1 reference recipe.
// Eight logs equal the 32 planks used by four vanilla chests. This removes
// repetitive clicks without discounting resources.
ServerEvents.recipes((event) => {
  event
    .shaped(Item.of('minecraft:chest', 4), [
      'LLL',
      'L L',
      'LLL'
    ], {
      L: '#industrial_frontier:materials/wood_logs'
    })
    .id('industrial_frontier:m1/bulk_chest_from_logs')
})
