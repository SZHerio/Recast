---
navigation:
  parent: example-setups/example-setups-index.md
  title: Автоматизация зарядника
  icon: charger
---

# Автоматизация зарядника

Эта система использует <ItemLink id="pattern_provider" /> и предназначена для подключения к вашей системе
[автоматического изготовления](../ae2-mechanics/autocrafting.md). Если требуется отдельно автоматизировать
<ItemLink id="charger" />, достаточно воронок, сундуков и других обычных средств перемещения предметов.

Автоматизировать <ItemLink id="charger" /> просто. <ItemLink id="pattern_provider" /> отправляет ингредиент в зарядник, а
[подсеть-труба](pipe-subnet.md) или другая предметная труба возвращает результат в поставщик.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/charger_automation.snbt" />

<BoxAnnotation color="#dddddd" min="1 0 0" max="2 1 1">
        (1) МЭ-поставщик шаблонов: стандартные настройки и нужные шаблоны обработки. Он также питает зарядник энергией.

        ![Шаблон зарядника](../assets/diagrams/charger_pattern_small.png)
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="0 1 0" max="1 1.3 1">
        (2) МЭ-шина импорта: стандартные настройки.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 1 0" max="2 1.3 1">
        (3) МЭ-шина хранения: стандартные настройки.
  </BoxAnnotation>

<DiamondAnnotation pos="4 0.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* <ItemLink id="pattern_provider" /> (1) использует стандартные настройки и содержит нужные
  <ItemLink id="processing_pattern" />. Он также передаёт [энергию](../ae2-mechanics/energy.md) в
  <ItemLink id="charger" />, поскольку действует как [кабель](../items-blocks-machines/cables.md).

    ![Шаблон зарядника](../assets/diagrams/charger_pattern.png)

* <ItemLink id="import_bus" /> (2) использует стандартные настройки.
* <ItemLink id="storage_bus" /> (3) использует стандартные настройки.

## Принцип работы

1. <ItemLink id="pattern_provider" /> отправляет ингредиенты в <ItemLink id="charger" />.
2. Зарядник выполняет операцию зарядки.
3. <ItemLink id="import_bus" /> зелёной подсети извлекает результат из зарядника и пытается поместить его в
   [сетевое хранилище](../ae2-mechanics/import-export-storage.md).
4. Единственное хранилище зелёной подсети — <ItemLink id="storage_bus" />. Оно помещает результат в МЭ-поставщик шаблонов,
   тем самым возвращая его в основную сеть.
