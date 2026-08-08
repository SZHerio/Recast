---
navigation:
  parent: example-setups/example-setups-index.md
  title: Автоматизация бросания в воду
  icon: fluix_crystal
---

# Автоматизация рецептов с бросанием в воду

Эта система использует <ItemLink id="pattern_provider" /> и предназначена для подключения к вашей системе
[автоматического изготовления](../ae2-mechanics/autocrafting.md).

Некоторые рецепты требуют бросить предметы в воду. Похожую конструкцию можно использовать и для выбрасывания предметов
в другие места. Процесс автоматизируют <ItemLink id="formation_plane" />, <ItemLink id="annihilation_plane" /> и
вспомогательная инфраструктура — фактически две изменённые [подсети-трубы](pipe-subnet.md).

Эта система рассчитана на совместную работу с [автоматизацией зарядника](charger-automation.md), которая предоставляет
<ItemLink id="charged_certus_quartz_crystal" />.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/throw_in_water.snbt" />

<BoxAnnotation color="#dddddd" min="2 0 1" max="3 1 2">
        (1) МЭ-поставщик шаблонов: стандартные настройки и нужные шаблоны обработки.

        ![Шаблон флюиса](../assets/diagrams/fluix_pattern_small.png) ![Шаблон потресканного цветущего блока](../assets/diagrams/flawed_budding_pattern_small.png)
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1.7 0 1" max="2 1 2">
        (2) МЭ-интерфейс: стандартные настройки.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 .7 1" max="2 1 2">
        (3) МЭ-плоскость формирования: настроена выбрасывать входные ресурсы как предметы.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 2 1" max="2 2.3 2">
        (4) МЭ-плоскость уничтожения: интерфейса настроек нет.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="2 1 1" max="3 1.3 2">
        (5) МЭ-шина хранения: фильтр настроен на результаты шаблонов.
        <Row><ItemImage id="fluix_crystal" scale="2" /><BlockImage id="flawless_budding_quartz" scale="2" /></Row>
  </BoxAnnotation>

<DiamondAnnotation pos="3.9 0.5 1.5" color="#00ff00">
        К основной сети и автоматизации зарядника
        <GameScene zoom="3" background="transparent">
          <ImportStructure src="../assets/assemblies/charger_automation.snbt" />
          <IsometricCamera yaw="195" pitch="30" />
        </GameScene>
    </DiamondAnnotation>

  <IsometricCamera yaw="180" pitch="0" />
</GameScene>

## Настройки и шаблоны

* <ItemLink id="pattern_provider" /> (1) использует стандартные настройки и содержит нужные
  <ItemLink id="processing_pattern" />.
  * Для <ItemLink id="fluix_crystal" /> подходит стандартный рецепт из JEI:

    ![Шаблон флюиса](../assets/diagrams/fluix_pattern.png)

  * <ItemLink id="flawed_budding_quartz" /> лучше изготавливать непосредственно из <ItemLink id="quartz_block" />.
    Так вход одного рецепта не будет одновременно выходом другого, из-за чего шина хранения не смогла бы правильно
    фильтровать ресурсы:

    ![Шаблон потресканного цветущего блока](../assets/diagrams/flawed_budding_pattern.png)

* <ItemLink id="interface" /> (2) использует стандартные настройки.
* <ItemLink id="formation_plane" /> (3) настроена выбрасывать входные ресурсы как предметы.
* У <ItemLink id="annihilation_plane" /> (4) нет интерфейса настроек.
* Фильтр <ItemLink id="storage_bus" /> (5) настроен на результаты шаблонов.

## Принцип работы

1.  <ItemLink id="pattern_provider" /> отправляет ингредиенты в расположенный сбоку <ItemLink id="interface" /> зелёной
    подсети.
2.  Интерфейс со стандартной пустой конфигурацией запаса пытается поместить содержимое в
    [сетевое хранилище](../ae2-mechanics/import-export-storage.md).
3.  Единственное хранилище зелёной подсети — <ItemLink id="formation_plane" />, поэтому плоскость выбрасывает полученные
    предметы в воду.
4.  <ItemLink id="annihilation_plane" /> оранжевой подсети пытается подобрать выброшенные предметы, но пока не может.
    <ItemLink id="storage_bus" /> сверху МЭ-поставщика шаблонов — единственное хранилище оранжевой подсети — принимает по
    фильтру только возможные результаты рецептов.
5.  Предметы преобразуются в мире.
6.  После преобразования плоскость уничтожения может подобрать предметы перед собой, поскольку шине хранения разрешено
    их сохранять.
7.  Шина хранения помещает результаты в МЭ-поставщик шаблонов, возвращая их в сеть.
