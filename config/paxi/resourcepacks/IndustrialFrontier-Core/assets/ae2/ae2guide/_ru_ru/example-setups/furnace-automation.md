---
navigation:
  parent: example-setups/example-setups-index.md
  title: Автоматизация печи
  icon: minecraft:furnace
---

# Автоматизация печи

Эта система использует <ItemLink id="pattern_provider" /> и предназначена для подключения к вашей системе
[автоматического изготовления](../ae2-mechanics/autocrafting.md). Если требуется отдельно автоматизировать печь,
достаточно воронок, сундуков и других обычных средств перемещения предметов.

Автоматизировать <ItemLink id="minecraft:furnace" /> немного сложнее, чем простую машину вроде
[зарядника](../example-setups/charger-automation.md). Печь принимает ресурсы с двух разных сторон, а результат отдаёт через
третью. Переплавляемый предмет подаётся сверху, топливо — сбоку, а результат извлекается снизу.

Сверху можно установить <ItemLink id="pattern_provider" />, сбоку — <ItemLink id="export_bus" /> для постоянной подачи
топлива, а снизу — <ItemLink id="import_bus" /> для возврата результатов в сеть. Однако такая схема занимает три
[канала](../ae2-mechanics/channels.md).

Ниже показан вариант всего с одним каналом.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/furnace_automation.snbt" />

<BoxAnnotation color="#dddddd" min="1 0 0" max="2 1 1">
        (1) МЭ-поставщик шаблонов: направленный вариант, созданный с помощью Гаечного ключа из истинного кварца;
        содержит нужные шаблоны обработки.

        ![Шаблон железа](../assets/diagrams/furnace_pattern_small.png)
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 1 0" max="2 1.3 1">
        (2) МЭ-интерфейс: стандартные настройки.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 1 0" max="1.3 2 1">
        (3) МЭ-шина хранения № 1: фильтр настроен на уголь.
        <ItemImage id="minecraft:coal" scale="2" />
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="0 2 0" max="1 2.3 1">
        (4) МЭ-шина хранения № 2: с помощью Карты-инвертера настроен чёрный список угля.
        <Row><ItemImage id="minecraft:coal" scale="2" /><ItemImage id="inverter_card" scale="2" /></Row>
  </BoxAnnotation>

<DiamondAnnotation pos="4 0.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* <ItemLink id="pattern_provider" /> (1) использует стандартные настройки и содержит нужные
  <ItemLink id="processing_pattern" />. Примените к поставщику <ItemLink id="certus_quartz_wrench" />, чтобы сделать его
  направленным.

  ![Шаблон железа](../assets/diagrams/furnace_pattern.png)

* <ItemLink id="interface" /> (2) использует стандартные настройки.
* Фильтр первой <ItemLink id="storage_bus" /> (3) настройте на уголь либо другое выбранное топливо.
* В фильтре второй <ItemLink id="storage_bus" /> (4) с помощью <ItemLink id="inverter_card" /> внесите выбранное топливо
  в чёрный список.

## Принцип работы

1. <ItemLink id="pattern_provider" /> отправляет ингредиенты в <ItemLink id="interface" />. В действительности система
   оптимизирует путь и передаёт их прямо через шины хранения, как будто те продолжают грани поставщика. В сам интерфейс
   предметы не попадают.
2. Интерфейс не настроен на внутренний запас, поэтому пытается отправить ингредиенты в
   [сетевое хранилище](../ae2-mechanics/import-export-storage.md).
3. Единственные хранилища зелёной подсети — <ItemLink id="storage_bus" />. Шина с фильтром на уголь помещает топливо в
   топливный слот через боковую грань печи. Шина с чёрным списком угля помещает переплавляемые предметы в верхний слот
   через верхнюю грань.
4. Печь выполняет переплавку.
5. Воронка извлекает результат снизу печи и помещает его в возвратные слоты поставщика, возвращая в основную сеть.
