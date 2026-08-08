---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Беспроводные терминалы
  icon: wireless_crafting_terminal
  position: 410
categories:
- tools
item_ids:
- ae2:wireless_terminal
- ae2:wireless_crafting_terminal
---

# Беспроводные терминалы

<Row>
  <ItemImage id="wireless_terminal" scale="4" />

  <ItemImage id="wireless_crafting_terminal" scale="4" />
</Row>

Беспроводные терминалы — переносные версии обычных проводных [МЭ-терминалов](terminals.md). Их интерфейсы полностью совпадают с проводными вариантами, но вместо слотов для <ItemLink id="view_cell" /> в них расположены слоты [карт улучшения](upgrade_cards.md).

Чтобы привязать терминал к сети, поместите его в правый верхний слот <ItemLink id="wireless_access_point" />, подключённой к этой сети. Нужный слот отмечен изображением беспроводного терминала и стрелкой под ним.

Терминал работает только в радиусе действия <ItemLink id="wireless_access_point" />.

Его встроенную батарею можно зарядить в <ItemLink id="charger" />.

# Беспроводной терминал

<ItemImage id="wireless_terminal" scale="4" />

Обычный терминал, который можно носить с собой. В пределах действия <ItemLink id="wireless_access_point" /> он позволяет просматривать [сетевое хранилище](../ae2-mechanics/import-export-storage.md), извлекать и помещать ресурсы, а также отправлять заказы системе [автоматического изготовления](../ae2-mechanics/autocrafting.md).

## Интерфейс

См. раздел [«МЭ-терминалы»](terminals.md).

## Улучшения

Беспроводной терминал поддерживает следующие [улучшения](upgrade_cards.md):

*   <ItemLink id="energy_card" /> — увеличивает ёмкость встроенной батареи.

## Рецепт

<RecipeFor id="wireless_terminal" />

# Беспроводной терминал изготовления

<ItemImage id="wireless_crafting_terminal" scale="4" />

Беспроводной терминал изготовления содержит все настройки и области обычного беспроводного терминала, но дополнен сеткой изготовления. Ингредиенты в ней автоматически пополняются из [сетевого хранилища](../ae2-mechanics/import-export-storage.md). Будьте осторожны, забирая результат с зажатым Shift: терминал продолжит пополнять сетку, пока хватает ингредиентов.

## Интерфейс

См. раздел [«МЭ-терминалы»](terminals.md).

## Улучшения

Беспроводной терминал изготовления поддерживает следующие [улучшения](upgrade_cards.md):

*   <ItemLink id="energy_card" /> — увеличивает ёмкость встроенной батареи.

## Рецепт

<RecipeFor id="wireless_crafting_terminal" />
