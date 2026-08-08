---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: МЭ-порт ввода-вывода
  icon: io_port
  position: 210
categories:
- devices
item_ids:
- ae2:io_port
---

# МЭ-порт ввода-вывода

<BlockImage id="io_port" p:powered="true" scale="8" />

МЭ-порт ввода-вывода быстро переносит содержимое [ячеек хранения](../items-blocks-machines/storage_cells.md) в
[сетевое хранилище](../ae2-mechanics/import-export-storage.md) или, наоборот, заполняет ячейки из сети.

Блок можно повернуть с помощью <ItemLink id="certus_quartz_wrench" />.

## Настройки

*   Порт можно настроить так, чтобы ячейка переходила в выходные слоты после опустошения, заполнения или завершения операции.
*   После установки <ItemLink id="redstone_card" /> появляются режимы управления для разных состояний редстоун-сигнала.
*   Стрелка в центре интерфейса задаёт направление переноса: из ячейки в
    [сетевое хранилище](../ae2-mechanics/import-export-storage.md) или из хранилища в ячейку.

## Улучшения

МЭ-порт ввода-вывода поддерживает следующие [улучшения](upgrade_cards.md):

*   <ItemLink id="speed_card" /> увеличивает объём ресурса, переносимый за одну операцию.
*   <ItemLink id="redstone_card" /> добавляет управление редстоун-сигналом: работу при сильном или слабом сигнале либо одну операцию на импульс.

## Рецепт

<RecipeFor id="io_port" />
