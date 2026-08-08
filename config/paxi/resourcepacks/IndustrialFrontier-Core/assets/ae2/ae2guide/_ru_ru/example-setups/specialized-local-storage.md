---
navigation:
  parent: example-setups/example-setups-index.md
  title: Специализированное локальное хранилище
  icon: drive
---

# Специализированное локальное хранилище

Одно из [особых взаимодействий МЭ-интерфейса](../items-blocks-machines/interface.md#special-interactions) позволяет
[подсети](../ae2-mechanics/subnetworks.md) предоставить основной сети содержимое своего хранилища. При этом подсеть не
получает доступа к хранилищу основной сети, а вся конструкция занимает лишь один [канал](../ae2-mechanics/channels.md).

Схема полезна для локального хранилища при ферме: её продукция не будет переполнять основное хранилище.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/local_storage.snbt" />

<BoxAnnotation color="#dddddd" min="4 0 0" max="5 2 1">
        (1) Любой способ импорта предметов; в примере используется МЭ-интерфейс.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="3 0 0" max="4 1 1">
        (2) МЭ-накопитель: содержит ячейки с фильтрами на продукцию фермы. В ячейки можно установить Карты равномерного
        распределения и Пустотные карты.
        <Row><ItemImage id="item_storage_cell_4k" scale="2" /> <ItemImage id="equal_distribution_card" scale="2" /> <ItemImage id="void_card" scale="2" /></Row>
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="3 1 0" max="4 2 0.3">
        (3) МЭ-терминал изготовления: видит содержимое накопителя подсети, но не хранилище основной сети.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="2 0 0" max="2.3 1 1">
        (4) МЭ-интерфейс № 2: стандартные настройки.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1.7 0 0" max="2 1 1">
        (5) МЭ-шина хранения: приоритет выше основного хранилища; фильтр можно настроить на продукцию фермы.
  </BoxAnnotation>

<BoxAnnotation color="#dddddd" min="1 1 0" max="2 2 0.3">
        МЭ-терминал изготовления: видит содержимое и основной сети, и подсети.
  </BoxAnnotation>

<DiamondAnnotation pos="0 0.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* Первый <ItemLink id="interface" /> (1) принимает предметы от фермы и отправляет их в подсеть.
* В <ItemLink id="drive" /> (2) установлены [ячейки](../items-blocks-machines/storage_cells.md). На верстаке для камер
  [распределите их на разделы](../items-blocks-machines/cell_workbench.md) по видам продукции фермы. В ячейки можно
  установить <ItemLink id="equal_distribution_card" /> и <ItemLink id="void_card" />.
* Второй <ItemLink id="interface" /> (4) использует стандартные настройки.
* [Приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) <ItemLink id="storage_bus" /> выше, чем у
  основного хранилища. Фильтр шины можно настроить на продукцию фермы.

## Принцип работы

* <ItemLink id="interface" /> подсети показывает <ItemLink id="storage_bus" /> основной сети содержимое
  <ItemLink id="drive" />. Поэтому шина может напрямую помещать предметы в ячейки накопителя и извлекать их.
* Высокий [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) шины хранения заставляет систему
  возвращать предметы в подсеть, а не отправлять их в основное хранилище.
* Важно: когда ячейки подсети заполнятся, предметы не начнут перетекать в основную сеть. Если остановка при заполнении
  ломает работу фермы, <ItemLink id="void_card" /> может удалять лишние предметы.
* Если ферма производит несколько видов предметов, <ItemLink id="equal_distribution_card" /> не позволит одному виду
  заполнить все ячейки и вытеснить остальные.
