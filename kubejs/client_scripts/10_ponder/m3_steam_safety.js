// P2 lesson that text explains badly. A boiler has three conditions and breaking
// any one of them ends the same way, so the scene shows the shape of the loop
// rather than listing rules: water in, fuel under, steam out, and an outlet that
// is never allowed to close.
Ponder.registry((event) => {
  event
    .create('minecraft:bucket')
    .scene(
      'industrial_frontier:steam_boiler_safety',
      'Котёл: три условия и одна ошибка',
      (scene) => {
        scene.showBasePlate()
        scene.world.setBlock([2, 1, 2], 'minecraft:furnace', false)
        scene.world.setBlock([2, 2, 2], 'create:fluid_tank', false)
        scene.world.setBlock([1, 1, 2], 'minecraft:water_cauldron', false)
        scene.world.setBlock([3, 1, 2], 'create:fluid_pipe', false)
        scene.world.setBlock([4, 1, 2], 'create:fluid_tank', false)
        scene.showStructure()
        scene.idle(20)

        scene
          .text(90, 'Слева подача воды. Она должна быть непрерывной, а не «я подолью, когда замечу».', [1.5, 1.5, 2.5])
          .colored(PonderPalette.INPUT)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .text(90, 'Снизу топливо. Без него котёл просто остынет — это единственная безопасная из трёх неудач.', [2.5, 1.2, 2.5])
          .colored(PonderPalette.MEDIUM)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .text(100, 'Справа выход пара. Он обязан оставаться открытым: закрытый выход и сухой котёл заканчиваются одинаково — разрушением.', [3.5, 1.5, 2.5])
          .colored(PonderPalette.RED)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(110)

        scene
          .showControls(70, [1.5, 1.8, 2.5], 'down')
          .withItem('minecraft:water_bucket')
        scene.idle(80)

        scene
          .text(110, 'Правило, которое стоит принять сразу: подачу воды делают автоматической до первого запуска, а не после первой аварии.', [2.5, 3.0, 2.5])
          .colored(PonderPalette.OUTPUT)
          .placeNearTarget()
          .attachKeyFrame()
      }
    )
})
