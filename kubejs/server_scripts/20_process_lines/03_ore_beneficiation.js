// Курируемый маршрут «руда → механический концентрат», отложенный в M2 до M3.
//
// M2 удалил штатное дробление руды в Create: оно давало второй, более дешёвый
// путь к тому же металлу и обесценивало металлургию GregTech. Но полностью
// лишать раннюю игру механической переработки не планировалось — планировалось
// развести два маршрута по роли.
//
// Здесь Create получает роль моста до электричества: дробильные колёса дают
// концентрат GregTech строго один к одному, без умножения и без побочных
// продуктов. Точная переработка GregTech остаётся выгоднее — она и умножает,
// и возвращает побочные минералы. Механический маршрут не обгоняет её никогда,
// он лишь позволяет начать до появления энергии.
//
// Все ID взяты из живой переписи реестра kubejs/exported/gtceu_item_census.json
// (8844 предмета GregTech), а не из предположений о схеме именования.
ServerEvents.recipes((event) => {
  // Железо, медь и золото GregTech берёт из ванильного сырья: собственных
  // gtceu:raw_* для них в реестре нет.
  const vanillaRaw = [
    ['minecraft:raw_iron', 'gtceu:crushed_iron_ore'],
    ['minecraft:raw_copper', 'gtceu:crushed_copper_ore'],
    ['minecraft:raw_gold', 'gtceu:crushed_gold_ore']
  ]

  // Остальные ранние металлы и рудные минералы имеют собственное сырьё GregTech.
  const gregtechRaw = [
    'tin', 'lead', 'silver', 'nickel',
    'chalcopyrite', 'tetrahedrite', 'sphalerite', 'galena', 'magnetite', 'cassiterite'
  ]

  let registered = 0

  vanillaRaw.forEach(([input, output]) => {
    event.recipes.create
      .crushing([Item.of(output)], input)
      .id(`industrial_frontier:create/crush_${output.substring('gtceu:crushed_'.length)}`)
    registered++
  })

  gregtechRaw.forEach((material) => {
    event.recipes.create
      .crushing([Item.of(`gtceu:crushed_${material}_ore`)], `gtceu:raw_${material}`)
      .id(`industrial_frontier:create/crush_${material}_ore`)
    registered++
  })

  console.info(`[Recast] Механический маршрут обогащения: ${registered} рецептов, соотношение 1:1 без побочных продуктов.`)
})
