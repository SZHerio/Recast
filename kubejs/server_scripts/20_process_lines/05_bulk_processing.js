// Массовая переработка P5.
//
// К пятой эпохе переработка руды перестаёт быть ручной и становится линией.
// Владелец этой линии один — GregTech: только он умножает выход, возвращает
// побочные минералы и различает классы чистоты. Всё остальное либо подвозит
// сырьё, либо потребляет продукт.
//
// Проверка установленных модов показала второго владельца. Immersive
// Engineering поставляет 67 рецептов, которые берут forge:ores/* и
// forge:raw_materials/* и выдают удвоенный металл: 37 в дробилке и 30 в
// дуговой печи. Это полноценная параллельная экономика обогащения.
//
// По документу домена IE — «видимая тяжёлая гражданская промышленность»
// и прямо «не ступень к GTCEu» (GLOBAL_TECH_CITY_CURSEFORGE_AUDIT §3.1).
// Поэтому удаляется ровно рудная ветка, а не мод: дуговая печь сохраняет
// переплавку лома и сплавы, остаются металлопресс, лесопилка, теплица,
// экскаватор, провода, конвейеры и вся тяжёлая архитектура.
//
// Механический мост уже существует и не дублируется: с M3 дробильные колёса
// Create дают концентрат GregTech строго один к одному, без умножения.
// Второй такой же мост в IE не добавил бы ни одного нового решения.
ServerEvents.recipes((event) => {
  const materials = [
    'aluminum', 'ardite', 'cobalt', 'copper', 'gold', 'iron', 'lead', 'nickel',
    'osmium', 'platinum', 'silver', 'tin', 'tungsten', 'uranium', 'zinc'
  ]
  // Дробилка обрабатывает ещё и неметаллические жилы, у которых нет варианта raw.
  const crusherOnly = ['coal', 'diamond', 'emerald', 'fluorite', 'lapis', 'quartz', 'redstone']

  let removed = 0
  const drop = (recipeId) => {
    event.remove({ id: recipeId })
    removed++
  }

  materials.forEach((material) => {
    drop(`immersiveengineering:crusher/ore_${material}`)
    drop(`immersiveengineering:crusher/raw_ore_${material}`)
    drop(`immersiveengineering:arcfurnace/ore_${material}`)
    drop(`immersiveengineering:arcfurnace/raw_ore_${material}`)
  })
  crusherOnly.forEach((material) => drop(`immersiveengineering:crusher/ore_${material}`))

  // Доменная печь Immersive Engineering. Решение откладывалось до переписи
  // тегов, потому что статически вопрос не решался: доменная печь превращает
  // forge:ingots/iron в forge:ingots/steel, и всё зависело от того, что в этом
  // теге лежит. GregTech не поставляет ни одного статического файла forge-тегов.
  //
  // Перепись от 3 августа 2026 дала ответ:
  // forge:ingots/steel = ad_astra, createbigcannons, gtceu, hbm_m,
  //                      immersiveengineering, magistuarmory, nuclearcraft.
  //
  // Тег общий, то есть сталь IE и сталь GregTech — один и тот же материал для
  // любого рецепта сборки. Значит доменная печь не «ещё одна машина на общем
  // сырье», а второй производственный маршрут той же стали, причём в обход
  // всей металлургии P2, которой посвящена глава. Это ровно тот случай, что
  // уже закрывался трижды в M3.
  //
  // Обратная сторона того же факта делает удаление безопасным: машинам IE
  // сталь по-прежнему доступна — они принимают её тегом, а в теге есть
  // gtceu:steel_ingot. Мод теряет дублирующий рецепт, а не работоспособность.
  drop('immersiveengineering:blastfurnace/steel')
  drop('immersiveengineering:blastfurnace/steel_block')

  console.info(
    `[Recast] Массовая переработка P5: удалено ${removed} дублирующих маршрутов Immersive Engineering (65 рудных, 2 стальных). Умножение руды и выплавка стали остаются у GregTech, механический мост 1:1 — у Create.`
  )
})
