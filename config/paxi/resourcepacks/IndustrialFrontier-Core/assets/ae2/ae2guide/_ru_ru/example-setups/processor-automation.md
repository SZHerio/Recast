---
navigation:
  parent: example-setups/example-setups-index.md
  title: Автоматизация процессоров
  icon: inscriber
---

# Автоматизация производства процессоров

[Процессоры](../items-blocks-machines/processors.md) можно автоматизировать многими способами. Ниже показан один из них.

Эту общую схему можно собрать с любыми фильтруемыми предметными трубами, проводниками или каналами из других модов,
независимо от их названия.

![Схема потока производства](../assets/diagrams/processor_flow_diagram.png)

Далее подробно описана реализация только средствами AE2 с помощью [подсетей-«труб»](pipe-subnet.md).

Система использует <ItemLink id="pattern_provider" /> и предназначена для подключения к
[автоматическому изготовлению](../ae2-mechanics/autocrafting.md). Для отдельной автоматизации процессоров замените
поставщик шаблонов ещё одной бочкой и вручную помещайте ингредиенты в верхнюю бочку.

Схема совместима и с прежними версиями AE2. Даже если стороны <ItemLink id="inscriber" /> имеют разные назначения,
подсети-трубы по-прежнему подают и извлекают ресурсы через правильные грани.

<GameScene zoom="4" interactive={true}>
  <ImportStructure src="../assets/assemblies/processor_automation.snbt" />

  <BoxAnnotation color="#dddddd" min="5 1 0" max="6 2 1" thickness=".05">
        (1) МЭ-поставщик шаблонов: стандартные настройки и нужные шаблоны обработки.

        <Row>
            ![Логический шаблон](../assets/diagrams/logic_pattern_small.png)
            ![Вычислительный шаблон](../assets/diagrams/calculation_pattern_small.png)
            ![Инженерный шаблон](../assets/diagrams/engineering_pattern_small.png)
        </Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4.7 2 0" max="5 3 1" thickness=".05">
        (2) МЭ-шина хранения № 1: стандартные настройки.
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 1 0" max="4.3 2 1" thickness=".05">
        (3) МЭ-шина экспорта № 1: фильтр настроен на кремний; установлены две Карты ускорения.
        <Row><ItemImage id="silicon" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 4 0" max="4.3 3 1" thickness=".05">
        (4) МЭ-шина экспорта № 2: фильтр настроен на золотой слиток; установлены две Карты ускорения.
        <Row><ItemImage id="minecraft:gold_ingot" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 5 0" max="4.3 4 1" thickness=".05">
        (5) МЭ-шина экспорта № 3: фильтр настроен на Кристалл истинного кварца; установлены две Карты ускорения.
        <Row><ItemImage id="certus_quartz_crystal" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 6 0" max="4.3 5 1" thickness=".05">
        (6) МЭ-шина экспорта № 4: фильтр настроен на алмаз; установлены две Карты ускорения.
        <Row><ItemImage id="minecraft:diamond" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.3 3 0" max="2 2 1" thickness=".05">
        (7) МЭ-шина экспорта № 5: фильтр настроен на редстоун; установлены две Карты ускорения.
        <Row><ItemImage id="minecraft:redstone" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 1 0" max="3 2 1" thickness=".05">
        (8) Вырезатель № 1: стандартные настройки; установлены Кремниевая печать для вырезателя и четыре Карты ускорения.
        <Row><ItemImage id="silicon_press" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 3 0" max="3 4 1" thickness=".05">
        (9) Вырезатель № 2: стандартные настройки; установлены Логическая печать для вырезателя и четыре Карты ускорения.
        <Row><ItemImage id="logic_processor_press" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 4 0" max="3 5 1" thickness=".05">
        (10) Вырезатель № 3: стандартные настройки; установлены Вычислительная печать для вырезателя и четыре Карты ускорения.
        <Row><ItemImage id="calculation_processor_press" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="4 5 0" max="3 6 1" thickness=".05">
        (11) Вырезатель № 4: стандартные настройки; установлены Инженерная печать для вырезателя и четыре Карты ускорения.
        <Row><ItemImage id="engineering_processor_press" scale="2" /> <ItemImage id="speed_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2 2 0" max="1 3 1" thickness=".05">
        (12) Вырезатель № 5: стандартные настройки; установлены четыре Карты ускорения.
        <ItemImage id="speed_card" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.7 2 0" max="3 1 1" thickness=".05">
        (13) МЭ-шина импорта № 1: стандартные настройки; установлены две Карты ускорения.
        <ItemImage id="speed_card" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.7 4 0" max="3 3 1" thickness=".05">
        (14) МЭ-шина импорта № 2: стандартные настройки; установлены две Карты ускорения.
        <ItemImage id="speed_card" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.7 5 0" max="3 4 1" thickness=".05">
        (15) МЭ-шина импорта № 3: стандартные настройки; установлены две Карты ускорения.
        <ItemImage id="speed_card" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.7 6 0" max="3 5 1" thickness=".05">
        (16) МЭ-шина импорта № 4: стандартные настройки; установлены две Карты ускорения.
        <ItemImage id="speed_card" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2 3 0" max="1 3.3 1" thickness=".05">
        (17) МЭ-шина хранения № 2: стандартные настройки.
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2 1.7 0" max="1 2 1" thickness=".05">
        (18) МЭ-шина хранения № 3: стандартные настройки.
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1 2 0" max="0.7 3 1" thickness=".05">
        (19) МЭ-шина импорта № 5: стандартные настройки; установлены две Карты ускорения.
        <ItemImage id="speed_card" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="5 0.7 0" max="6 1 1" thickness=".05">
        (20) МЭ-шина хранения № 4: стандартные настройки.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="3.3 2.7 0.3" max="3.7 3 0.7" thickness=".05">
        Кварцевое волокно питает все пять вырезателей, потому что вырезатели действуют как кабели и передают энергию.
  </BoxAnnotation>

<DiamondAnnotation pos="7 1.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="185" pitch="5" />
</GameScene>

## Настройки

* <ItemLink id="pattern_provider" /> (1) использует стандартные настройки и содержит нужные
  <ItemLink id="processing_pattern" />.

  ![Логический шаблон](../assets/diagrams/logic_pattern.png)
  ![Вычислительный шаблон](../assets/diagrams/calculation_pattern.png)
  ![Инженерный шаблон](../assets/diagrams/engineering_pattern.png)

* <ItemLink id="storage_bus" /> (2, 17, 18, 20) использует стандартные настройки.
* Фильтры <ItemLink id="export_bus" /> (3–7) настроены на соответствующие ингредиенты. В каждую шину установлены две
  <ItemLink id="speed_card" />.
    <Row>
      <ItemImage id="silicon" scale="2" />
      <ItemImage id="minecraft:gold_ingot" scale="2" />
      <ItemImage id="certus_quartz_crystal" scale="2" />
      <ItemImage id="minecraft:diamond" scale="2" />
      <ItemImage id="minecraft:redstone" scale="2" />
    </Row>
* <ItemLink id="import_bus" /> (13–16, 19) использует стандартные настройки. В каждую шину установлены две
  <ItemLink id="speed_card" />.
* <ItemLink id="inscriber" /> использует стандартные настройки. В каждый вырезатель установлены соответствующая
  [печать](../items-blocks-machines/presses.md) и четыре <ItemLink id="speed_card" />.
   <Row>
     <ItemImage id="silicon_press" scale="2" />
     <ItemImage id="logic_processor_press" scale="2" />
     <ItemImage id="calculation_processor_press" scale="2" />
     <ItemImage id="engineering_processor_press" scale="2" />
   </Row>

## Принцип работы

1. <ItemLink id="pattern_provider" /> отправляет ингредиенты в бочку.
2. Первая [подсеть-труба](pipe-subnet.md), оранжевая, извлекает из бочки кремний, редстоун и материал соответствующего
   процессора — золотой слиток, кристалл истинного кварца или алмаз — и помещает их в нужный
   <ItemLink id="inscriber" />.
3. Первые четыре <ItemLink id="inscriber" /> изготавливают <ItemLink id="printed_silicon" /> и одну из печатных схем:
   <ItemLink id="printed_logic_processor" />, <ItemLink id="printed_calculation_processor" /> или
   <ItemLink id="printed_engineering_processor" />.
4. Вторая и третья [подсети-трубы](pipe-subnet.md), зелёные, извлекают печатные схемы из первых четырёх
   <ItemLink id="inscriber" /> и помещают их в пятый, сборочный <ItemLink id="inscriber" />.
5. Пятый <ItemLink id="inscriber" /> собирает [процессор](../items-blocks-machines/processors.md).
6. Четвёртая [подсеть-труба](pipe-subnet.md), фиолетовая, помещает процессор в МЭ-поставщик шаблонов и возвращает его в
   основную сеть.
