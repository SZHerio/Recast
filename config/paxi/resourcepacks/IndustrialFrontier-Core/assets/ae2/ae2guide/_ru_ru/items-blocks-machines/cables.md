---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Кабели
  icon: fluix_glass_cable
  position: 110
categories:
- network infrastructure
item_ids:
- ae2:white_glass_cable
- ae2:orange_glass_cable
- ae2:magenta_glass_cable
- ae2:light_blue_glass_cable
- ae2:yellow_glass_cable
- ae2:lime_glass_cable
- ae2:pink_glass_cable
- ae2:gray_glass_cable
- ae2:light_gray_glass_cable
- ae2:cyan_glass_cable
- ae2:purple_glass_cable
- ae2:blue_glass_cable
- ae2:brown_glass_cable
- ae2:green_glass_cable
- ae2:red_glass_cable
- ae2:black_glass_cable
- ae2:fluix_glass_cable
- ae2:white_covered_cable
- ae2:orange_covered_cable
- ae2:magenta_covered_cable
- ae2:light_blue_covered_cable
- ae2:yellow_covered_cable
- ae2:lime_covered_cable
- ae2:pink_covered_cable
- ae2:gray_covered_cable
- ae2:light_gray_covered_cable
- ae2:cyan_covered_cable
- ae2:purple_covered_cable
- ae2:blue_covered_cable
- ae2:brown_covered_cable
- ae2:green_covered_cable
- ae2:red_covered_cable
- ae2:black_covered_cable
- ae2:fluix_covered_cable
- ae2:white_covered_dense_cable
- ae2:orange_covered_dense_cable
- ae2:magenta_covered_dense_cable
- ae2:light_blue_covered_dense_cable
- ae2:yellow_covered_dense_cable
- ae2:lime_covered_dense_cable
- ae2:pink_covered_dense_cable
- ae2:gray_covered_dense_cable
- ae2:light_gray_covered_dense_cable
- ae2:cyan_covered_dense_cable
- ae2:purple_covered_dense_cable
- ae2:blue_covered_dense_cable
- ae2:brown_covered_dense_cable
- ae2:green_covered_dense_cable
- ae2:red_covered_dense_cable
- ae2:black_covered_dense_cable
- ae2:fluix_covered_dense_cable
- ae2:white_smart_cable
- ae2:orange_smart_cable
- ae2:magenta_smart_cable
- ae2:light_blue_smart_cable
- ae2:yellow_smart_cable
- ae2:lime_smart_cable
- ae2:pink_smart_cable
- ae2:gray_smart_cable
- ae2:light_gray_smart_cable
- ae2:cyan_smart_cable
- ae2:purple_smart_cable
- ae2:blue_smart_cable
- ae2:brown_smart_cable
- ae2:green_smart_cable
- ae2:red_smart_cable
- ae2:black_smart_cable
- ae2:fluix_smart_cable
- ae2:white_smart_dense_cable
- ae2:orange_smart_dense_cable
- ae2:magenta_smart_dense_cable
- ae2:light_blue_smart_dense_cable
- ae2:yellow_smart_dense_cable
- ae2:lime_smart_dense_cable
- ae2:pink_smart_dense_cable
- ae2:gray_smart_dense_cable
- ae2:light_gray_smart_dense_cable
- ae2:cyan_smart_dense_cable
- ae2:purple_smart_dense_cable
- ae2:blue_smart_dense_cable
- ae2:brown_smart_dense_cable
- ae2:green_smart_dense_cable
- ae2:red_smart_dense_cable
- ae2:black_smart_dense_cable
- ae2:fluix_smart_dense_cable
---

# Кабели

<GameScene zoom="3" background="transparent">
  <ImportStructure src="../assets/assemblies/cables.snbt" />
  <IsometricCamera yaw="180" pitch="30" />
</GameScene>

МЭ-сеть может образоваться и между стоящими рядом совместимыми машинами, но именно кабели позволяют протянуть её на
большое расстояние.

Кабели разных цветов не соединяются друг с другом, даже если установлены вплотную. Это помогает эффективнее распределять
[каналы](../ae2-mechanics/channels.md). Цвет кабеля также меняет цвет подключённых терминалов, поэтому все терминалы не
обязательно делать фиолетовыми. Флюисовый кабель соединяется с кабелем любого цвета.

Обратите внимание: **КАНАЛЫ НИКАК НЕ СВЯЗАНЫ С ЦВЕТОМ КАБЕЛЯ**.

## Важное замечание

**Если вы только знакомитесь с AE2 и ещё не освоили каналы, по возможности используйте умный кабель и плотный умный
кабель. Они показывают путь каналов по сети и делают её работу нагляднее.**

## Ещё одно замечание

**Кабели не являются трубами для предметов, жидкостей, энергии или чего-либо ещё.** У них нет внутреннего инвентаря,
поставщики шаблонов и машины ничего в них не «выталкивают». Кабели лишь соединяют [устройства](../ae2-mechanics/devices.md)
AE2 в одну сеть.

## Стеклянный кабель

<GameScene zoom="6" background="transparent">
<ImportStructure src="../assets/assemblies/fluix_glass_cable.snbt" />
<IsometricCamera yaw="195" pitch="30" />
</GameScene>

<ItemLink id="fluix_glass_cable" /> — самый простой в изготовлении кабель. Он передаёт энергию и до 8
[каналов](../ae2-mechanics/channels.md). Кабель доступен в 17 цветах: исходный вариант имеет цвет Флюиса, а покрасить его
можно любым из 16 красителей.

Чтобы изготовить окрашенные кабели, окружите любой краситель 8 кабелями одного типа. Цвет этих кабелей не
имеет значения, но их тип должен совпадать: например, все кабели должны быть стеклянными или умными. Установленный в мире
кабель также можно покрасить любой кистью, совместимой с Forge.

Соедините окрашенный кабель с ведром воды, чтобы смыть краску.

Кабель можно покрыть шерстью и получить <ItemLink id="fluix_covered_cable" />. Изготовьте
<ItemLink id="fluix_smart_cable" />, если хотите наглядно видеть распределение [каналов](../ae2-mechanics/channels.md).

<RecipeFor id="fluix_glass_cable" />

<RecipeFor id="blue_glass_cable" />

## Покрытый кабель

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/fluix_covered_cable.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Покрытый кабель не даёт игровых преимуществ по сравнению с вариантом <ItemLink id="fluix_glass_cable" />. Выбирайте его,
если вам больше нравится закрытый внешний вид.

Он окрашивается так же, как <ItemLink id="fluix_glass_cable" />. Четыре <ItemLink id="fluix_covered_cable" /> можно
соединить с редстоуном и светокаменной пылью, чтобы изготовить <ItemLink id="fluix_covered_dense_cable" />.

<Recipe id="network/cables/covered_fluix" />

<RecipeFor id="blue_covered_cable" />

<a name="dense-cable" />

## Плотный кабель

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/fluix_covered_dense_cable.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Плотный кабель передаёт 32 канала, тогда как обычный — только 8. На плотный кабель нельзя устанавливать шины и панели,
поэтому перед ними необходимо перейти на кабель меньшего размера, например <ItemLink id="fluix_glass_cable" /> или
<ItemLink id="fluix_smart_cable" />.

Плотный кабель немного меняет правило «кратчайшего пути» для каналов: сначала канал выбирает кратчайший путь к плотному
кабелю, а затем — кратчайший путь по этому плотному кабелю до контроллера.

<Recipe id="network/cables/dense_covered_fluix" />

<RecipeFor id="blue_covered_dense_cable" />

<a name="smart-cable" />

## Умный кабель

<Row>
<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/fluix_smart_cable.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>
<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/fluix_smart_dense_cable.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>
</Row>

Внешне умный кабель похож на <ItemLink id="fluix_covered_cable" />, но дополнительно показывает загрузку каналов.
Задействованные каналы отображаются светящимися линиями вдоль чёрной полосы кабеля. У обычного умного кабеля первые
четыре канала показаны линиями цвета самого кабеля, а следующие четыре — белыми. У плотного умного кабеля каждая полоса
соответствует 4 каналам.

В сети с <ItemLink id="controller" /> линии на кабелях показывают точный путь каналов.

В автономной сети умный кабель показывает общее число занятых каналов во всей сети, а не число каналов, проходящих через
данный кабель.

Умные кабели окрашиваются так же, как <ItemLink id="fluix_glass_cable" />.

<Recipe id="network/cables/smart_fluix" />

<Recipe id="network/cables/dense_smart_fluix" />

<RecipeFor id="blue_smart_cable" />
