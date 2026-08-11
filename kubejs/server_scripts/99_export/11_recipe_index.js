// Выгрузка рецептов сборки.
//
// GregTech и часть других модов не поставляют рецепты файлами: они рождаются в
// коде и видны только в запущенной игре. Файл появляется при загрузке мира и
// при /reload: kubejs/exported/recipe_index.json
//
// Скрипт намеренно предельно простой: ни рекурсии, ни вложенных функций, ни
// блочных объявлений. Rhino поднимает объявления к началу функции, и три
// предыдущие попытки разобрать структуру рецепта прямо здесь падали именно на
// этом. Разбор делается вне игры, здесь только сбор текста.
ServerEvents.recipes((event) => {
  let rows = []
  let total = 0

  event.forEachRecipe({}, (recipe) => {
    total = total + 1
    rows.push(recipe.getId().toString() + '' + recipe.json.toString())
  })

  JsonIO.write('kubejs/exported/recipe_index.json', {
    generated_by: 'industrial_frontier:recipe_index',
    note: 'Каждая строка: идентификатор рецепта, сразу за ним полный JSON. Разделять по первой открывающей фигурной скобке — в идентификаторе её быть не может.',
    recipe_count: total,
    rows: rows
  })

  console.info('[Recast] указатель рецептов выгружен: ' + total + ' записей')
})
