---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Ячейка просмотра
  icon: view_cell
  position: 410
categories:
- tools
item_ids:
- ae2:view_cell
---

# Ячейка просмотра

<ItemImage id="view_cell" scale="2" />

Ячейка просмотра фильтрует список ресурсов в [МЭ-терминалах](terminals.md). Её содержимое настраивается в <ItemLink id="cell_workbench" />.

Например, терминал должен показывать только выбранные каменные материалы для строительства. Добавьте эти материалы в фильтр ячейки просмотра и установите её в терминал — все остальные ресурсы исчезнут из списка.

Фильтры нескольких ячеек складываются. Если одна ячейка настроена на дубовые доски, а другая — на булыжник, при одновременной установке терминал покажет и доски, и булыжник.

## Рецепт

<Recipe id="network/cells/view_cell_storage" />

<Recipe id="network/cells/view_cell" />
