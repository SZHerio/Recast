// Единый вход алюминиевой линии P4.
//
// GregTech генерирует мацерацию только для собственных форм aluminium. Между
// тем HBM, Immersive Engineering и Creating Space регистрируют совместимое
// алюминиевое сырьё в британских и американских Forge-тегах. Квест принимает
// обе семьи, поэтому каждый внешний вход обязан вести в тот же канонический
// промежуточный продукт, а не завершаться после формальной проверки тега.
//
// Мост сохраняет баланс штатного сырьевого рецепта: одна единица сырья даёт
// две дроблёные единицы GregTech в мацераторе LV. Побочный продукт намеренно
// не добавлен — внешняя руда получает совместимость, но не преимущество над
// полноценной рудной цепью GregTech.
ServerEvents.recipes((event) => {
  const externalAluminiumSources = [
    ['hbm_ntm_rebirth:ore_aluminium', 'hbm_ore'],
    ['immersiveengineering:raw_aluminum', 'ie_raw'],
    ['immersiveengineering:ore_aluminum', 'ie_ore'],
    ['immersiveengineering:deepslate_ore_aluminum', 'ie_deepslate_ore'],
    ['creatingspace:raw_aluminum', 'creating_space_raw'],
    ['creatingspace:moon_aluminum_ore', 'creating_space_moon_ore']
  ]

  externalAluminiumSources.forEach(([input, suffix]) => {
    event.recipes.gtceu.macerator(`industrial_frontier:aluminium/${suffix}_to_crushed`)
      .itemInputs(input)
      .itemOutputs('2x gtceu:crushed_aluminium_ore')
      .duration(400)
      .EUt(30)
  })

  console.info(`[Recast] Алюминиевая линия P4: ${externalAluminiumSources.length} внешних источников сведены к дроблёной форме GregTech.`)
})
