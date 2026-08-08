---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Процессоры
  icon: logic_processor
  position: 010
categories:
- misc ingredients blocks
item_ids:
- ae2:logic_processor
- ae2:calculation_processor
- ae2:engineering_processor
- ae2:printed_silicon
- ae2:printed_logic_processor
- ae2:printed_calculation_processor
- ae2:printed_engineering_processor
- ae2:silicon
---

# Процессоры

<Row>
  <ItemImage id="logic_processor" scale="4" />

  <ItemImage id="calculation_processor" scale="4" />

  <ItemImage id="engineering_processor" scale="4" />
</Row>

Процессоры — одни из основных ингредиентов [устройств](../ae2-mechanics/devices.md) и механизмов AE2. Их серийное
производство станет одной из первых серьёзных задач автоматизации. Существует три типа процессоров: для них соответственно
нужны золото, <ItemLink id="certus_quartz_crystal" /> и алмаз. Процессоры изготавливаются в несколько этапов с помощью
[прессов](presses.md) и <ItemLink id="inscriber" />. Обычно производство автоматизируют цепочкой вырезателей и труб с фильтрами.

## Этапы производства

<Column gap="5">
  1.  Соберите или изготовьте нужные материалы: кремний, редстоун, золото, <ItemLink id="certus_quartz_crystal" /> и алмаз.

  <RecipeFor id="silicon" />

  <br />

  2.  Отпечатайте промежуточные компоненты схем.

  <Row>
    <RecipeFor id="printed_silicon" />

    <RecipeFor id="printed_logic_processor" />
  </Row>

  <Row>
    <RecipeFor id="printed_calculation_processor" />

    <RecipeFor id="printed_engineering_processor" />
  </Row>

  <br />

  3.  Выполните окончательную сборку.

  <Row>
    <RecipeFor id="logic_processor" />

    <RecipeFor id="calculation_processor" />
  </Row>

  <RecipeFor id="engineering_processor" />
</Column>
