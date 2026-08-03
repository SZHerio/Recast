Ponder.tags((event) => {
  event.createTag(
    'industrial_frontier:factory_foundations',
    'create:basin',
    'Основы фабрики',
    'Поток, партии, буферы и поиск узких мест',
    ['create:basin', 'create:mechanical_mixer']
  )
})

Ponder.registry((event) => {
  event
    .create('create:basin')
    .scene(
      'industrial_frontier:batch_processing_basics',
      'Партия, буфер и узкое место',
      (scene) => {
        scene.showBasePlate()
        scene.world.setBlock([2, 1, 2], 'create:basin', false)
        scene.world.setBlock([2, 3, 2], 'create:mechanical_mixer', false)
        scene.world.setBlock([3, 3, 2], 'create:cogwheel', false)
        scene.world.setBlock([4, 3, 2], 'create:shaft', false)
        scene.world.setBlock([1, 1, 2], 'minecraft:chest', false)
        scene.world.setBlock([3, 1, 2], 'minecraft:chest', false)
        scene.showStructure()
        scene.idle(20)

        scene
          .text(80, 'Левый сундук — входной буфер. Он отделяет снабжение от скорости машины.', [1.5, 1.5, 2.5])
          .colored(PonderPalette.INPUT)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(90)

        scene
          .text(90, 'Чаша обрабатывает партию. Смеситель должен получать стабильное вращение без перегрузки сети.', [2.5, 2.2, 2.5])
          .colored(PonderPalette.MEDIUM)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .text(90, 'Правый сундук — выходной буфер. Если он переполнен, остановится вся линия: это узкое место.', [3.5, 1.5, 2.5])
          .colored(PonderPalette.OUTPUT)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .showControls(70, [2.5, 1.8, 2.5], 'down')
          .withItem('minecraft:clay_ball')
        scene.idle(80)

        scene
          .text(100, 'Настраивайте не одну машину, а весь поток: подачу, обработку, отвод и запас на сбой.', [2.5, 3.5, 2.5])
          .colored(PonderPalette.FAST)
          .placeNearTarget()
          .attachKeyFrame()
      }
    )
})
