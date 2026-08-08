---
navigation:
  parent: example-setups/example-setups-index.md
  title: Автоматическая обработка руды «Удачей»
  icon: minecraft:raw_iron
---

# Автоматическая обработка руды «Удачей»

<ItemLink id="annihilation_plane" /> можно зачаровать любыми чарами кирки, включая «Удачу». Очевидное применение —
наложить «Удачу» на несколько плоскостей и заставить <ItemLink id="formation_plane" /> вместе с
<ItemLink id="annihilation_plane" /> быстро размещать и разрушать руду.

Учтите, что <ItemLink id="import_bus" /> постепенно «разгоняется»: сначала система работает медленно и лишь через
несколько секунд достигает полной скорости.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/ore_fortuner.snbt" />

  <BoxAnnotation color="#dddddd" min="2.7 0 2" max="3 1 3">
        (1) МЭ-шина импорта: установлено несколько Карт ускорения.
        <ItemImage id="speed_card" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="0 0 2" max="2 1 2.3">
        (2) МЭ-плоскости формирования: стандартные настройки.
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="0 0 0.7" max="2 1 1">
        (3) МЭ-плоскости уничтожения: интерфейса настроек нет, наложены чары «Удача».
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.7 0 0" max="3 1 1">
        (4) МЭ-шина хранения: стандартные настройки.
  </BoxAnnotation>

<DiamondAnnotation pos="3.5 0.5 2.5" color="#00ff00">
        Вход
    </DiamondAnnotation>

<DiamondAnnotation pos="3.5 0.5 0.5" color="#00ff00">
        Выход
    </DiamondAnnotation>

<DiamondAnnotation pos="4 0.5 1.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

*   В <ItemLink id="import_bus" /> (1) установлено несколько <ItemLink id="speed_card" />. Чем больше плоскостей
    формирования в ряду, тем больше требуется карт: они позволяют шине импорта забирать больше предметов одновременно.
*   <ItemLink id="formation_plane" /> (2) использует стандартные настройки.
*   У <ItemLink id="annihilation_plane" /> (3) нет интерфейса настроек, но на плоскости наложены чары «Удача».
*   <ItemLink id="storage_bus" /> (4) использует стандартные настройки.

## Принцип работы

1.  <ItemLink id="import_bus" /> зелёной подсети импортирует блоки из первой бочки в
    [сетевое хранилище](../ae2-mechanics/import-export-storage.md).
2.  Единственное хранилище зелёной подсети — <ItemLink id="formation_plane" />, поэтому плоскость размещает эти блоки.
3.  <ItemLink id="annihilation_plane" /> оранжевой подсети разрушает блоки и применяет к ним «Удачу».
4.  <ItemLink id="storage_bus" /> оранжевой подсети помещает результаты разрушения во вторую бочку.
