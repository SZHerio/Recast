---
navigation:
  parent: ae2-mechanics/ae2-mechanics-index.md
  title: Каналы
  icon: controller
---

# Каналы

[МЭ-сетям](me-network-connections.md) Applied Energistics 2 требуются каналы для поддержки
[устройств](../ae2-mechanics/devices.md), использующих сетевое хранилище или другие сетевые службы. Каналы можно
представить как USB-провода к устройствам: у компьютера ограничено число портов, поэтому он поддерживает лишь определённое
число подключений. Большинство машин, полноразмерных устройств и обычных кабелей могут передавать не более восьми
каналов. Считайте такой блок или кабель пучком из восьми «проводов каналов». [Плотные
кабели](../items-blocks-machines/cables.md#dense-cable) поддерживают до 32 каналов. Среди других устройств 32 канала могут
передавать только <ItemLink id="me_p2p_tunnel" /> и [МЭ-квантовый
мост](../items-blocks-machines/quantum_bridge.md). Когда устройство занимает канал, один «провод» из пучка расходуется и
становится недоступен дальше по линии.

<GameScene zoom="7" interactive={true}>
  <ImportStructure src="../assets/assemblies/channel_demonstration_1.snbt" />

  <LineAnnotation color="#33ff33" from="1 .4 .7" to="2.4 .4 .7" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="1 .6 .7" to="2.4 .6 .7" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="1 .4 .6" to="2.6 .4 .6" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="1 .6 .6" to="2.6 .6 .6" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="1 .6 .6" to="2.6 .6 .6" alwaysOnTop={true}/>

  <LineAnnotation color="#33ff33" from="2.4 .6 .7" to="2.4 .6 1.5" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="2.4 .4 .7" to="2.4 .4 1.5" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="2.6 .6 .6" to="2.6 .6 1.5" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="2.6 .4 .6" to="2.6 .4 1.5" alwaysOnTop={true}/>

  <LineAnnotation color="#33ff33" from="2.1 .6 1.5" to="2.4 .6 1.5" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="2.6 .4 1.5" to="2.9 .4 1.5" alwaysOnTop={true}/>

  <LineAnnotation color="#33ff33" from="2.6 .6 1.5" to="2.6 .9 1.5" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="2.4 .1 1.5" to="2.4 .4 1.5" alwaysOnTop={true}/>

  <LineAnnotation color="#33ff33" from="1 .6 .4" to="3.5 .6 .4" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="1 .4 .4" to="3.5 .4 .4" alwaysOnTop={true}/>

  <LineAnnotation color="#33ff33" from="3.5 .6 .4" to="3.5 .9 .4" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="3.5 .1 .4" to="3.5 .4 .4" alwaysOnTop={true}/>

  <LineAnnotation color="#33ff33" from="1 .6 .3" to="1.5 .6 .3" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="1 .4 .3" to="1.5 .4 .3" alwaysOnTop={true}/>

  <LineAnnotation color="#33ff33" from="1.5 .6 .3" to="1.5 .9 .3" alwaysOnTop={true}/>
  <LineAnnotation color="#33ff33" from="1.5 .1 .3" to="1.5 .4 .3" alwaysOnTop={true}/>

  <LineAnnotation color="#ff3333" from="3.5 .5 .5" to="5.5 .5 .5" alwaysOnTop={true}>
  Все восемь каналов кабеля заняты, поэтому МЭ-накопителю канал не достаётся.
  </LineAnnotation>

  <LineAnnotation color="#993333" from="1 .5 .5" to="1.25 .5 .5" alwaysOnTop={true}/>
  <LineAnnotation color="#993333" from="1.5 .5 .5" to="1.75 .5 .5" alwaysOnTop={true}/>
  <LineAnnotation color="#993333" from="2 .5 .5" to="2.25 .5 .5" alwaysOnTop={true}/>
  <LineAnnotation color="#993333" from="2.5 .5 .5" to="2.75 .5 .5" alwaysOnTop={true}/>
  <LineAnnotation color="#993333" from="3 .5 .5" to="3.25 .5 .5" alwaysOnTop={true}/>

  <DiamondAnnotation pos="3.6 0.5 0.5" color="#ff0000">
        Все восемь каналов кабеля заняты, поэтому МЭ-накопителю канал не достаётся.
    </DiamondAnnotation>

  <IsometricCamera yaw="15" pitch="30" />
</GameScene>

[Умные кабели](../items-blocks-machines/cables.md) показывают маршруты и занятость каналов, поэтому с их помощью проще
понять, как сеть распределяет каналы.

Каждый узел, через который проходит канал, потребляет 1⁄128 AE/т. Поэтому после добавления
<ItemLink id="controller" /> в сеть с восемью устройствами и более чем 96 узлами потребление энергии может даже
уменьшиться: контроллер меняет способ распределения каналов.

Важно: **КАНАЛЫ НИКАК НЕ СВЯЗАНЫ С ЦВЕТОМ КАБЕЛЯ**. Цвет лишь запрещает соединение кабелей разных цветов.

<a name="channel-routing" />

## Маршрутизация каналов

При наличии <ItemLink id="controller" /> каналы прокладываются в три этапа. Сначала выбирается кратчайший путь через
соседние машины к ближайшему [обычному кабелю](../items-blocks-machines/cables.md): стеклянному, покрытому или умному.
Затем выбирается кратчайший путь по обычному кабелю к ближайшему [плотному
кабелю](../items-blocks-machines/cables.md), обычному или умному. Наконец, по плотному кабелю строится кратчайший путь к
<ItemLink id="controller" />. Если кратчайший путь уже достиг предельной пропускной способности, некоторые
[устройства](devices.md) не получат необходимые каналы. Используйте цвета кабелей, кабельные якоря и тоннели, чтобы
ограничить возможные пути и направить каналы по нужному маршруту.

В следующем примере части накопителей не хватает каналов. Общая пропускная способность кабелей достаточна, но каналы
выбирают кратчайшие пути: одни кабели перегружаются, а другие остаются пустыми.

<GameScene zoom="4" interactive={true}>
  <ImportStructure src="../assets/assemblies/channel_path_length_issue.snbt" />

  <LineAnnotation color="#33ff33" from="3 .5 1.4" to="0.4 0.5 1.4" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#33ff33" from="0.4 .5 1.4" to="0.4 0.5 3.6" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#33ff33" from="0.4 0.5 3.6" to="1.4 0.5 3.6" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#33ff33" from="1.4 0.5 3.6" to="1.4 0.5 5" alwaysOnTop={true} thickness="0.05"/>

  <LineAnnotation color="#33ff33" from="3 0.5 3.6" to="1.6 0.5 3.6" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#33ff33" from="1.6 0.5 3.6" to="1.6 0.5 5" alwaysOnTop={true} thickness="0.05"/>

  <LineAnnotation color="#ff3333" from="3 .5 1.6" to="0.6 .5 1.6" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#ff3333" from="0.6 .5 1.6" to="0.6 .5 3.4" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#ff3333" from="0.6 .5 3.4" to="1.4 .5 3.4" alwaysOnTop={true} thickness="0.05"/>

  <LineAnnotation color="#ff3333" from="3 .5 3.4" to="1.6 .5 3.4" alwaysOnTop={true} thickness="0.05"/>

  <BoxAnnotation color="#dddddd" min="1.2 0.2 3.2" max="1.8 0.8 3.8" alwaysOnTop={true} thickness="0.05">
        Через это место пытаются пройти более восьми каналов, поэтому часть из них обрывается.
  </BoxAnnotation>

  <IsometricCamera yaw="90" pitch="90" />

</GameScene>

Проблема решается более строгим ограничением доступных маршрутов. Сеть должна напоминать дерево или куст. Сведите к
минимуму петли и участки с неоднозначным выбором пути.

<GameScene zoom="4" interactive={true}>
  <ImportStructure src="../assets/assemblies/channel_path_length_issue_fix.snbt" />

  <LineAnnotation color="#33ff33" from="3 .5 1.4" to="0.4 0.5 1.4" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#33ff33" from="0.4 .5 1.4" to="0.4 0.5 5.6" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#33ff33" from="0.4 0.5 5.6" to="1 0.5 5.6" alwaysOnTop={true} thickness="0.05"/>

  <LineAnnotation color="#33ff33" from="3 0.5 3.6" to="1.6 0.5 3.6" alwaysOnTop={true} thickness="0.05"/>
  <LineAnnotation color="#33ff33" from="1.6 0.5 3.6" to="1.6 0.5 5" alwaysOnTop={true} thickness="0.05"/>

  <IsometricCamera yaw="90" pitch="90" />

</GameScene>

## Сети без контроллера

Сеть без <ItemLink id="controller" /> считается автономной и поддерживает не более восьми устройств, использующих
каналы. Если подключить больше восьми, все использующие каналы устройства отключатся. Удалите лишние устройства либо
добавьте <ItemLink id="controller" />.

В отличие от сети с контроллером, [умный кабель](../items-blocks-machines/cables.md) автономной сети показывает общее число
занятых каналов во всей сети, а не число каналов, проходящих через конкретный кабель.

В автономной сети каждое устройство занимает один канал во всей сети. Это заметно отличается от работы
<ItemLink id="controller" />, который распределяет каналы по кратчайшим маршрутам.

## Проектирование

Как сказано в разделе [о маршрутизации](channels.md#channel-routing), сеть лучше строить в виде дерева. Плотные кабели
ответвляются от контроллера, обычные кабели — от плотных, а [устройства](../ae2-mechanics/devices.md) подключаются к обычным
кабелям группами не более чем по восемь.

Ниже показан пример неудачной структуры.

Проследим пути каналов:

1. Сразу справа от контроллера возникает узкое место на восемь каналов: накопитель действует как обычный кабель. Умного
кабеля здесь нет, поэтому увидеть число занятых каналов невозможно. Остаётся восемь каналов.
2. Накопитель занимает один канал. Остаётся семь.
3. Два канала уходят вверх к терминалам. Остаётся пять.
4. Дальше справа ещё один канал занимает интерфейс. Остаётся четыре.
5. Один канал уходит вверх к поставщику шаблонов. Остаётся три.
6. Дальше справа один канал уходит вверх к шине импорта. Остаётся два.
7. Группа поставщиков шаблонов, питающих сборщики, получает лишь два канала, поэтому двум поставщикам каналов не хватает.

Основная ошибка — узкое место в каналах и отсутствие расчёта их дальнейшего распределения.

<GameScene zoom="4" interactive={true}>
  <ImportStructure src="../assets/assemblies/bad_network_structure.snbt" />

<LineAnnotation color="#33ff33" from="6.5 .5 1.5" to="6 .5 1.5" alwaysOnTop={true} thickness="0.4">
  32 канала
</LineAnnotation>

<LineAnnotation color="#33ff33" from="6 .5 1.5" to="5.5 .5 1.5" alwaysOnTop={true} thickness="0.2">
  8 каналов
</LineAnnotation>

<LineAnnotation color="#33ff33" from="5.5 .5 1.5" to="5.5 1.5 1.5" alwaysOnTop={true} thickness="0.1">
  2 канала
</LineAnnotation>

<LineAnnotation color="#33ff33" from="5.5 .5 1.5" to="5.5 .3 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="5.5 1.5 1.5" to="5.5 2.5 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="5.5 2.5 1.5" to="5.5 2.5 1.1" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="5.5 .5 1.5" to="4.5 .5 1.5" alwaysOnTop={true} thickness="0.158">
  5 каналов
</LineAnnotation>

<LineAnnotation color="#33ff33" from="4.5 .5 1.5" to="4.5 .3 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="4.5 .5 1.5" to="4.5 1.5 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="4.5 .5 1.5" to="3.5 .5 1.5" alwaysOnTop={true} thickness="0.122">
  3 канала
</LineAnnotation>

<LineAnnotation color="#33ff33" from="3.5 .5 1.5" to="3.5 2.5 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="3.5 2.5 1.5" to="3.7 2.5 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="3.5 .5 1.5" to="1.5 .5 1.5" alwaysOnTop={true} thickness="0.1">
  2 канала
</LineAnnotation>

<LineAnnotation color="#33ff33" from="1.5 0.5 1.5" to="1.5 0.3 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="1.5 0.5 1.5" to="0.5 0.5 1.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#33ff33" from="0.5 0.5 1.5" to="0.5 0.5 0.5" alwaysOnTop={true} thickness="0.071">
  1 канал
</LineAnnotation>

<LineAnnotation color="#ff3333" from="0.5 1.5 1.5" to="0.5 1.3 1.5" alwaysOnTop={true} thickness="0.071">
  нет каналов
</LineAnnotation>

<LineAnnotation color="#ff3333" from="1.5 1.5 0.5" to="1.5 1.3 0.5" alwaysOnTop={true} thickness="0.071">
  нет каналов
</LineAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

---

Ниже показан пример удачной структуры.

<GameScene zoom="2.5" interactive={true}>
  <ImportStructure src="../assets/assemblies/treelike_network_structure.snbt" />

    <BoxAnnotation color="#dddddd" min="6.9 0 4.9" max="9.1 4 7.1" thickness="0.05">
        Обратите внимание: поставщики шаблонов разделены на группы по восемь.
    </BoxAnnotation>

    <BoxAnnotation color="#dddddd" min="5 4 4" max="8 5 5" thickness="0.05">
        Если сходятся два обычных кабеля с полностью занятыми каналами, здесь требуется плотный кабель.
    </BoxAnnotation>

    <BoxAnnotation color="#dddddd" min="5 0 13" max="8 1 14" thickness="0.05">
        Разные цвета не позволяют соседним кабелям соединиться.
    </BoxAnnotation>


  <IsometricCamera yaw="315" pitch="30" />
</GameScene>

## Режимы каналов

В AE2 10.0.0 для Minecraft 1.18 появились настройки поведения каналов в мире. Параметр `channels` в общем разделе
конфигурации выбирает режим. Оператор также может изменить режим и конфигурацию прямо в игре. Команда
`/ae2 channelmode <mode>` устанавливает режим, а `/ae2 channelmode` показывает текущее значение. После изменения режима
в игре все существующие сети перезапускаются и сразу переходят на новые правила.

Эта возможность возвращает и расширяет настройку из Minecraft 1.12. Она предоставляет более спокойные варианты игры,
не требуя полностью удалять механику каналов.

В таблице перечислены значения, доступные и в файле конфигурации, и в команде.

| Значение   | Описание                                                                                                                                                                                                                                  |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `default`  | Стандартный режим с пропускной способностью кабелей и автономных сетей, описанной в этом руководстве.                                                                                                                                      |
| `x2`       | Вся пропускная способность удвоена: 16 каналов в обычном кабеле, 64 в плотном, автономная сеть поддерживает 16.                                                                                                                            |
| `x3`       | Вся пропускная способность утроена: 24 канала в обычном кабеле, 96 в плотном, автономная сеть поддерживает 24.                                                                                                                             |
| `x4`       | Вся пропускная способность увеличена вчетверо: 32 канала в обычном кабеле, 128 в плотном, автономная сеть поддерживает 32.                                                                                                                 |
| `infinite` | Все ограничения каналов сняты. Контроллеры по-прежнему *значительно* снижают энергопотребление сетей. Умные кабели показывают только два состояния: полностью выключен — не передаёт каналы; включён — передаёт один или несколько каналов. |
