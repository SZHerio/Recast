// AE2 is the P5 order-and-storage domain. Its seven stock entry roots are
// removed now so an unmodified vanilla-tier recipe cannot open the domain in
// P0-P2. M5 will add the complete, taught replacement contract.
ServerEvents.recipes((event) => {
  ;[
    'ae2:network/blocks/crystal_processing_charger',
    'ae2:network/blocks/inscribers',
    'ae2:network/blocks/energy_energy_acceptor',
    'ae2:transform/fluix_crystals',
    'ae2:inscriber/calculation_processor',
    'ae2:inscriber/engineering_processor',
    'ae2:inscriber/logic_processor'
  ].forEach((recipeId) => event.remove({ id: recipeId }))
})
