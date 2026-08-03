// P1 lesson that plain text explains badly: stress is a budget shared by the
// whole rotation network, so an overload stops every machine at once - not the
// one you just connected. The fix taught here is splitting the network, because
// independent circuits fail and get repaired separately.
Ponder.registry((event) => {
  event
    .create('create:stressometer')
    .scene(
      'industrial_frontier:mechanical_stress_budget',
      'Стресс: почему встала вся линия',
      (scene) => {
        scene.showBasePlate()
        scene.world.setBlock([1, 1, 2], 'create:water_wheel', false)
        scene.world.setBlock([2, 1, 2], 'create:shaft', false)
        scene.world.setBlock([3, 1, 2], 'create:cogwheel', false)
        scene.world.setBlock([4, 1, 2], 'create:shaft', false)
        scene.world.setBlock([3, 2, 2], 'create:stressometer', false)
        scene.world.setBlock([3, 1, 1], 'create:millstone', false)
        scene.world.setBlock([3, 1, 3], 'create:mechanical_press', false)
        scene.showStructure()
        scene.idle(20)

        scene
          .text(90, 'Водяное колесо — источник. Оно даёт не только скорость, но и ограниченный запас усилия.', [1.5, 1.8, 2.5])
          .colored(PonderPalette.INPUT)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .text(90, 'Каждая подключённая машина забирает часть этого запаса. Запас общий на всю сеть.', [3.5, 1.5, 2.5])
          .colored(PonderPalette.MEDIUM)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .text(100, 'Когда потребление превысит запас, остановится вся сеть целиком, а не последняя добавленная машина.', [3.5, 2.5, 2.5])
          .colored(PonderPalette.RED)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(110)

        scene
          .showControls(70, [3.5, 2.5, 2.5], 'down')
          .withItem('create:stressometer')
        scene.idle(80)

        scene
          .text(100, 'Стрессометр показывает остаток. Смотрите на него до подключения новой машины, а не после остановки.', [3.5, 2.8, 2.5])
          .colored(PonderPalette.OUTPUT)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(110)

        scene
          .text(110, 'Решений два: добавить источник или разделить сеть. Второе надёжнее — независимые контуры чинятся по отдельности.', [2.5, 3.5, 2.5])
          .colored(PonderPalette.FAST)
          .placeNearTarget()
          .attachKeyFrame()
      }
    )
})
