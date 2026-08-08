---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: МЭ-интерфейс
  icon: interface
  position: 210
categories:
- devices
item_ids:
- ae2:interface
- ae2:cable_interface
---

# МЭ-интерфейс

<Row gap="20">
<BlockImage id="interface" scale="8" />
<GameScene zoom="8" background="transparent">
  <ImportStructure src="../assets/blocks/cable_interface.snbt" />
</GameScene>
</Row>

МЭ-интерфейс работает как небольшой сундук и резервуар, который пополняется из
[сетевого хранилища](../ae2-mechanics/import-export-storage.md) или опустошается в него согласно запасам, заданным в
верхних слотах. Интерфейс старается выполнить перенос за один игровой такт и способен заполнить или освободить до 9 стопок
за такт. С быстрыми предметными трубами это даёт высокую скорость импорта и экспорта.

Большинство резервуаров хранит только 1 тип жидкости, а интерфейс вмещает до 9 типов одновременно и вдобавок принимает
предметы. По сути, это сундук и многожидкостный резервуар с дополнительными функциями. Чтобы отключить эти функции,
достаточно не подключать блок ни к одной сети. Поэтому интерфейс полезен в редких схемах, где нужно держать небольшой запас
многих разных ресурсов.

## Внутреннее устройство интерфейса

Как уже говорилось, интерфейс похож на сундук и резервуар, к которым подключены особо быстрые <ItemLink id="import_bus" />,
<ItemLink id="export_bus" /> и множество <ItemLink id="level_emitter" />.

<GameScene zoom="3" interactive={true}>
  <ImportStructure src="../assets/assemblies/interface_internals.snbt" />

  <BoxAnnotation color="#dddddd" min="1.3 0.3 1.3" max="9.7 1 1.7">
        Набор излучателей уровня контролирует запрошенный объём запаса
        <GameScene zoom="4" background="transparent">
        <ImportStructure src="../assets/blocks/level_emitter.snbt" />
        </GameScene>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1.3 4 1.3" max="9.7 4.7 1.7">
        Набор излучателей уровня контролирует запрошенный объём запаса
        <GameScene zoom="4" background="transparent">
        <ImportStructure src="../assets/blocks/level_emitter.snbt" />
        </GameScene>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1.3 1.3 1.3" max="9.7 2 1.7">
        Набор особо быстрых шин импорта передаёт по 1 стопке за игровой такт
        <GameScene zoom="4" background="transparent">
        <ImportStructure src="../assets/blocks/import_bus.snbt" />
        </GameScene>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1.3 3 1.3" max="9.7 3.7 1.7">
        Набор особо быстрых шин экспорта передаёт по 1 стопке за игровой такт
        <GameScene zoom="4" background="transparent">
        <ImportStructure src="../assets/blocks/export_bus.snbt" />
        </GameScene>
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1 2 1" max="10 3 2">
        9 отдельных внутренних слотов
  </BoxAnnotation>

  <IsometricCamera yaw="195" pitch="15" />
</GameScene>

<a name="special-interactions" />

## Особые взаимодействия

Интерфейс также особым образом взаимодействует с некоторыми [устройствами](../ae2-mechanics/devices.md) AE2.

Если <ItemLink id="storage_bus" /> установлен на ненастроенном интерфейсе, он открывает своей сети доступ ко всему
[сетевому хранилищу](../ae2-mechanics/import-export-storage.md) сети интерфейса. Для шины это выглядит так, будто интерфейс —
один большой сундук. Если задать поддерживаемый запас в слотах фильтра интерфейса, такое взаимодействие отключается.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/interface_storage.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Поставщик шаблонов особым образом взаимодействует с интерфейсом в [подсети](../ae2-mechanics/subnetworks.md). Если
интерфейс не настроен, поставщик пропускает его и передаёт ингредиенты напрямую в [хранилище](../ae2-mechanics/import-export-storage.md)
подсети. Интерфейс не заполняется партиями рецепта, а следующая партия не поступает, пока в хранилище не освободится место.

<GameScene zoom="6" background="transparent">
<ImportStructure src="../assets/assemblies/provider_interface_storage.snbt" />

<BoxAnnotation color="#dddddd" min="2.7 0 1" max="3 1 2">
        МЭ-интерфейс (обязательно плоская версия, не полный блок)
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 0 0" max="1.3 1 4">
        Шины хранения
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="0 0 0" max="1 1 4">
        Механизмы, которые должны получать ингредиенты шаблонов: несколько механизмов или несколько граней 1 механизма
  </BoxAnnotation>

<IsometricCamera yaw="185" pitch="30" />
</GameScene>

## Варианты

Интерфейс существует в 2 вариантах: обычном и плоском, то есть в виде
[кабельной части](../ae2-mechanics/cable-subparts.md). Вариант определяет, с каких сторон доступен инвентарь и через какие
грани блок предоставляет сетевое соединение.

*   Обычный интерфейс позволяет помещать и извлекать ресурсы, а также обращаться к инвентарю со всех сторон. Подобно
    большинству механизмов AE2, он работает как кабель и предоставляет сетевое соединение на каждой грани.

*   Плоские интерфейсы относятся к [кабельным частям](../ae2-mechanics/cable-subparts.md), поэтому на одном кабеле можно
    разместить несколько таких блоков и собрать компактную схему. Ресурсы можно помещать, извлекать и просматривать через
    лицевую сторону, но сетевого соединения на этой стороне нет.

Обычный и плоский варианты можно взаимно преобразовывать в сетке изготовления.

## Настройки

Верхние слоты задают ресурсы, запас которых интерфейс должен поддерживать внутри себя. Когда вы помещаете туда предмет
или перетаскиваете его из JEI, появляется значок гаечного ключа для настройки количества.

Чтобы выбрать жидкость вместо содержащего её ведра или резервуара, щёлкните по интерфейсу правой кнопкой мыши с этой ёмкостью в руке.

## Улучшения

Интерфейс поддерживает следующие [улучшения](upgrade_cards.md):

*   <ItemLink id="fuzzy_card" /> позволяет учитывать степень повреждения предмета или игнорировать его NBT.
*   <ItemLink id="crafting_card" /> разрешает интерфейсу отправлять запросы в систему
    [автоматического изготовления](../ae2-mechanics/autocrafting.md). Сначала интерфейс попытается забрать нужные предметы
    из хранилища и только при их отсутствии запросит изготовление новых.

## Приоритет

Чтобы задать приоритет, нажмите значок гаечного ключа в правом верхнем углу интерфейса. Интерфейс с более высоким
приоритетом получает нужные предметы раньше интерфейса с меньшим приоритетом.

## Рецепты

<Recipe id="network/blocks/interfaces_interface" />

<RecipeFor id="cable_interface" />
