---
navigation:
  parent: example-setups/example-setups-index.md
  title: Полуавтоматическая ферма истинного кварца
  icon: certus_quartz_crystal
  position: 115
---

# Полуавтоматическая ферма истинного кварца

К сожалению, для полностью автоматической работы [простой ферме истинного кварца](simple-certus-farm.md) требуется
<ItemLink id="flawless_budding_quartz" />. Для этого потребуется [пространственный
ввод/вывод](../ae2-mechanics/spatial-io.md) либо ферму придётся построить у [метеорита](../ae2-mechanics/meteorites.md).

Однако AE2 умеет размещать и разрушать блоки, поэтому ферма может *самостоятельно заменять цветущий истинный кварц*.
Вам лишь придётся периодически добавлять <ItemLink id="flawed_budding_quartz" /> во входную бочку и забирать
<ItemLink id="quartz_block" /> из бочки истощившихся блоков.

Полностью автоматический вариант описан в разделе [«Улучшенная ферма истинного кварца»](advanced-certus-farm.md).

Эта ферма сложнее [простой](simple-certus-farm.md), поскольку фактически объединяет три отдельные системы.

**ЭТО СЛОЖНАЯ КОНСТРУКЦИЯ: ЧАСТЬ КОМПОНЕНТОВ СКРЫТА ЗА ДРУГИМИ. ПОВЕРНИТЕ КАМЕРУ И ОСМОТРИТЕ ЕЁ СО ВСЕХ СТОРОН.**

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/semiauto_certus_farm.snbt" />

  <BoxAnnotation color="#ddaaaa" min="3.7 2 1" max="4 3 2">
        (1) МЭ-плоскость уничтожения № 1: интерфейса настроек нет, можно наложить чары «Удача».
  </BoxAnnotation>

  <BoxAnnotation color="#ddaaaa" min="2 2 1" max="2.3 3 2">
        (2) МЭ-шина хранения № 1: фильтр настроен на Кристалл истинного кварца.
        <ItemImage id="certus_quartz_crystal" scale="2" />
  </BoxAnnotation>

  <DiamondAnnotation pos="3 2.5 1.5" color="#ff0000">
    Подсеть разрушения друз
  </DiamondAnnotation>

  <BoxAnnotation color="#aaddaa" min="3.7 1 1" max="4 2 2">
        (3) МЭ-плоскость уничтожения № 2: интерфейса настроек нет, наложены чары «Шёлковое касание».
  </BoxAnnotation>

  <BoxAnnotation color="#aaddaa" min="2 1 1" max="2.3 2 2">
        (4) МЭ-шина хранения № 2: фильтр настроен на Блок истинного кварца.
        <BlockImage id="quartz_block" scale="2" />
  </BoxAnnotation>

  <DiamondAnnotation pos="3 1.5 1.5" color="#00ff00">
    Подсеть разрушения блоков истинного кварца
  </DiamondAnnotation>

  <BoxAnnotation color="#ffddaa" min="4 0.7 1" max="5 1 2">
        (5) МЭ-плоскость формирования: стандартные настройки.
  </BoxAnnotation>

  <BoxAnnotation color="#ffddaa" min="2 0 1" max="2.3 1 2">
        (6) МЭ-шина импорта: стандартные настройки.
  </BoxAnnotation>

  <DiamondAnnotation pos="3 0.5 1.5" color="#ddcc00">
    Подсеть установки цветущих блоков
  </DiamondAnnotation>

  <BoxAnnotation color="#aaaadd" min="0.7 2 1" max="1 3 2">
        (7) МЭ-шина хранения № 3: фильтр настроен на Кристалл истинного кварца, приоритет выше основного хранилища.
        <ItemImage id="certus_quartz_crystal" scale="2" />
  </BoxAnnotation>

    <DiamondAnnotation pos="1.5 0.5 1.5" color="#00ff00">
        Вручную добавляйте Потресканный цветущий блок истинного кварца.
        <BlockImage id="flawed_budding_quartz" scale="2" />
    </DiamondAnnotation>

    <DiamondAnnotation pos="1.5 1.5 1.5" color="#00ff00">
        Вручную забирайте Блок истинного кварца.
        <BlockImage id="quartz_block" scale="2" />
    </DiamondAnnotation>

<DiamondAnnotation pos="0.5 0.5 0" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="165" pitch="5" />
</GameScene>

## Настройки

### Разрушитель друз

* У первой <ItemLink id="annihilation_plane" /> (1) нет интерфейса настроек, но на плоскость можно наложить «Удачу».
* Фильтр первой <ItemLink id="storage_bus" /> (2) настроен на <ItemLink id="certus_quartz_crystal" />.

### Разрушитель блоков истинного кварца

* У второй <ItemLink id="annihilation_plane" /> (3) нет интерфейса настроек; на неё обязательно наложите
  «Шёлковое касание».
* Фильтр второй <ItemLink id="storage_bus" /> (4) настроен на <ItemLink id="quartz_block" />.

### Установщик цветущих блоков

* <ItemLink id="formation_plane" /> (5) использует стандартные настройки.
* <ItemLink id="import_bus" /> (6) использует стандартные настройки.

### В основной сети

* Фильтр третьей <ItemLink id="storage_bus" /> (7) настроен на <ItemLink id="certus_quartz_crystal" />, а её
  [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) выше приоритета основного хранилища.

## Принцип работы

### Разрушитель друз

Эта подсеть работает почти так же, как подсеть [простой фермы истинного кварца](simple-certus-farm.md).

1. <ItemLink id="annihilation_plane" /> пытается разрушить блок перед собой, но может разрушить только
   <ItemLink id="quartz_cluster" />. Единственное хранилище подсети — <ItemLink id="storage_bus" /> с фильтром на
   <ItemLink id="certus_quartz_crystal" />.
2. <ItemLink id="storage_bus" /> помещает кристаллы истинного кварца в бочку.

### Разрушитель блоков истинного кварца

Эта подсеть разрушает истощившийся цветущий блок после того, как он превращается в обычный
<ItemLink id="quartz_block" />. Принцип похож на разрушитель друз.

1. <ItemLink id="annihilation_plane" /> пытается разрушить блок перед собой, но может разрушить только
   <ItemLink id="quartz_block" />. Единственное хранилище подсети — <ItemLink id="storage_bus" /> с фильтром на
   <ItemLink id="quartz_block" />. Плоскости необходимо «Шёлковое касание», чтобы цветущий блок не ухудшался при
   разрушении: иначе плоскость могла бы сломать его раньше времени.
2. <ItemLink id="storage_bus" /> помещает блок истинного кварца в бочку истощившихся цветущих блоков. Вам придётся
   вручную бросить его в воду вместе с <ItemLink id="charged_certus_quartz_crystal" />, чтобы восстановить блок.

### Установщик цветущих блоков

Эта подсеть размещает новый <ItemLink id="flawed_budding_quartz" />, когда подсеть разрушения убирает старый истощённый
блок.

1. <ItemLink id="import_bus" /> импортирует цветущий блок из входной бочки.
2. Единственное хранилище подсети — <ItemLink id="formation_plane" />, поэтому плоскость размещает цветущий блок.

### Основная сеть

* <ItemLink id="storage_bus" /> предоставляет основной сети и [автоматизации зарядника](charger-automation.md) доступ ко
  всем кристаллам истинного кварца в бочке. Высокий
  [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) заставляет систему возвращать кристаллы в эту
  бочку, а не отправлять в основное хранилище.
