---
navigation:
  parent: ae2-mechanics/ae2-mechanics-index.md
  title: Сетевые соединения
  icon: fluix_glass_cable
---

# Сетевые соединения

## Что означает «сеть»?

«Сеть» — это группа [устройств](../ae2-mechanics/devices.md), соединённых блоками, которые передают
[каналы](../ae2-mechanics/channels.md): [кабелями](../items-blocks-machines/cables.md), полноразмерными машинами или
[устройствами](../ae2-mechanics/devices.md), например <ItemLink id="charger" />, <ItemLink id="interface" /> и
<ItemLink id="drive" />. Строго говоря, даже один кабель уже является сетью.

## О расположении устройств

Физическое положение [устройства](../ae2-mechanics/devices.md) с определённой сетевой функцией не имеет значения. Это
относится, например, к <ItemLink id="interface" />, который помещает ресурсы в
[сетевое хранилище](../ae2-mechanics/import-export-storage.md) и извлекает их; к <ItemLink id="level_emitter" />,
считывающему содержимое сетевого хранилища; или к <ItemLink id="drive" />, предоставляющему это хранилище.

Ещё раз: **физическое положение устройства не имеет значения**. Важно лишь, чтобы оно было подключено к сети — и именно
к той сети, с которой должно работать.

## Сетевые соединения

Понять состав сети проще всего с помощью <ItemLink id="network_tool" />. Инструмент показывает каждый компонент сети.
Если в списке есть лишнее или отсутствует ожидаемое устройство, соединение устроено неправильно.

Например, ниже показаны две отдельные сети.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/2_networks_1.snbt" />

  <BoxAnnotation color="#915dcd" min="0 0 0" max="1 2 2">
        Сеть 1
  </BoxAnnotation>

<BoxAnnotation color="#915dcd" min="2 0 0" max="3 2 2">
        Сеть 2
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Следующая схема тоже содержит две отдельные сети: <ItemLink id="quartz_fiber" /> передаёт
[энергию](../ae2-mechanics/energy.md), но не создаёт сетевого соединения.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/2_networks_2.snbt" />

  <BoxAnnotation color="#915dcd" min="0 0 0" max="1 2 2">
        Сеть 1
  </BoxAnnotation>

  <BoxAnnotation color="#915dcd" min="1.3 0 0" max="3 2 2">
        Сеть 2
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

А здесь находится одна сеть, а не две. [Квантовый мост](../items-blocks-machines/quantum_bridge.md) действует как
беспроводной [плотный кабель](../items-blocks-machines/cables.md#dense-cable), поэтому обе стороны принадлежат одной сети.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/actually_1_network.snbt" />

  <BoxAnnotation color="#915dcd" min="0 0 0" max="7 3 3">
        Всё это одна сеть
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Следующая схема также представляет одну сеть. Цвет [кабеля](../items-blocks-machines/cables.md) влияет на соединение только
тем, что кабели разных цветов не стыкуются друг с другом. Кабель любого цвета соединяется с флюисовым, то есть
«неокрашенным», кабелем.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/actually_1_network_2.snbt" />

  <BoxAnnotation color="#915dcd" min="0 0 0" max="4 2 2">
        Всё это одна сеть
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Неочевидные соединения

Ниже снова показана одна сеть. Полноразмерный <ItemLink id="pattern_provider" /> действует подобно кабелю, как и
<ItemLink id="inscriber" />. Поэтому сетевое соединение проходит сквозь поставщик и вырезатель.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/pattern_provider_network_connection_1.snbt" />

  <BoxAnnotation color="#915dcd" min="0 0 0" max="4 2 2">
        Всё это одна сеть
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Чтобы разорвать такое соединение — это полезно во многих системах автоматического изготовления с
[подсетями](../ae2-mechanics/subnetworks.md), — щёлкните по поставщику правой кнопкой мыши, держа
<ItemLink id="certus_quartz_wrench" />. Поставщик станет направленным и перестанет передавать каналы через одну сторону.

<Row gap="40">
<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/pattern_provider_network_connection_2.snbt" />

  <BoxAnnotation color="#915dcd" min="0 0 0" max="2 2 2">
        Сеть 1
  </BoxAnnotation>

  <BoxAnnotation color="#915dcd" min="2 0 0" max="4 2 2">
        Сеть 2
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/pattern_provider_directional_connection.snbt" />

  <BoxAnnotation color="#ee3333" min="1 .3 .3" max="1.3 .7 .7">
        Обратите внимание: кабель не соединяется
  </BoxAnnotation>

  <IsometricCamera yaw="255" pitch="30" />
</GameScene>
</Row>

Другие компоненты, не передающие сетевое соединение через своё направление, — большинство [кабельных
частей](../ae2-mechanics/cable-subparts.md), включая такие [устройства](../ae2-mechanics/devices.md), как
<ItemLink id="import_bus" />, <ItemLink id="storage_bus" /> и <ItemLink id="cable_interface" />.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/subpart_no_connection.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>
