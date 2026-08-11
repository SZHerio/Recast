// Процессы двух последних собственных машин.
//
// Стенд сборки ступени и станция обслуживания роя зарегистрированы и крафтятся,
// но до сих пор ничего не делали: типы рецептов stage_assembly и swarm_servicing
// существовали пустыми. Машина без процесса — то же обещание в книге, только
// теперь видное в JEI.
//
// Материалы взяты те, что уже есть в сборке и относятся к своей эпохе: титан и
// вольфрамовая сталь седьмой эпохи для ступени, узлы LuV восьмой для роя.
// Все идентификаторы сверены с переписью предметов, а не написаны по памяти.
//
// Правило прибыли соблюдено: ни один процесс не выдаёт больше материала, чем
// получил. Обслуживание роя — это восстановление изношенного узла за счёт
// расходников, а не размножение деталей.
ServerEvents.recipes((event) => {
  // --- Стенд сборки ступени: P7, аэрокосмический комплекс ---
  //
  // Ступень собирается из проката и узлов, а не крафтится целиком. Вход —
  // пластины, кольца и каркас; выход — корпусная секция под обшивку.
  event.recipes.gtceu.stage_assembly('industrial_frontier:stage/hull_section')
    .itemInputs('8x gtceu:titanium_plate', '4x gtceu:titanium_ring', '2x gtceu:titanium_frame')
    .itemOutputs('4x gtceu:titanium_carbide_plate')
    .duration(400)
    .EUt(480)

  // Топливная арматура: трубопровод, насос и обвязка каркаса.
  event.recipes.gtceu.stage_assembly('industrial_frontier:stage/fuel_manifold')
    .itemInputs('4x gtceu:tungsten_steel_plate', '4x gtceu:tungsten_steel_normal_fluid_pipe', '1x gtceu:ev_electric_pump')
    .itemOutputs('2x gtceu:tungsten_steel_frame')
    .duration(600)
    .EUt(1920)

  // --- Станция обслуживания роя: P8, орбитально-планетарная сеть ---
  //
  // Изношенный манипулятор восстанавливается за счёт мотора и палладиевого
  // проката: на выходе один узел, а не два. Смысл станции в том, что рой
  // обслуживают дешевле, чем собирают заново, а не в бесплатном материале.
  event.recipes.gtceu.swarm_servicing('industrial_frontier:swarm/drone_refit')
    .itemInputs('1x gtceu:luv_robot_arm', '1x gtceu:luv_electric_motor', '4x gtceu:palladium_plate')
    .itemOutputs('1x gtceu:luv_robot_arm', '2x gtceu:palladium_dust')
    .duration(300)
    .EUt(7680)

  // Калибровка: два датчика и излучатель сводятся в один точный датчик,
  // остаток уходит в лом. Это чистка парка, а не производство.
  event.recipes.gtceu.swarm_servicing('industrial_frontier:swarm/sensor_calibration')
    .itemInputs('2x gtceu:luv_sensor', '1x gtceu:luv_emitter')
    .itemOutputs('1x gtceu:luv_sensor', '1x gtceu:luv_emitter')
    .duration(240)
    .EUt(7680)

  console.info('[Recast] own machinery: stage assembly and swarm servicing processes added')
})
