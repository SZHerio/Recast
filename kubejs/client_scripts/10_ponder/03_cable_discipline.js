// P3 lesson that text explains badly. Voltage, current and loss are three
// separate quantities, and the mistake that burns cables is confusing the first
// with the third. The scene shows the shape of a correct run: short and thick
// from the source to a node, thin from the node to the machines.
Ponder.registry((event) => {
  event
    .create('minecraft:redstone')
    .scene(
      'industrial_frontier:cable_discipline',
      'Кабель: напряжение, ток и потери',
      (scene) => {
        scene.showBasePlate()
        scene.world.setBlock([1, 1, 2], 'minecraft:furnace', false)
        scene.world.setBlock([2, 1, 2], 'minecraft:copper_block', false)
        scene.world.setBlock([3, 1, 2], 'minecraft:iron_block', false)
        scene.world.setBlock([4, 1, 2], 'minecraft:copper_block', false)
        scene.world.setBlock([4, 1, 1], 'create:andesite_casing', false)
        scene.world.setBlock([4, 1, 3], 'create:andesite_casing', false)
        scene.showStructure()
        scene.idle(20)

        scene
          .text(90, 'Слева источник. У него есть класс напряжения — это не «сила тока», а тип оборудования.', [1.5, 1.5, 2.5])
          .colored(PonderPalette.INPUT)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .text(100, 'Подача напряжения выше класса приёмника сжигает его. Машина не начнёт работать быстрее — она перестанет существовать.', [2.5, 2.2, 2.5])
          .colored(PonderPalette.RED)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(110)

        scene
          .text(90, 'Ток — это сколько потребителей тянут одновременно. Кабель рассчитан на своё число, а не на «сколько поместится».', [3.0, 1.5, 2.5])
          .colored(PonderPalette.MEDIUM)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(100)

        scene
          .text(100, 'Потери зависят от длины. Поэтому линия строится так: коротко и толсто до узла, тонко от узла до машин.', [4.0, 1.8, 2.5])
          .colored(PonderPalette.OUTPUT)
          .placeNearTarget()
          .attachKeyFrame()
        scene.idle(110)

        scene
          .text(110, 'Одна длинная линия «до всего сразу» — самая частая ранняя ошибка. Узел стоит дешевле, чем перегоревший кабель.', [2.5, 3.5, 2.5])
          .colored(PonderPalette.FAST)
          .placeNearTarget()
          .attachKeyFrame()
      }
    )
})
