// P2 «Сборка»: мебель, знаки, столярка и каменная отделка собираются машиной.
//
// Решение владельца от 9 августа 2026 года. Линия и правила —
// docs/registries/recipe_devolution.json.
//
// Волна закрывает ту часть группы «прочее», у которой владелец уже стоит и
// проверен: механический сборщик и пила. Металл, электрика, кабели, машины,
// оружие и броня сюда НЕ входят — это территория GregTech, чьи рецепты
// порождаются в коде и статически не видны. Их очередь наступит после выгрузки
// реестра из запущенной игры.
//
// Список не выписывается вручную: источником истины служат сами рецепты сборки.
ServerEvents.recipes((event) => {
  // Что берём: предмет обихода, столярка, отделка.
  const TAKE = /(chair|table|bench|sofa|desk|shelf|drawer|cabinet|counter|stool|wardrobe|cushion|curtain|rug|carpet|door|window|shutter|trapdoor|roof|bridge|railing|ladder|sign|banner|flag|painting|vase|pot$|tile|panel|beam|pillar|column|paving|mosaic)/
  // Чего не трогаем: чужие домены, эпохальные ворота и первый час.
  const SKIP_ITEM = /(gun|rifle|pistol|ammo|bullet|shell|cannon|grenade|magazine|helmet|chestplate|leggings|boots|armor|suit|circuit|board|module|core|cable|wire|machine|casing|controller|reactor|turbine|generator|rocket|fuel)/
  const SKIP_NS = ['gtceu', 'gtnn', 'ae2', 'hbm_ntm_rebirth', 'nuclearcraft', 'tacz', 'createbigcannons', 'magistuarmory', 'lightmanscurrency']
  // Металл во входах означает домен GregTech: такие сборки ждут выгрузки.
  const METAL = /(ingot|nugget|plate|rod|wire|steel|circuit)/

  let handed = 0
  event.forEachRecipe({ type: 'minecraft:crafting_shaped' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result || !result.isJsonObject()) return
    const output = result.getAsJsonObject().get('item').getAsString()
    const parts = output.split(':')
    if (SKIP_NS.indexOf(parts[0]) >= 0) return
    if (!TAKE.test(parts[1]) || SKIP_ITEM.test(parts[1])) return
    if (!json.has('pattern') || !json.has('key')) return

    const pattern = []
    json.get('pattern').getAsJsonArray().forEach((row) => pattern.push(row.getAsString()))
    const key = {}
    const rawKey = json.get('key').getAsJsonObject()
    let metal = false
    rawKey.keySet().forEach((symbol) => {
      const value = rawKey.get(symbol)
      if (METAL.test(value.toString())) metal = true
      key[symbol] = Ingredient.of(value)
    })
    if (metal) return

    const count = result.getAsJsonObject().has('count')
      ? result.getAsJsonObject().get('count').getAsInt() : 1

    event.recipes.create.mechanical_crafting(Item.of(output, count), pattern, key)
    event.remove({ type: 'minecraft:crafting_shaped', output: output })
    handed += 1
  })

  console.info(`[Recast] сборка: механическому сборщику передано ${handed} изделий`)
})
