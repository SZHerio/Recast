---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: МЭ-плоскость уничтожения
  icon: annihilation_plane
  position: 210
categories:
- devices
item_ids:
- ae2:annihilation_plane
---

# МЭ-плоскость уничтожения

<GameScene zoom="8" background="transparent">
<ImportStructure src="../assets/blocks/annihilation_plane.snbt" />
</GameScene>

МЭ-плоскость уничтожения ломает блоки и подбирает предметы. Она работает подобно <ItemLink id="import_bus" />, отправляя
ресурсы в [сетевое хранилище](../ae2-mechanics/import-export-storage.md). Чтобы плоскость подобрала предмет, он должен
столкнуться с её лицевой стороной: предметы в окружающей области она не собирает.

На плоскость уничтожения можно наложить любые чары для кирки. Если сборка это допускает, несколько плоскостей с очень
высоким уровнем «Удачи» позволяют [автоматизировать обработку руды](../example-setups/ore-fortuner.md). «Шёлковое касание»
работает обычным образом, «Эффективность» снижает расход энергии при разрушении блока, а «Прочность» даёт шанс вовсе не
потратить энергию.

Плоскости относятся к [кабельным частям](../ae2-mechanics/cable-subparts.md).

**НЕ ЗАБУДЬТЕ РАЗРЕШИТЬ ФИКТИВНЫХ ИГРОКОВ В НАСТРОЙКАХ ПРИВАТА ЧАНКА.**

## Фильтрация

Плоскость уничтожает блок или подбирает предмет, только если сеть способна сохранить полученный ресурс. Поэтому для
фильтрации необходимо ограничить список ресурсов, которые может принять её сеть. Обычно для этого плоскость помещают в
[подсеть](../ae2-mechanics/subnetworks.md). Фильтр можно задать для <ItemLink id="storage_bus" /> или
[ячейки](../items-blocks-machines/storage_cells.md) с помощью [верстака для ячеек](cell_workbench.md).

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/annihilation_filtering.snbt" />

  <DiamondAnnotation pos="1 0.5 0.5" color="#00ff00">
        Фильтр настроен на предметы, выпадающие из блока, который требуется разрушать.
  </DiamondAnnotation>

  <DiamondAnnotation pos=".5 0.5 2.5" color="#00ff00">
        Ячейка настроена на предметы, выпадающие из блока, который требуется разрушать.
  </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Ещё раз: фильтр проверяет именно *выпадающие предметы*. Например, чтобы разрешить разрушение
<ItemLink id="minecraft:amethyst_cluster" />, на плоскость необходимо наложить «Шёлковое касание». Без этих чар каждая
предыдущая стадия роста не оставляет предметов, поэтому плоскость всё равно её сломает: сеть всегда может сохранить
«ничего».

## Рецепт

<RecipeFor id="annihilation_plane" />
