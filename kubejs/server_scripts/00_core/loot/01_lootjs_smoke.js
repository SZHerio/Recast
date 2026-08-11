// M1 deliberately changes no loot. Registering the exact LootJS event gives
// the owner's latest.log a narrow compatibility signal without affecting play.
LootJS.modifiers(() => {
  console.info('[Recast M1] LootJS modifier event registered; no loot changes applied.')
})
