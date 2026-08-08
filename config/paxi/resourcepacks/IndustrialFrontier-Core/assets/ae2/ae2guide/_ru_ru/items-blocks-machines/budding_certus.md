---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Цветущий истинный кварц
  icon: flawless_budding_quartz
  position: 010
categories:
- misc ingredients blocks
item_ids:
- ae2:flawless_budding_quartz
- ae2:flawed_budding_quartz
- ae2:chipped_budding_quartz
- ae2:damaged_budding_quartz
- ae2:small_quartz_bud
- ae2:medium_quartz_bud
- ae2:large_quartz_bud
- ae2:quartz_cluster
---

# Цветущий истинный кварц

(См. также раздел [«Рост истинного кварца»](../ae2-mechanics/certus-growth.md).)

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/budding_blocks.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

На цветущих блоках истинного кварца, как на аметисте, появляются почки истинного кварца. Эти блоки встречаются в
[метеоритах](../ae2-mechanics/meteorites.md). Существует 4 уровня цветущих блоков: безупречный, потресканный,
сколотый и повреждённый. Проще всего различать их с помощью HWYLA, Jade, The One Probe или похожего мода, а также на
экране F3.

Когда почка на потресканном, сколотом или повреждённом цветущем блоке переходит на следующую стадию роста, блок может
ухудшиться на 1 уровень. В конце концов он превращается в обычный <ItemLink id="quartz_block" />.

Безупречный цветущий блок не ухудшается при росте почек и служит бесконечным источником истинного кварца.

Если сломать цветущий блок обычной киркой, он ухудшится на один уровень. Кирка с «Шёлковым касанием» сохраняет текущий
уровень блока, но это правило не действует на безупречный вариант. **Это означает, что безупречный цветущий блок истинного
кварца нельзя подобрать и перенести киркой.** Вместо этого его можно переместить с помощью
[пространственного хранилища](../ae2-mechanics/spatial-io.md), буквально вырезав в одном месте и вставив в другом.

## Рецепты

Потресканный, сколотый и повреждённый цветущие блоки можно изготовить: бросьте предыдущий уровень цветущего блока или
<ItemLink id="quartz_block" /> в воду вместе с одним или несколькими предметами
<ItemLink id="charged_certus_quartz_crystal" />.

Безупречный цветущий блок нельзя изготовить — его можно только найти в мире.

<Row>
  <RecipeFor id="damaged_budding_quartz" />

  <RecipeFor id="chipped_budding_quartz" />

  <RecipeFor id="flawed_budding_quartz" />
</Row>
