---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: МЭ-шина переключения
  icon: toggle_bus
  position: 110
categories:
- network infrastructure
item_ids:
- ae2:toggle_bus
- ae2:inverted_toggle_bus
---

# МЭ-шина переключения

<GameScene zoom="8" background="transparent">
<ImportStructure src="../assets/assemblies/toggle_bus.snbt" />
<IsometricCamera yaw="195" pitch="30" />
</GameScene>

Эта шина работает подобно <ItemLink id="fluix_glass_cable" /> и другим кабелям, но её соединение можно включать и выключать сигналом красного камня. Так можно отсоединять целую часть [МЭ-сети](../ae2-mechanics/me-network-connections.md).

При наличии сигнала обычная шина включает соединение. <ItemLink id="inverted_toggle_bus" /> действует наоборот и при наличии сигнала отключает его.

Учтите: переключение может вызвать перезапуск сети и повторный расчёт подключённых устройств.

Обе шины являются [частями кабеля](../ae2-mechanics/cable-subparts.md).

## Рецепты

<RecipeFor id="toggle_bus" />

<RecipeFor id="inverted_toggle_bus" />
