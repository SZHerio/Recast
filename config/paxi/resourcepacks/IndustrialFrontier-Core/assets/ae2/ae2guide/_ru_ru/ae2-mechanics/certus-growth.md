---
navigation:
  parent: ae2-mechanics/ae2-mechanics-index.md
  title: Рост истинного кварца
  icon: quartz_cluster
---

# Рост истинного кварца

## Краткое повторение раздела «Начало работы»

<GameScene zoom="6" background="transparent">
<ImportStructure src="../assets/assemblies/budding_certus_1.snbt" />
</GameScene>

На [цветущих блоках истинного кварца](../items-blocks-machines/budding_certus.md), как на блоках аметиста, появляются
почки истинного кварца. Из не успевшей вырасти почки выпадает одна <ItemLink id="certus_quartz_dust" />; «Удача» не
изменяет это количество. Полностью выросшая друза даёт четыре кристалла: <ItemLink id="certus_quartz_crystal" />.
«Удача» увеличивает их число.

Цветущие блоки истинного кварца имеют четыре уровня: безупречный, потресканный, сколотый и повреждённый.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/budding_blocks.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Каждый раз, когда почка переходит на следующую стадию роста, цветущий блок может ухудшиться на один уровень и в конце
концов стать обычным блоком истинного кварца. Повреждённый цветущий блок можно восстановить, а обычный блок — превратить
в цветущий, если бросить его в воду вместе с одним или несколькими предметами
<ItemLink id="charged_certus_quartz_crystal" />.

<RecipeFor id="damaged_budding_quartz" />

Безупречные цветущие блоки истинного кварца не ухудшаются и позволяют получать истинный кварц бесконечно. Однако их
нельзя изготовить или перенести киркой даже с «Шёлковым касанием». Переместить их всё же можно с помощью
[пространственного хранилища](../ae2-mechanics/spatial-io.md).

Сами по себе почки истинного кварца растут очень медленно. <ItemLink id="growth_accelerator" />, установленный рядом с
цветущим блоком, значительно ускоряет этот процесс. Несколько таких ускорителей должны стать вашей первой целью.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/budding_certus_2.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Если кварца пока недостаточно для двух электрических источников — <ItemLink id="energy_acceptor" /> или
<ItemLink id="vibration_chamber" />, — изготовьте <ItemLink id="crank" /> и установите рукоять на торец ускорителя.

Автоматический сбор истинного кварца [описан здесь](../example-setups/simple-certus-farm.md).
