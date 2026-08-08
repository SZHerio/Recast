---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Процессор изготовления (хранилище, сопроцессор, монитор, блок)
  icon: 1k_crafting_storage
  position: 210
categories:
- devices
item_ids:
- ae2:1k_crafting_storage
- ae2:4k_crafting_storage
- ae2:16k_crafting_storage
- ae2:64k_crafting_storage
- ae2:256k_crafting_storage
- ae2:crafting_accelerator
- ae2:crafting_monitor
- ae2:crafting_unit
---

# Процессор изготовления

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/crafting_cpus.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

<Row>
  <BlockImage id="1k_crafting_storage" scale="4" />

  <BlockImage id="crafting_accelerator" scale="4" />

  <BlockImage id="crafting_monitor" scale="4" />

  <BlockImage id="crafting_unit" scale="4" />
</Row>

Процессор изготовления управляет заказами и заданиями автоматического изготовления. Во время многоэтапной работы он хранит промежуточные ингредиенты, определяет максимальный размер задания и в некоторой степени влияет на скорость выполнения. Подробнее см. раздел [«Автоматическое изготовление»](../ae2-mechanics/autocrafting.md).

Каждый процессор одновременно обслуживает 1 заказ или задание. Например, чтобы параллельно заказать вычислительный процессор и 256 блоков гладкого камня, понадобятся 2 многоблочных процессора.

Процессор можно настроить на заказы игроков, на заказы автоматических устройств — МЭ-шин экспорта и МЭ-интерфейсов — либо на оба источника.

Щелчок ПКМ по любому блоку процессора открывает окно состояния, где можно проверить ход текущего задания.

## Настройки

*   Процессор может принимать заказы только от игроков, только от автоматических устройств — например, от <ItemLink id="export_bus" /> с <ItemLink id="crafting_card" /> — либо от обоих источников.

## Постройка

Процессор изготовления — многоблочная установка в форме сплошного прямоугольного параллелепипеда без промежутков. Она собирается из нескольких видов компонентов.

Каждый процессор должен содержать как минимум 1 блок хранилища для изготовления. Минимальный рабочий вариант состоит лишь из одного хранилища для изготовления на 1K.

# Блок процессора изготовления

<BlockImage id="crafting_unit" scale="4" />

Необязательный блок процессора заполняет свободное место, чтобы установка оставалась сплошным прямоугольным параллелепипедом, когда других компонентов не хватает. Он также служит основой для их изготовления.

<RecipeFor id="crafting_unit" />

<a name="crafting-storage" />

# Хранилище для изготовления

<Row>
  <BlockImage id="1k_crafting_storage" scale="4" />

  <BlockImage id="4k_crafting_storage" scale="4" />

  <BlockImage id="16k_crafting_storage" scale="4" />

  <BlockImage id="64k_crafting_storage" scale="4" />

  <BlockImage id="256k_crafting_storage" scale="4" />
</Row>

Обязательные хранилища выпускаются во всех стандартных размерах ячеек: 1K, 4K, 16K, 64K и 256K. Они содержат исходные и промежуточные ингредиенты заказа. Чем больше ингредиентов требуется заданию, тем больше или вместительнее должны быть хранилища процессора.

<Column>
  <Row>
    <RecipeFor id="1k_crafting_storage" />

    <RecipeFor id="4k_crafting_storage" />

    <RecipeFor id="16k_crafting_storage" />
  </Row>

  <Row>
    <RecipeFor id="64k_crafting_storage" />

    <RecipeFor id="256k_crafting_storage" />
  </Row>
</Column>

# Сопроцессор

<BlockImage id="crafting_accelerator" scale="4" />

Необязательные сопроцессоры позволяют системе чаще отправлять партии ингредиентов из <ItemLink id="pattern_provider" />. Это помогает не отставать от быстрых механизмов. Например, поставщик шаблонов, окружённый <ItemLink id="molecular_assembler" />, может выдавать ингредиенты быстрее, чем один сборщик успевает их обработать. Тогда партии распределяются между окружающими сборщиками.

<RecipeFor id="crafting_accelerator" />

# Монитор изготовления

<BlockImage id="crafting_monitor" scale="4" />

Необязательный монитор показывает задание, которое процессор выполняет в данный момент. Экран можно окрасить с помощью <ItemLink id="color_applicator" />.

<RecipeFor id="crafting_monitor" />
