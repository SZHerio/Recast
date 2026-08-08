---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: МЭ-контроллер
  icon: controller
  position: 110
categories:
- network infrastructure
item_ids:
- ae2:controller
---

# МЭ-контроллер

<BlockImage id="controller" p:state="online" scale="8" />

МЭ-контроллер служит узлом маршрутизации [МЭ-сети](../ae2-mechanics/me-network-connections.md). Без него сеть считается импровизированной и может содержать суммарно не более 8 [устройств](../ae2-mechanics/devices.md), использующих каналы.

В одной [МЭ-сети](../ae2-mechanics/me-network-connections.md) нельзя разместить 2 отдельных контроллера.

Каждая грань контроллера предоставляет 32 [канала](../ae2-mechanics/channels.md).

Для работы каждый блок контроллера потребляет 6 AE/t и способен хранить 8 000 AE. Поэтому крупной сети может понадобиться дополнительное энергохранилище. Подробности приведены [на странице об энергии](../ae2-mechanics/energy.md).

Многоблочный контроллер допускает довольно свободную форму.

<GameScene zoom="2" background="transparent">
  <ImportStructure src="../assets/assemblies/controllers.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Однако необходимо соблюдать несколько правил:

1.  Все блоки контроллера в [МЭ-сети](../ae2-mechanics/me-network-connections.md) должны быть соединены. Иначе они загорятся красным.
2.  Контроллер должен помещаться в объём 7x7x7. При превышении размера он загорится красным.
3.  У блока контроллера могут быть 2 соседних блока максимум по 1 оси. Нарушивший это правило блок отключится и загорится красным.

<GameScene zoom="2" background="transparent">
  <ImportStructure src="../assets/assemblies/controller_rules.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Если контроллер получает питание и все правила соблюдены, он светится и переливается разными цветами.

Щелчок ПКМ по контроллеру открывает то же окно, что и <ItemLink id="network_tool" />.

## Рецепт

<RecipeFor id="controller" />
