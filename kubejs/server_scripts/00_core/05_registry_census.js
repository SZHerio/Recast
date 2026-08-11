// GregTech registers its items at runtime, so their exact IDs cannot be proven
// from the jar and must never be guessed. This script does not guess: it reads
// the live registry when the world loads and writes down what is actually there.
//
// One launch produces the census, and the curated ore route plus the P4 acid
// lines can then be written against real IDs. It changes no recipe, removes
// nothing and adds no content.
//
// Наименования API у KubeJS несимметричны, и это уже стоило одного пустого
// запуска: у предметов метод называется Item.getTypeList(), а у жидкостей —
// Fluid.getTypes(). Прежняя версия звала Fluid.getTypeList(), падала на этой
// строке и уносила с собой всю перепись — файл не записывался вообще.
//
// Оба имени сверены с JAR kubejs-forge-2001.6.5-build.26:
// dev/latvian/mods/kubejs/bindings/ItemWrapper -> getTypeList
// dev/latvian/mods/kubejs/fluid/FluidWrapper   -> getTypes
// dev/latvian/mods/kubejs/core/IngredientKJS   -> getItemIds
//
// Отсюда второе правило этого файла: каждый раздел собирается отдельно и под
// своей защитой. Сбой одного раздела уменьшает перепись, но не отменяет её.
// Rhino в KubeJS не терпит одноимённых const внутри нескольких стрелочных
// функций одного файла: первый же вызов падает с «redeclaration of var».
// Это стоило второго пустого запуска, поэтому сбор идентификаторов вынесен
// в одну функцию и больше нигде не повторяется.
function ifSortedIds(source) {
  const collected = []
  source.forEach((id) => collected.push(String(id)))
  collected.sort()
  return collected
}

ServerEvents.highPriorityData((event) => {
  const problems = []
  const buckets = ['crushed', 'purified', 'refined', 'dust', 'ingot', 'plate', 'raw', 'nugget', 'gem', 'rod', 'wire']
  const groups = {}
  let total = 0

  try {
    Item.getTypeList().forEach((id) => {
      const itemId = String(id)
      if (!itemId.startsWith('gtceu:')) return
      total++
      const short = itemId.substring('gtceu:'.length)
      const bucket = buckets.find((name) => short.startsWith(name + '_') || short.includes('_' + name))
      const key = bucket || 'other'
      if (!groups[key]) groups[key] = []
      groups[key].push(itemId)
    })
    Object.keys(groups).forEach((key) => groups[key].sort())
  } catch (error) {
    problems.push('items: ' + error)
  }

  // Жидкости регистрируются так же динамически, как предметы, и их ID тоже
  // нельзя доказать по JAR: в lang-файле GregTech всего пять ключей fluid.*,
  // а названия кислот и газов собираются в рантайме.
  const fluids = []
  try {
    Fluid.getTypes().forEach((id) => {
      const fluidId = String(id)
      if (fluidId.startsWith('gtceu:')) fluids.push(fluidId)
    })
    fluids.sort()
  } catch (error) {
    problems.push('fluids: ' + error)
  }

  // Теги — третий класс фактов, который нельзя доказать по JAR: GregTech не
  // поставляет ни одного статического файла forge-тегов, он собирает их в
  // рантайме. Из-за этого нельзя было ответить на простой вопрос: входит ли
  // сталь GregTech в forge:ingots/steel, то есть является ли доменная печь
  // Immersive Engineering вторым владельцем стали или просто ещё одной машиной,
  // работающей на общем материале.
  //
  // Ingredient.getItemIds подтверждён в kubejs-forge-2001.6.5-build.26
  // (dev/latvian/mods/kubejs/core/IngredientKJS).
  const auditedTags = [
    'forge:ingots/steel', 'forge:plates/steel', 'forge:ingots/aluminium', 'forge:ingots/aluminum',
    'forge:ores/iron', 'forge:raw_materials/iron', 'forge:dusts/iron',
    'forge:gems/certus_quartz', 'forge:gems/fluix', 'forge:storage_blocks/steel',
    'forge:rods/steel', 'forge:gears/steel', 'forge:plates/aluminium'
  ]
  const tags = {}
  auditedTags.forEach((tag) => {
    try {
      tags[tag] = ifSortedIds(Ingredient.of('#' + tag).getItemIds())
    } catch (error) {
      tags[tag] = ['<не удалось прочитать: ' + error + '>']
      problems.push('tag ' + tag + ': ' + error)
    }
  })

  // Авторские теги проверяются здесь же. Повод конкретный: в палитре P0 холст
  // Farmer's Delight стоял как блок, хотя это предмет, и из-за одной строки
  // не грузилась вся палитра. Статически такую ошибку не поймать — форма записи
  // правильная, ошибочна принадлежность к реестру. Пустой список ниже означает,
  // что тег не загрузился, и это видно сразу, а не через месяц стройки.
  //
  // Block.getTaggedIds подтверждён в kubejs-forge-2001.6.5-build.26
  // (dev/latvian/mods/kubejs/bindings/BlockWrapper).
  const packItemTags = [
    'industrial_frontier:storage/long_term_reserve',
    'industrial_frontier:storage/field_kit',
    'industrial_frontier:storage/returnable_food_container',
    'industrial_frontier:furniture/city_set',
    'industrial_frontier:rations/field',
    'industrial_frontier:rations/worker',
    'industrial_frontier:rations/city',
    'industrial_frontier:rations/preserved'
  ]
  const packBlockTags = [
    'industrial_frontier:palette/p0',
    'industrial_frontier:palette/p1',
    'industrial_frontier:palette/p2',
    'industrial_frontier:palette/p3',
    'industrial_frontier:palette/p4',
    'industrial_frontier:palette/p5'
  ]
  const packTags = {}
  packItemTags.forEach((tag) => {
    try {
      packTags[tag] = ifSortedIds(Ingredient.of('#' + tag).getItemIds())
      if (packTags[tag].length === 0) problems.push('пустой тег предметов ' + tag)
    } catch (error) {
      packTags[tag] = []
      problems.push('tag ' + tag + ': ' + error)
    }
  })
  packBlockTags.forEach((tag) => {
    try {
      packTags[tag] = ifSortedIds(Block.getTaggedIds(tag))
      if (packTags[tag].length === 0) problems.push('пустой тег блоков ' + tag)
    } catch (error) {
      packTags[tag] = []
      problems.push('tag ' + tag + ': ' + error)
    }
  })

  // JsonIO.write does not create the parent folder and throws
  // NoSuchFileException when it is missing, so kubejs/exported/ is shipped with
  // the pack. A failed write must not take the rest of the reload down with it.
  try {
    JsonIO.write('kubejs/exported/gtceu_item_census.json', {
      generated_by: 'industrial_frontier:registry_census',
      gtceu_item_count: total,
      group_count: Object.keys(groups).length,
      gtceu_fluid_count: fluids.length,
      audited_tag_count: Object.keys(tags).length,
      pack_tag_count: Object.keys(packTags).length,
      problems: problems,
      groups: groups,
      fluids: fluids,
      tags: tags,
      pack_tags: packTags
    })
    console.info(`[Recast] Перепись: ${total} предметов GTCEu, ${fluids.length} жидкостей, ${Object.keys(tags).length} чужих тегов, ${Object.keys(packTags).length} авторских тегов. Проблем: ${problems.length}`)
    problems.forEach((problem) => console.warn(`[Recast] Перепись — проблема: ${problem}`))
  } catch (error) {
    console.error(`[Recast] GTCEu census could not be written (${error}). Found ${total} items; check that kubejs/exported/ exists.`)
  }
})
