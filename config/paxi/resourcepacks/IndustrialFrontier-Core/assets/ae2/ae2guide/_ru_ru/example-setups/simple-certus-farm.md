---
navigation:
  parent: example-setups/example-setups-index.md
  title: Простая ферма истинного кварца
  icon: certus_quartz_crystal
  position: 110
---

# Простая ферма истинного кварца

Как сказано в разделе [«Рост истинного кварца»](../ae2-mechanics/certus-growth.md), для автоматического сбора
<ItemLink id="certus_quartz_crystal" /> используются <ItemLink id="annihilation_plane" /> и
<ItemLink id="storage_bus" />. <ItemLink id="growth_accelerator" /> значительно ускоряет рост почек, после чего плоскости
разрушают полностью выросший <ItemLink id="quartz_cluster" />. Фильтрация опирается на удобную особенность: незрелые почки
истинного кварца оставляют <ItemLink id="certus_quartz_dust" />, а не исчезают без добычи.

С <ItemLink id="flawless_budding_quartz" /> ферма работает полностью автоматически. Потресканные, сколотые и повреждённые
цветущие блоки истинного кварца придётся заменять вручную. Автоматические варианты описаны в разделах
[«Полуавтоматическая ферма истинного кварца»](semiauto-certus-farm.md) и
[«Улучшенная ферма истинного кварца»](advanced-certus-farm.md).

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/simple_certus_farm.snbt" />

  <BoxAnnotation color="#dddddd" min="3.7 1 1" max="4 2 2">
        (1) МЭ-плоскость уничтожения: интерфейса настроек нет, можно наложить чары «Удача».
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="3 1 1" max="3.3 2 2">
        (2) МЭ-шина хранения № 1: фильтр настроен на Кристалл истинного кварца.
        <ItemImage id="certus_quartz_crystal" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="3 1 .7" max="2 2 1">
        (3) МЭ-шина хранения № 2: фильтр настроен на Кристалл истинного кварца, приоритет выше основного хранилища.
        <ItemImage id="certus_quartz_crystal" scale="2" />
  </BoxAnnotation>

<DiamondAnnotation pos="1 0.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* У <ItemLink id="annihilation_plane" /> (1) нет интерфейса настроек, но на плоскость можно наложить чары «Удача».
* Фильтр первой <ItemLink id="storage_bus" /> (2) настроен на <ItemLink id="certus_quartz_crystal" />.
* Фильтр второй <ItemLink id="storage_bus" /> (3) настроен на <ItemLink id="certus_quartz_crystal" />, а её
  [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) выше, чем у основного хранилища.

## Принцип работы

1. <ItemLink id="annihilation_plane" /> пытается разрушить блок перед собой, но может разрушить только
   <ItemLink id="quartz_cluster" />. Единственное хранилище подсети — <ItemLink id="storage_bus" /> с фильтром на
   <ItemLink id="certus_quartz_crystal" />.
4. Первая <ItemLink id="storage_bus" /> помещает кристаллы истинного кварца в бочку.
5. Вторая <ItemLink id="storage_bus" /> предоставляет основной сети доступ ко всем кристаллам в бочке. Высокий
   [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) заставляет систему возвращать кристаллы в эту
   бочку, а не отправлять их в основное хранилище.
