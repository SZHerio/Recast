// Горелка всполоха разжигается огнём, а не пойманным ифритом.
//
// В стоковом Create горелку нельзя получить, не сходив в Нижний мир и не поймав
// там ифрита в пустую горелку. Для фабричной сборки это тупик: на чаше под
// горелкой держатся уплотнение блоков, приготовление смесей и окраска —
// операции первой и второй эпохи. Требовать ради них Нижний мир значит
// перевернуть прогрессию с ног на голову.
//
// Ифрит при этом ничего не даёт механически: разожжённая горелка всё равно
// работает на обычном твёрдом топливе. Он был только ключом.
//
// Поэтому добавляется второй способ: пустая горелка плюс ведро лавы. Ведро
// возвращается игроку, как и в любом ванильном рецепте с жидкостью. Прежний
// способ с ифритом не снимается — тот, кто уже в Нижнем мире, воспользуется им.
ServerEvents.recipes((event) => {
  // Стоковые рецепты снимаются: у операции один владелец, а два пути к одному
  // предмету — тот самый обход, который сборка убирает у чужих модов.
  event.remove({ type: 'minecraft:crafting_shaped', output: 'create:empty_blaze_burner' })
  event.remove({ type: 'minecraft:crafting_shapeless', output: 'create:empty_blaze_burner' })

  event.shapeless('create:blaze_burner', [
    'create:empty_blaze_burner',
    'minecraft:lava_bucket'
  ]).id('industrial_frontier:create/blaze_burner_from_lava')

  // Пустая горелка из обычных материалов. Стоковый рецепт требует адского
  // камня, и это сводит на нет разжигание лавой: за камнем всё равно пришлось
  // бы идти в Нижний мир. Топка из обожжённого кирпича в железной обвязке —
  // то же самое по смыслу и доступно с первой эпохи.
  event.shaped('create:empty_blaze_burner', [
    'NNN',
    'NBN',
    'NNN'
  ], {
    N: 'minecraft:iron_nugget',
    B: 'minecraft:bricks'
  }).id('industrial_frontier:create/empty_blaze_burner_from_bricks')

  console.info('[Recast] blaze burner: lava ignition and brick firebox added, no nether trip required')
})
