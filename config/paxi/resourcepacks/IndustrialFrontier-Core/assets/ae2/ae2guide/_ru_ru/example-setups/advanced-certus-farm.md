---
navigation:
  parent: example-setups/example-setups-index.md
  title: Улучшенная ферма истинного кварца
  icon: certus_quartz_crystal
  position: 120
---

# Улучшенная ферма истинного кварца

По сути, это [полуавтоматическая ферма истинного кварца](semiauto-certus-farm.md), полностью встроенная в МЭ-систему.

Вместо большого запаса цветущих блоков и их периодического ручного восстановления здесь используются
[автоматизация зарядника](charger-automation.md) и [автоматизация бросания в воду](throw-in-water-automation.md).

**ЭТО СЛОЖНАЯ КОНСТРУКЦИЯ: ЧАСТЬ КОМПОНЕНТОВ СКРЫТА ЗА ДРУГИМИ. ПОВЕРНИТЕ КАМЕРУ И ОСМОТРИТЕ ЕЁ СО ВСЕХ СТОРОН.**

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/advanced_certus_farm.snbt" />

  <BoxAnnotation color="#ddaaaa" min="3.7 2 1" max="4 3 2">
        (1) МЭ-плоскость уничтожения № 1: интерфейса настроек нет, можно наложить чары «Удача».
  </BoxAnnotation>

  <BoxAnnotation color="#ddaaaa" min="2 2 1.7" max="3 3 2">
        (2) МЭ-шина хранения № 1: фильтр настроен на Кристалл истинного кварца.
        <ItemImage id="certus_quartz_crystal" scale="2" />
  </BoxAnnotation>

  <DiamondAnnotation pos="3 2.5 1.5" color="#ff0000">
    Подсеть разрушения друз
  </DiamondAnnotation>

  <BoxAnnotation color="#aaddaa" min="3.7 1 1" max="4 2 2">
        (3) МЭ-плоскость уничтожения № 2: интерфейса настроек нет, наложены чары «Шёлковое касание».
  </BoxAnnotation>

  <BoxAnnotation color="#aaddaa" min="2 1 1.7" max="3 2 2">
        (4) МЭ-шина хранения № 2: фильтр настроен на Блок истинного кварца.
        <BlockImage id="quartz_block" scale="2" />
  </BoxAnnotation>

  <DiamondAnnotation pos="3 1.5 1.5" color="#00ff00">
    Подсеть разрушения блоков истинного кварца
  </DiamondAnnotation>

  <BoxAnnotation color="#ffddaa" min="4 0.7 1" max="5 1 2">
        (5) МЭ-плоскость формирования: стандартные настройки.
  </BoxAnnotation>

  <BoxAnnotation color="#ffddaa" min="2 0.7 2" max="3 1 3">
        (6) МЭ-шина импорта: фильтр настроен на Потресканный цветущий блок истинного кварца.
        <BlockImage id="flawed_budding_quartz" scale="2" />
  </BoxAnnotation>

  <DiamondAnnotation pos="3 0.5 1.5" color="#ddcc00">
    Подсеть установки цветущих блоков
  </DiamondAnnotation>

  <BoxAnnotation color="#aaaadd" min="1.7 2 2" max="2 3 3">
        (7) МЭ-шина хранения № 3: фильтр настроен на Кристалл истинного кварца, приоритет выше основного хранилища.
        <ItemImage id="certus_quartz_crystal" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#aaaadd" min="2 1 2" max="3 2 3">
        (8) МЭ-интерфейс: поддерживает запас из одного Потресканного цветущего блока истинного кварца; установлена
        Карта изготовления.
        <Row><BlockImage id="flawed_budding_quartz" scale="2" /> <ItemImage id="crafting_card" scale="2" /></Row>
  </BoxAnnotation>

<DiamondAnnotation pos="1.5 0.5 0" color="#00ff00">
        К основной сети, автоматизации зарядника и автоматизации бросания в воду
        <Row>
        <GameScene zoom="3" background="transparent">
          <ImportStructure src="../assets/assemblies/charger_automation.snbt" />
          <IsometricCamera yaw="195" pitch="30" />
        </GameScene>
        <GameScene zoom="3" background="transparent">
          <ImportStructure src="../assets/assemblies/throw_in_water.snbt" />
          <IsometricCamera yaw="195" pitch="30" />
        </GameScene>
        </Row>
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
* Фильтр <ItemLink id="import_bus" /> (6) настроен на <ItemLink id="flawed_budding_quartz" />.

### В основной сети

* Фильтр третьей <ItemLink id="storage_bus" /> (7) настроен на <ItemLink id="certus_quartz_crystal" />, а её
  [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) выше приоритета основного хранилища.
* <ItemLink id="interface" /> (8) поддерживает внутри запас из одного Потресканного цветущего блока истинного кварца и
  содержит <ItemLink id="crafting_card" />.

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
2. <ItemLink id="storage_bus" /> помещает блок истинного кварца в <ItemLink id="interface" />. Благодаря этому
   [автоматизация бросания в воду](throw-in-water-automation.md) сможет превратить блок в новый
   <ItemLink id="flawed_budding_quartz" />.

### Установщик цветущих блоков

Эта подсеть размещает новый <ItemLink id="flawed_budding_quartz" />, когда подсеть разрушения убирает старый истощённый
блок.

1. <ItemLink id="import_bus" /> импортирует цветущий блок из <ItemLink id="interface" /> в
   [сетевое хранилище](../ae2-mechanics/import-export-storage.md).
2. Единственное хранилище подсети — <ItemLink id="formation_plane" />, поэтому плоскость размещает цветущий блок.

### Основная сеть

* <ItemLink id="storage_bus" /> предоставляет основной сети и [автоматизации зарядника](charger-automation.md) доступ ко
  всем кристаллам истинного кварца в бочке. Высокий
  [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) заставляет систему возвращать кристаллы в эту
  бочку, а не отправлять в основное хранилище.
* <ItemLink id="interface" /> предоставляет подсети установки доступ к <ItemLink id="flawed_budding_quartz" /> и позволяет
  подсети разрушения вернуть истощённые блоки в основную сеть. <ItemLink id="crafting_card" /> позволяет интерфейсу
  запросить новые цветущие блоки у системы [автоматического изготовления](../ae2-mechanics/autocrafting.md) основной сети.
