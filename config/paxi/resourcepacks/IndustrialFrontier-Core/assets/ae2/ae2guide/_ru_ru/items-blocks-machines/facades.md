---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Кабельные фасады
  icon: facade
  icon_nbt: '{item: "minecraft:stone"}'
  position: 110
categories:
- network infrastructure
item_ids:
- ae2:facade
---

# Кабельные фасады

Фасады помогают аккуратно вписать МЭ-сеть в интерьер базы. Ими можно закрыть кабели обоих размеров, а внешний вид фасада воспроизводит множество разных блоков.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/facades_1.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Кабель можно закрыть со всех сторон. [Части кабеля](../ae2-mechanics/cable-subparts.md) и соединения при этом проходят сквозь фасад и остаются снаружи.

<GameScene zoom="6"  interactive={true}>
  <ImportStructure src="../assets/assemblies/facades_2.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Комбинируйте фасады, чтобы сделать базу аккуратнее или создать блок, у которого каждая сторона выглядит по-разному.

<GameScene zoom="4" interactive={true}>
  <ImportStructure src="../assets/assemblies/facades_3.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Скрытие фасадов

Фасады становятся невидимыми, пока в любой руке находится <a href="network_tool.md">сетевой инструмент</a>.

С блоками за скрытыми фасадами можно взаимодействовать, не снимая облицовку.

## Рецепт

Поместите блок с нужной текстурой в центр между 4 <ItemLink id="cable_anchor" />.

![Рецепт фасада](../assets/diagrams/facade_recipe.png)
