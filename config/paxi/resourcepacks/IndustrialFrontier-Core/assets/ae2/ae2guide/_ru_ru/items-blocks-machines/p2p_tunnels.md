---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: P2P-туннели
  icon: me_p2p_tunnel
  position: 210
categories:
- devices
item_ids:
- ae2:me_p2p_tunnel
- ae2:redstone_p2p_tunnel
- ae2:item_p2p_tunnel
- ae2:fluid_p2p_tunnel
- ae2:fe_p2p_tunnel
- ae2:light_p2p_tunnel
---

# P2P-туннели

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/p2p_tunnels.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

P2P-туннели передают предметы, жидкости, редстоун-сигналы, энергию, свет и
[каналы](../ae2-mechanics/channels.md) через сеть, не смешивая передаваемый поток с содержимым самой сети. Существует
несколько разновидностей туннеля, и каждая передаёт только свой тип ресурса. По сути, туннель напрямую связывает две
грани блоков на расстоянии, как портал. Связь однонаправленная: у неё явно заданы вход и выход.

![Портал](../assets/assemblies/p2p_portal.png)

Например, воронка, направленная в предметный P2P-туннель, ведёт себя так, будто подключена непосредственно к бочке,
поэтому предметы будут перемещаться.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/p2p_hopper_barrel.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Однако две соседние бочки сами по себе не передают предметы друг другу.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/p2p_barrel_barrel.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Другие разновидности работают с иными потоками. Например, редстоуновый P2P-туннель передаёт редстоун-сигнал.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/p2p_redstone.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Типы P2P-туннелей и их настройка

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/p2p_tunnels.snbt" />
  <IsometricCamera yaw="180" pitch="90" />
</GameScene>

P2P-туннели бывают нескольких типов. Напрямую изготавливается только P2P-туннель МЭ. Чтобы настроить другой тип,
щёлкните правой кнопкой мыши по любому P2P-туннелю с подходящим предметом в руке:

- любой [кабель](../items-blocks-machines/cables.md) настраивает P2P-туннель МЭ;
- различные редстоун-компоненты настраивают редстоуновый P2P-туннель;
- сундук или воронка настраивают предметный P2P-туннель;
- ведро или бутылочка настраивают жидкостный P2P-туннель;
- почти любой предмет с запасом энергии настраивает энергетический P2P-туннель;
- факел или светокамень настраивает световой P2P-туннель.

У некоторых типов есть особые ограничения. Каналы P2P-туннеля МЭ нельзя провести через другой P2P-туннель МЭ.
Энергетический P2P-туннель косвенно удерживает 2,5 % проходящей через него энергии FE: именно на эту величину он
увеличивает собственное потребление [энергии](../ae2-mechanics/energy.md).

## Самое распространённое применение P2P

Чаще всего P2P-туннели МЭ используют для уплотнения потока [каналов](../ae2-mechanics/channels.md). Вместо нескольких
плотных кабелей множество каналов можно передать через одну компактную кабельную линию.

В этом примере 8 входов P2P МЭ принимают 256 каналов (8 × 32) от <ItemLink id="controller" /> основной сети, а 8 выходов
P2P МЭ выводят их в другом месте. Каждый вход и каждый выход P2P занимает по 1 каналу. Поэтому все эти каналы можно
провести через тонкий кабель. Более того, P2P-туннели находятся в отдельной [подсети](../ae2-mechanics/subnetworks.md),
так что не занимают ни одного канала основной сети. Туннели можно поставить вплотную к контроллеру, но промежуточный
[плотный умный кабель](../items-blocks-machines/cables.md#smart-cable) нагляднее показывает распределение каналов.

<GameScene zoom="4" interactive={true}>
  <ImportStructure src="../assets/assemblies/p2p_compact_channels.snbt" />

  <BoxAnnotation color="#dddddd" min="1.3 1.3 6.3" max="2 2.7 6.7">
        Кварцевое волокно передаёт энергию между основной сетью и P2P-подсетью.
  </BoxAnnotation>

  <IsometricCamera yaw="225" pitch="30" />
</GameScene>

Ещё один пример, в том числе с [квантовыми мостами](quantum_bridge.md), показан на этой простой схеме:

![P2P-туннели и квантовые мосты](../assets/diagrams/p2p_quantum_network.png)

## Вложение

Такая схема не позволяет передать бесконечное число каналов через один кабель. Канал, который питает P2P-туннель МЭ,
не проходит через другой P2P-туннель МЭ, поэтому рекурсивно вкладывать их нельзя. На сцене внешний слой P2P-туннелей МЭ
на красных кабелях отключён. Ограничение относится только к МЭ P2P-туннелям: туннели других типов могут проходить через
P2P-туннель МЭ. Это видно по исправной работе редстоуновых P2P-туннелей.

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/p2p_nesting.snbt" />
  <IsometricCamera yaw="225" pitch="30" />
</GameScene>

## Связывание

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/p2p_linking_frequency.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Концы P2P-соединения связываются с помощью <ItemLink id="memory_card" />. Частота связи отображается на задней стороне
туннеля в виде массива цветов 2x2.

- Shift + правая кнопка мыши: создать новую частоту связи P2P.
- Правая кнопка мыши: вставить настройки, карты улучшений или частоту связи.

Туннель, по которому вы щёлкнули с зажатой клавишей Shift, станет входом. Туннель, по которому вы затем щёлкнете правой
кнопкой мыши, станет выходом. К одному входу можно привязать несколько выходов, но P2P-туннели МЭ разделят входящие каналы
между ними: дублировать каналы нельзя.

## Рецепт

<RecipeFor id="me_p2p_tunnel" />
