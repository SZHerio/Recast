---
navigation:
  parent: example-setups/example-setups-index.md
  title: Автоподдержание запаса излучателем уровня
  icon: level_emitter
---

# Автоподдержание запаса излучателем уровня

Как поддерживать заданное количество одного предмета и по мере необходимости изготавливать новые?

Один из вариантов — использовать <ItemLink id="export_bus" />, <ItemLink id="level_emitter" /> и
<ItemLink id="crafting_card" />. Они автоматически запрашивают новые предметы у системы
[автоматического изготовления](../ae2-mechanics/autocrafting.md). Эта схема рассчитана на большой запас одного предмета.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/level_emitter_autostocking.snbt" />

  <BoxAnnotation color="#dddddd" min="1 1 0" max="2 1.3 1">
        (1) МЭ-шина экспорта: фильтр настроен на нужный предмет; установлены Редстоуновая карта и Карта изготовления.
        Для «Режима красного камня» выбрано «Активируется сигналом», а для поведения изготовления — «Не использовать
        имеющиеся в наличии предметы, только изготавливать предметы при экспорте».
        <Row><ItemImage id="redstone_card" scale="2" /> <ItemImage id="crafting_card" scale="2" /></Row>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="0.7 1 0" max="1 2 1">
        (2) МЭ-излучатель уровня: заданы нужный предмет и количество; выбран режим «Излучать, когда уровни находятся ниже предела».
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1 0 0" max="2 1 1">
        (3) МЭ-интерфейс: стандартные настройки.
  </BoxAnnotation>

<DiamondAnnotation pos="4 0.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* Фильтр <ItemLink id="export_bus" /> (1) настройте на нужный предмет. Установите <ItemLink id="redstone_card" /> и
  <ItemLink id="crafting_card" />. Для «Режима красного камня» выберите «Активируется сигналом», а для поведения
  изготовления — «Не использовать имеющиеся в наличии предметы, только изготавливать предметы при экспорте».
* В <ItemLink id="level_emitter" /> (2) задайте нужный предмет и количество, затем выберите «Излучать, когда уровни
  находятся ниже предела».
* <ItemLink id="interface" /> (3) использует стандартные настройки.

## Принцип работы

1. Если количество нужного предмета в [сетевом хранилище](../ae2-mechanics/import-export-storage.md) ниже значения,
   заданного в <ItemLink id="level_emitter" />, излучатель подаёт сигнал редстоуна.
2. Получив сигнал, благодаря <ItemLink id="crafting_card" /> и запрету использовать предметы из запаса
   <ItemLink id="export_bus" /> запрашивает у системы [автоматического изготовления](../ae2-mechanics/autocrafting.md)
   новую партию, а затем экспортирует её.
3. <ItemLink id="interface" />, не настроенный на поддержание внутреннего запаса, принимает предмет и помещает его в
   сетевое хранилище.
