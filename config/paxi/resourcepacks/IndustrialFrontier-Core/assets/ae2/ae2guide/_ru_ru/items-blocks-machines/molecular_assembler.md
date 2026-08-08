---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Молекулярный сборщик
  icon: molecular_assembler
  position: 310
categories:
- machines
item_ids:
- ae2:molecular_assembler
---

# Молекулярный сборщик

<BlockImage id="molecular_assembler" scale="8" />

Молекулярный сборщик принимает предметы и выполняет операцию, заданную соседним <ItemLink id="pattern_provider" />
либо вставленным <ItemLink id="crafting_pattern" />, <ItemLink id="smithing_table_pattern" /> или
<ItemLink id="stonecutting_pattern" />. Готовый результат он выталкивает в соседние хранилища.

В этом примере в сборщик установлен шаблон рецепта «1 дубовое бревно = 4 дубовые доски». Верхняя воронка подаёт
брёвна, сборщик изготавливает доски и выбрасывает их в нижнюю воронку.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/standalone_assembler.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Основное применение молекулярного сборщика

Чаще всего сборщик размещают рядом с <ItemLink id="pattern_provider" />. В такой связке поставщик передаёт соседнему
сборщику ингредиенты и сведения о нужном шаблоне. Сборщик автоматически выталкивает результат в соседнее хранилище,
то есть в возвратные слоты поставщика. Поэтому для автоматизации шаблонов изготовления достаточно одного сборщика,
примыкающего к поставщику шаблонов.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/assembler_tower.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Улучшения

Молекулярный сборщик поддерживает следующее [улучшение](upgrade_cards.md):

*   <ItemLink id="speed_card" />

## Рецепт

<RecipeFor id="molecular_assembler" />

## Примечание

OptiFine нарушает функцию выталкивания в соседние хранилища, поэтому большинство производственных схем с молекулярными сборщиками работать не будет.
