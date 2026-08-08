---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Энергохранилища
  icon: energy_cell
  position: 110
categories:
- network infrastructure
item_ids:
- ae2:energy_cell
- ae2:dense_energy_cell
- ae2:creative_energy_cell
---

# Энергохранилища

<Row gap="20">
  <BlockImage id="energy_cell" scale="8" p:fullness="4" />

  <BlockImage id="dense_energy_cell" scale="8" p:fullness="4" />

  <BlockImage id="creative_energy_cell" scale="8" />
</Row>

Энергохранилища увеличивают запас [энергии](../ae2-mechanics/energy.md) МЭ-сети. Даже небольшой буфер сглаживает резкие скачки потребления при массовом помещении или извлечении ресурсов. Большой запас позволяет сети продолжать работу, пока генераторы бездействуют — например, ночью при питании от солнечных панелей, — и выдерживать огромные мгновенные затраты [пространственного ввода-вывода](../ae2-mechanics/spatial-io.md).

## Индикаторы заполнения

<Row>
<BlockImage id="energy_cell" scale="4" p:fullness="0" />
<BlockImage id="energy_cell" scale="4" p:fullness="1" />
<BlockImage id="energy_cell" scale="4" p:fullness="2" />
<BlockImage id="energy_cell" scale="4" p:fullness="3" />
<BlockImage id="energy_cell" scale="4" p:fullness="4" />
</Row>

Полосы на боковых гранях показывают уровень заряда:

*   0 полос при заряде ниже 25%.
*   1 полоса при заряде от 25% до 50%.
*   2 полосы при заряде от 50% до 75%.
*   3 полосы при заряде от 75% до 99%.
*   4 полосы при заряде выше 99%.

## Виды энергохранилищ

*   <ItemLink id="energy_cell" /> вмещает 200 000 AE. Для большинства задач достаточно одного такого блока: он легко сглаживает скачки потребления обычной сети.
*   <ItemLink id="dense_energy_cell" /> вмещает 1,6 миллиона AE. Такой блок пригодится, если сеть должна долго работать на накопленной энергии или выдерживать огромные мгновенные затраты крупной системы [пространственного ввода-вывода](../ae2-mechanics/spatial-io.md).
*   <ItemLink id="creative_energy_cell" /> — творческий блок для испытаний, предоставляющий неограниченное количество энергии.

## Рецепты

<Row>
  <RecipeFor id="energy_cell" />

  <RecipeFor id="dense_energy_cell" />
</Row>
