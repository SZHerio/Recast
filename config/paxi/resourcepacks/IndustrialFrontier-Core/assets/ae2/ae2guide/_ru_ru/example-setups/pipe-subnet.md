---
navigation:
  parent: example-setups/example-setups-index.md
  title: Подсеть-«труба» для предметов и жидкостей
  icon: storage_bus
---

# Подсеть-«труба» для предметов и жидкостей

Простой способ имитировать предметную или жидкостную трубу с помощью [устройств](../ae2-mechanics/devices.md) AE2. Такая
подсеть подходит для любых обычных задач трубы, включая возврат результата изготовления в
<ItemLink id="pattern_provider" />.

Обычно применяют один из двух способов.

## МЭ-шина импорта → МЭ-шина хранения

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/import_storage_pipe.snbt" />

<BoxAnnotation color="#dddddd" min="3.7 0 0" max="4 1 1">
        (1) МЭ-шина импорта: можно настроить фильтр.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 0 0" max="1.3 1 1">
        (2) МЭ-шина хранения: можно настроить фильтр. Эта шина и другие целевые шины хранения должны быть единственными
        хранилищами сети.
  </BoxAnnotation>

<DiamondAnnotation pos="4.5 0.5 0.5" color="#00ff00">
        Источник
    </DiamondAnnotation>

<DiamondAnnotation pos="0.5 0.5 0.5" color="#00ff00">
        Назначение
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

<ItemLink id="import_bus" /> (1) на исходном инвентаре импортирует предметы или жидкость и пытается поместить их в
[сетевое хранилище](../ae2-mechanics/import-export-storage.md). Единственное хранилище этой сети —
<ItemLink id="storage_bus" /> (2), поэтому ресурс оказывается в целевом инвентаре. Именно поэтому конструкция должна быть
подсетью, а не частью основной сети. Энергию передаёт <ItemLink id="quartz_fiber" />. Обе шины поддерживают фильтры; без
фильтров система переносит всё, к чему имеет доступ. Схема также работает с несколькими шинами импорта и хранения.

## МЭ-шина хранения → МЭ-шина экспорта

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/storage_export_pipe.snbt" />

<BoxAnnotation color="#dddddd" min="3.7 0 0" max="4 1 1">
        (1) МЭ-шина хранения: можно настроить фильтр. Эта шина и другие исходные шины хранения должны быть единственными
        хранилищами сети.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 0 0" max="1.3 1 1">
        (2) МЭ-шина экспорта: фильтр обязателен.
  </BoxAnnotation>

<DiamondAnnotation pos="4.5 0.5 0.5" color="#00ff00">
        Источник
    </DiamondAnnotation>

<DiamondAnnotation pos="0.5 0.5 0.5" color="#00ff00">
        Назначение
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

<ItemLink id="export_bus" /> на целевом инвентаре пытается извлечь из
[сетевого хранилища](../ae2-mechanics/import-export-storage.md) ресурсы, указанные в фильтре. Единственное хранилище сети —
<ItemLink id="storage_bus" />, поэтому предметы или жидкость извлекаются из исходного инвентаря и переносятся в целевой.
Именно поэтому конструкция должна быть подсетью, а не частью основной сети. Энергию передаёт
<ItemLink id="quartz_fiber" />. МЭ-шина экспорта не работает без фильтра, поэтому его настройка обязательна. Схема также
поддерживает несколько шин хранения и экспорта.

## Неработающая схема: МЭ-шина импорта → МЭ-шина экспорта

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/import_export_pipe.snbt" />

<BoxAnnotation color="#dd3333" min="3.7 0 0" max="4 1 1">
        МЭ-шина импорта: в сети нет хранилища, поэтому импортировать ресурсы некуда.
  </BoxAnnotation>

<BoxAnnotation color="#dd3333" min="1 0 0" max="1.3 1 1">
        (2) МЭ-шина экспорта: в сети нет хранилища, поэтому экспортировать нечего.
  </BoxAnnotation>

<DiamondAnnotation pos="4.5 0.5 0.5" color="#ff0000">
        Источник
    </DiamondAnnotation>

<DiamondAnnotation pos="0.5 0.5 0.5" color="#ff0000">
        Назначение
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

Конструкция только из шин импорта и экспорта не работает. Первая пытается извлечь ресурсы из исходного инвентаря и
поместить их в сетевое хранилище. Вторая пытается забрать ресурсы из сетевого хранилища и передать в целевой инвентарь.
Но в этой сети **нет хранилища**, поэтому одна шина не может импортировать, а другая — экспортировать. Ничего не происходит.

## Вход и выход через одну грань

Предположим, машина принимает ингредиенты и позволяет извлекать результат через одну грань, как
<ItemLink id="charger" />. Чтобы одновременно подавать ресурсы и забирать результат, объедините два способа построения
подсети-трубы.

<GameScene zoom="6" background="transparent">
  <ImportStructure src="../assets/assemblies/import_storage_export_pipe.snbt" />

<BoxAnnotation color="#dddddd" min="4 1 1" max="5 1.3 2">
        (1) МЭ-шина импорта: можно настроить фильтр.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="2 1 1" max="3 1.3 2">
        (2) МЭ-шина хранения: можно настроить фильтр. Эта шина и другие шины, через которые требуется передавать ресурсы
        в обоих направлениях, должны быть единственными хранилищами сети.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="2 0 1" max="3 1 2">
        (3) Машина для подачи и извлечения; в примере — Зарядник.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="0 1 1" max="1 1.3 2">
        (4) МЭ-шина экспорта: фильтр обязателен.
  </BoxAnnotation>

<DiamondAnnotation pos="4.5 0.5 1.5" color="#00ff00">
        Источник
    </DiamondAnnotation>

<DiamondAnnotation pos="0.5 0.5 1.5" color="#00ff00">
        Назначение
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Интерфейсы

Помимо шин импорта и экспорта, существуют и другие [устройства](../ae2-mechanics/devices.md), помещающие ресурсы в
[сетевое хранилище](../ae2-mechanics/import-export-storage.md) и извлекающие их. Здесь полезен
<ItemLink id="interface" />. Если вставить предмет, запас которого интерфейс не настроен поддерживать, он отправит этот
предмет в сетевое хранилище. Это поведение можно использовать как трубу «шина импорта → шина хранения». Если настроить
интерфейс на поддержание предмета в запасе, он будет забирать его из сетевого хранилища, как труба «шина хранения → шина
экспорта». Один интерфейс может поддерживать запас одних предметов и не поддерживать запас других. Так при необходимости
можно удалённо передавать ресурсы через шины хранения в обоих направлениях.

<GameScene zoom="6" background="transparent">
<ImportStructure src="../assets/assemblies/interface_pipes.snbt" />

<BoxAnnotation color="#dddddd" min="3.7 0 0" max="4 1 1">
        МЭ-интерфейс
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 0 0" max="1.3 1 1">
        МЭ-шина хранения
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="3.7 0 2" max="4 1 3">
        МЭ-шина хранения
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="0 1 2" max="1 1.3 3">
        МЭ-шина хранения
  </BoxAnnotation>

<IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Один ко многим, многие к одному и многие ко многим

Разумеется, система не ограничена одним экземпляром <ItemLink id="import_bus" />, <ItemLink id="export_bus" /> или
<ItemLink id="storage_bus" />.

<GameScene zoom="3" background="transparent">
<ImportStructure src="../assets/assemblies/many_to_many_pipe.snbt" />

<IsometricCamera yaw="185" pitch="30" />
</GameScene>

## Подача в несколько мест

На основе описанных принципов можно отправлять ингредиенты с одной грани <ItemLink id="pattern_provider" /> в несколько
точек: например, в ряд машин или на разные грани одной машины.

Трубы «импорт → хранение» и «хранение → экспорт» здесь не подходят, потому что ингредиенты никогда фактически не лежат в
<ItemLink id="pattern_provider" />. Поставщик *выталкивает* их в соседние инвентари, поэтому рядом нужен инвентарь, который
также умеет импортировать предметы.

Эту задачу решает <ItemLink id="interface" />. Убедитесь, что поставщик имеет направленную или плоскую кабельную форму
и/или интерфейс установлен как плоская кабельная часть. Иначе два компонента создадут сетевое соединение.

<GameScene zoom="6" background="transparent">
<ImportStructure src="../assets/assemblies/provider_interface_storage.snbt" />

<BoxAnnotation color="#dddddd" min="2.7 0 1" max="3 1 2">
        МЭ-интерфейс: обязательно плоский, не полноразмерный
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 0 0" max="1.3 1 4">
        МЭ-шины хранения
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="0 0 0" max="1 1 4">
        Точки, куда поставщик должен подавать шаблон: несколько машин или несколько граней одной машины
  </BoxAnnotation>

<IsometricCamera yaw="185" pitch="30" />
</GameScene>
