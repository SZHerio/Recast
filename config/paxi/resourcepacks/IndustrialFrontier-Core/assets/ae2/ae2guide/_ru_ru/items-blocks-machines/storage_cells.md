---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Ячейки хранения
  icon: item_storage_cell_1k
  position: 410
categories:
- tools
item_ids:
- ae2:item_cell_housing
- ae2:fluid_cell_housing
- ae2:cell_component_1k
- ae2:cell_component_4k
- ae2:cell_component_16k
- ae2:cell_component_64k
- ae2:cell_component_256k
- ae2:item_storage_cell_1k
- ae2:item_storage_cell_4k
- ae2:item_storage_cell_16k
- ae2:item_storage_cell_64k
- ae2:item_storage_cell_256k
- ae2:fluid_storage_cell_1k
- ae2:fluid_storage_cell_4k
- ae2:fluid_storage_cell_16k
- ae2:fluid_storage_cell_64k
- ae2:fluid_storage_cell_256k
---

# Ячейки хранения

<Column>
  <Row>
    <ItemImage id="item_storage_cell_1k" scale="4" />

    <ItemImage id="item_storage_cell_4k" scale="4" />

    <ItemImage id="item_storage_cell_16k" scale="4" />

    <ItemImage id="item_storage_cell_64k" scale="4" />

    <ItemImage id="item_storage_cell_256k" scale="4" />
  </Row>

  <Row>
    <ItemImage id="fluid_storage_cell_1k" scale="4" />

    <ItemImage id="fluid_storage_cell_4k" scale="4" />

    <ItemImage id="fluid_storage_cell_16k" scale="4" />

    <ItemImage id="fluid_storage_cell_64k" scale="4" />

    <ItemImage id="fluid_storage_cell_256k" scale="4" />
  </Row>
</Column>

Ячейки хранения — один из основных способов хранить ресурсы в Applied Energistics. Их устанавливают в <ItemLink id="drive" /> или <ItemLink id="chest" />.

Принцип расчёта вместимости в байтах и типах описан в разделе [«Байты и типы»](../ae2-mechanics/bytes-and-types.md).

Если ячейка пуста, из неё можно извлечь компонент хранения: возьмите ячейку в руку и щёлкните ПКМ с зажатым Shift.

## Вместимость при разном числе типов

Из-за [начальной стоимости типа](../ae2-mechanics/bytes-and-types.md) ячейка с 1 типом вмещает вдвое больше предметов, чем ячейка, в которой заняты все 63 типа.

| Ячейка                                  | Общая вместимость при 1 типе | Общая вместимость при 63 типах |
| --------------------------------------- | ---------------------------: | -----------------------------: |
| <ItemLink id="item_storage_cell_1k" />   |                        8 128 |                          4 160 |
| <ItemLink id="item_storage_cell_4k" />   |                       32 512 |                         16 640 |
| <ItemLink id="item_storage_cell_16k" />  |                      130 048 |                         66 560 |
| <ItemLink id="item_storage_cell_64k" />  |                      520 192 |                        266 240 |
| <ItemLink id="item_storage_cell_256k" /> |                    2 080 768 |                      1 064 960 |


## Фильтрация

Ячейку можно настроить так, чтобы она принимала только определённые ресурсы, — почти как <ItemLink id="storage_bus" />. Фильтр задаётся в <ItemLink id="cell_workbench" />.

Предметы можно перетаскивать в слоты фильтра из JEI, даже если их нет в инвентаре игрока.

## Улучшения

В <ItemLink id="cell_workbench" /> в ячейку можно установить следующие [улучшения](upgrade_cards.md):

*   <ItemLink id="fuzzy_card" /> — позволяет учитывать степень повреждения предметов и/или игнорировать NBT; недоступно для жидкостных ячеек.
*   <ItemLink id="inverter_card" /> — превращает белый список фильтра в чёрный.
*   <ItemLink id="equal_distribution_card" /> — выделяет каждому типу одинаковую долю байтов ячейки, поэтому один тип не сможет занять всё место.
*   <ItemLink id="void_card" /> — уничтожает поступающие ресурсы, когда ячейка заполнена. Если установлено улучшение равномерного распределения, учитывается заполнение доли конкретного типа. Это помогает не останавливать фермы из-за переполнения, но обязательно задайте фильтр, чтобы не потерять нужные ресурсы.
*   Переносные ячейки принимают <ItemLink id="energy_card" />, увеличивающую ёмкость встроенной батареи.

## Окрашивание

Переносные предметные и жидкостные ячейки можно окрашивать красителями так же, как кожаную броню: объедините ячейку с красителем при изготовлении.

# Корпуса

Ячейку можно изготовить из компонента хранения и корпуса либо окружить компонент материалами для корпуса:

<Row>
  <Recipe id="network/cells/item_storage_cell_1k" />

  <Recipe id="network/cells/item_storage_cell_1k_storage" />
</Row>

Отдельные корпуса изготавливаются так:

<Row>
  <RecipeFor id="item_cell_housing" />

  <RecipeFor id="fluid_cell_housing" />
</Row>

# Компоненты хранения

Компонент хранения — основа любой ячейки AE2, определяющая её вместимость. Каждый следующий уровень увеличивает вместимость вчетверо и требует 3 компонента предыдущего уровня.

<Column>
  <Row>
    <RecipeFor id="cell_component_1k" />

    <RecipeFor id="cell_component_4k" />

    <RecipeFor id="cell_component_16k" />
  </Row>

  <Row>
    <RecipeFor id="cell_component_64k" />

    <RecipeFor id="cell_component_256k" />
  </Row>
</Column>

# Предметные ячейки хранения

Предметная ячейка может содержать до 63 разных типов предметов. Такие ячейки доступны во всех стандартных вариантах вместимости.

<Column>
  <Row>
    <Recipe id="network/cells/item_storage_cell_1k_storage" />

    <Recipe id="network/cells/item_storage_cell_4k_storage" />

    <Recipe id="network/cells/item_storage_cell_16k_storage" />
  </Row>

  <Row>
    <Recipe id="network/cells/item_storage_cell_64k_storage" />

    <Recipe id="network/cells/item_storage_cell_256k_storage" />
  </Row>
</Column>

## Переносные предметные ячейки

Такая ячейка работает как карманный <ItemLink id="chest" /> или небольшой рюкзак. Зарядить её можно в <ItemLink id="charger" />.

В отличие от обычных ячеек, с ростом байтовой вместимости у переносных ячеек *уменьшается* число доступных типов. Их общая байтовая вместимость также вдвое ниже.

Помимо улучшений, доступных всем ячейкам, переносные варианты принимают <ItemLink id="energy_card" />, увеличивающую ёмкость встроенной батареи.

<Column>
  <Row>
    <RecipeFor id="portable_item_cell_1k" />

    <RecipeFor id="portable_item_cell_4k" />

    <RecipeFor id="portable_item_cell_16k" />
  </Row>

  <Row>
    <RecipeFor id="portable_item_cell_64k" />

    <RecipeFor id="portable_item_cell_256k" />
  </Row>
</Column>

# Жидкостные ячейки хранения

Жидкостная ячейка может содержать до 5 разных типов жидкостей. Такие ячейки доступны во всех стандартных вариантах вместимости.

<Column>
  <Row>
    <Recipe id="network/cells/fluid_storage_cell_1k_storage" />

    <Recipe id="network/cells/fluid_storage_cell_4k_storage" />

    <Recipe id="network/cells/fluid_storage_cell_16k_storage" />
  </Row>

  <Row>
    <Recipe id="network/cells/fluid_storage_cell_64k_storage" />

    <Recipe id="network/cells/fluid_storage_cell_256k_storage" />
  </Row>
</Column>

## Переносные жидкостные ячейки

Такая ячейка работает как карманный <ItemLink id="chest" /> или небольшой рюкзак. Зарядить её можно в <ItemLink id="charger" />.

В отличие от обычных ячеек, с ростом байтовой вместимости у переносных ячеек *уменьшается* число доступных типов. Их общая байтовая вместимость также вдвое ниже.

Помимо улучшений, доступных всем ячейкам, переносные варианты принимают <ItemLink id="energy_card" />, увеличивающую ёмкость встроенной батареи.

<Column>
  <Row>
    <RecipeFor id="portable_fluid_cell_1k" />

    <RecipeFor id="portable_fluid_cell_4k" />

    <RecipeFor id="portable_fluid_cell_16k" />
  </Row>

  <Row>
    <RecipeFor id="portable_fluid_cell_64k" />

    <RecipeFor id="portable_fluid_cell_256k" />
  </Row>
</Column>

# Творческие предметные и жидкостные ячейки

<Row>
  <ItemImage id="creative_item_cell" scale="2" />

  <ItemImage id="creative_fluid_cell" scale="2" />
</Row>

Творческие предметные и жидкостные ячейки **не предоставляют бесконечное хранилище**. Вместо этого они служат бесконечным источником и поглотителем того предмета или жидкости, который задан им с помощью [фильтра](cell_workbench.md).
