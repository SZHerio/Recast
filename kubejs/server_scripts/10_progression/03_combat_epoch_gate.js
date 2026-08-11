// M3 weapon-stack integration.
//
// Both combat mods shipped their own way around shared metallurgy:
//   * Epic Knights blasts a plain iron ingot into its own steel ingot, and that
//     item joins forge:ingots/steel. Steel is the P2 milestone that gates the
//     entire electrical era, so this made it a P0 furnace recipe.
//   * Epic Knights also presses a steel plate in the crafting grid, bypassing
//     both the Create press and GregTech precision routes.
//   * TaCZ's gun smith table costs logs and iron, which put the whole firearms
//     domain inside P0/P1.
//
// The fix keeps every mod fully playable and only moves its entry point:
// Epic Knights consumes forge:ingots/steel, which GregTech steel satisfies, and
// the gun smith table now costs P2 steel. Nothing downstream is re-priced.
ServerEvents.recipes((event) => {
  // Steel must come from metallurgy, not from a blast furnace shortcut.
  event.remove({ id: 'magistuarmory:steel_ingot_blasting' })

  // A plate is a pressed or machined form. The crafting grid is neither.
  event.remove({ id: 'magistuarmory:steel_plate' })

  // Firearms open at the end of P2, after steel exists.
  event.remove({ id: 'tacz:gun_smith_table' })
  event
    .shaped('tacz:gun_smith_table', [
      'PPP',
      'IBI',
      'I I'
    ], {
      P: '#industrial_frontier:materials/steel_plates',
      I: '#industrial_frontier:materials/steel_ingots',
      B: 'minecraft:iron_block'
    })
    .id('industrial_frontier:tacz/gun_smith_table_p2')
})
