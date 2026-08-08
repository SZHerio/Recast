---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Беспроводная точка доступа
  icon: wireless_access_point
  position: 210
categories:
- devices
item_ids:
- ae2:wireless_booster
- ae2:wireless_access_point
---

# Беспроводная точка доступа

<BlockImage id="wireless_access_point" p:state="has_channel" scale="8" />

Предоставляет беспроводной доступ к сети через <ItemLink id="wireless_terminal" />. Дальность связи и расход энергии зависят от числа установленных <ItemLink id="wireless_booster" />.

В одной сети может работать любое число точек доступа, а в каждой из них — любое число <ItemLink id="wireless_booster" />. Меняя их расположение и количество, можно подобрать нужный баланс дальности и энергопотребления.

Точке доступа требуется [канал](../ae2-mechanics/channels.md).

Она также используется для привязки [беспроводных терминалов](wireless_terminals.md) к сети.

# Беспроводной усилитель

<ItemImage id="wireless_booster" scale="2" />

Увеличивает дальность беспроводной точки доступа.

## Рецепты

<RecipeFor id="wireless_access_point" />

<RecipeFor id="wireless_booster" />
