---
navigation:
  parent: example-setups/example-setups-index.md
  title: Автоподдержание запаса интерфейсами
  icon: interface
---

# Автоподдержание запаса интерфейсами

Как поддерживать заданное количество разных предметов и по мере необходимости изготавливать новые?

Один из вариантов — использовать <ItemLink id="interface" /> вместе с <ItemLink id="crafting_card" />. Интерфейс будет
автоматически запрашивать недостающие предметы у системы [автоматического
изготовления](../ae2-mechanics/autocrafting.md). Эта схема лучше подходит для небольших запасов множества разных предметов.

Демонстрационная конструкция укорочена, чтобы сцена не получилась слишком широкой. На практике выгодно использовать четыре
<ItemLink id="interface" /> и четыре <ItemLink id="storage_bus" />, заняв все восемь
[каналов](../ae2-mechanics/channels.md) обычного [кабеля](../items-blocks-machines/cables.md).

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/interface_autostocking.snbt" />

<BoxAnnotation color="#dddddd" min="0 0 0" max="2 1 1">
        (1) Интерфейсы: настроены на поддержание запаса нужных предметов и содержат Карты изготовления.
        <ItemImage id="crafting_card" scale="2" />
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="0 1 0" max="2 1.3 1">
        (2) МЭ-шины хранения: для параметра «Режим ввода/вывода» выбрано «Только извлекать».
  </BoxAnnotation>

<DiamondAnnotation pos="4 0.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* В <ItemLink id="interface" /> (1) задайте предметы, запас которых нужно поддерживать. Щёлкните нужным предметом по
  верхнему слоту или перетащите его туда из JEI, затем нажмите значок гаечного ключа над слотами и укажите количество.
  В каждый интерфейс установите <ItemLink id="crafting_card" />.
* В <ItemLink id="storage_bus" /> (2) установите для параметра «Режим ввода/вывода» значение «Только извлекать».

## Принцип работы

1. Если <ItemLink id="interface" /> не может получить из
   [сетевого хранилища](../ae2-mechanics/import-export-storage.md) достаточное количество настроенного предмета и содержит
   <ItemLink id="crafting_card" />, он запрашивает изготовление недостающего количества у системы
   [автоматического изготовления](../ae2-mechanics/autocrafting.md).
2. <ItemLink id="storage_bus" /> предоставляет сети доступ к содержимому интерфейсов.
