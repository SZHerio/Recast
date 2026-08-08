---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Квантовый мост
  icon: quantum_ring
  position: 110
categories:
- network infrastructure
item_ids:
- ae2:quantum_link
- ae2:quantum_ring
---

# Квантовый сетевой мост

![Собранный квантовый сетевой мост](../assets/diagrams/quantum_bridge_demonstration.png)

Квантовый сетевой мост соединяет части [сети](../ae2-mechanics/me-network-connections.md) на неограниченном расстоянии
и даже в разных измерениях. Всего он передаёт 32 канала независимо от того, как кабели подключены к его граням. По сути,
мост работает как беспроводной [плотный кабель](cables.md#dense-cable).

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/quantum_bridge_internal_structure_1.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/quantum_bridge_internal_structure_2.snbt" />

  <BoxAnnotation color="#33dd33" min="1 1 1" max="6 2 3">
        Воображаемый кабель между двумя конечными точками
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Важно: чанки **с обеих сторон должны оставаться загруженными**. Если 2 части моста находятся далеко друг от друга,
используйте <ItemLink id="spatial_anchor" /> или другой загрузчик чанков.

# МЭ-квантовое кольцо

<BlockImage id="quantum_ring" scale="8" />

Разместите восемь таких блоков вокруг <ItemLink id="quantum_link" />, чтобы собрать квантовый сетевой мост. Подключение
к сети принимают только 4 блока <ItemLink id="quantum_ring" />, которые непосредственно соприкасаются с
<ItemLink id="quantum_link" />. К 4 угловым блокам подключить кабели нельзя.

## Рецепт

<RecipeFor id="quantum_ring" />

# МЭ-камера квантовой связи

<BlockImage id="quantum_link" scale="8" />

Один такой блок, окружённый <ItemLink id="quantum_ring" />, образует квантовый сетевой мост. Сама камера не подключается
к кабелям и становится частью сети только после полной сборки моста.

В инвентаре камеры помещается только один <ItemLink id="quantum_entangled_singularity" />. Этот слот доступен средствам автоматизации.

## Рецепт

<RecipeFor id="quantum_link" />
