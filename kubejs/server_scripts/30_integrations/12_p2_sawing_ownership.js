// P2 «Распил и формовка»: плиты, ступени, стены и заборы режет пила.
//
// Решение владельца от 9 августа 2026 года: ручной рецепт снимается полностью.
// Линия — docs/registries/recipe_devolution.json.
//
// Группа насчитывает сотни позиций, поэтому список не выписывается вручную:
// источником истины служат уже существующие рецепты камнереза. Для каждого из
// них создаётся такой же рецепт механической пилы, и только после этого
// снимается ручная выкладка того же результата на верстаке.
//
// Так ни один предмет не может выпасть из игры: пила получает ровно то, что
// раньше умел камнерез, а верстак теряет только дубль.
ServerEvents.recipes((event) => {
  let handed = 0
  let dropped = 0

  event.forEachRecipe({ type: 'minecraft:stonecutting' }, (recipe) => {
    const json = recipe.json
    const result = json.get('result')
    if (!result) return
    const output = result.isJsonObject() ? result.getAsJsonObject().get('item').getAsString() : result.getAsString()
    const count = json.has('count') ? json.get('count').getAsInt() : 1
    const ingredient = json.get('ingredient')
    if (!ingredient || !output) return

    // Пила выполняет ту же операцию, что и камнерез.
    event.recipes.create.cutting(Item.of(output, count), Ingredient.of(ingredient))
    handed += 1
  })

  // Верстак теряет дубли распила: результат уже принадлежит пиле.
  ;['#minecraft:slabs', '#minecraft:stairs', '#minecraft:walls', '#minecraft:fences'].forEach((tag) => {
    Ingredient.of(tag).itemIds.forEach((id) => {
      event.remove({ type: 'minecraft:crafting_shaped', output: id })
      dropped += 1
    })
  })

  console.info(`[Recast] распил: пиле передано ${handed} операций, у верстака снято ${dropped} результатов`)
})
