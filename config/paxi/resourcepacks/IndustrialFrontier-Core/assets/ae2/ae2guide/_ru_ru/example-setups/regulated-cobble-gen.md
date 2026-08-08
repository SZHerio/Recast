---
navigation:
  parent: example-setups/example-setups-index.md
  title: Регулируемый генератор булыжника
  icon: minecraft:cobblestone
---

# Регулируемый генератор булыжника

Автоматизировать генератор булыжника просто: направьте <ItemLink id="annihilation_plane" /> на обычный ручной генератор
из Minecraft. Однако без регулирования сеть рано или поздно полностью заполнится булыжником.

МЭ-плоскость уничтожения действует подобно <ItemLink id="import_bus" />, поэтому нельзя просто направить
<ItemLink id="level_emitter" /> на <ItemLink id="export_bus" /> с <ItemLink id="redstone_card" />. Нельзя передать ресурс
непосредственно от импорта к экспорту, если между ними нет хранилища. Потребуется обходная схема.

<ItemLink id="toggle_bus" /> подключает и отключает части сети по сигналу редстоуна, но каждое переключение перезагружает
сеть. Простое решение — установить шину переключения в [подсети](../ae2-mechanics/subnetworks.md), чтобы перезагружалась
только она.

Автономная [подсеть](../ae2-mechanics/subnetworks.md) из <ItemLink id="annihilation_plane" /> и
<ItemLink id="storage_bus" /> может отправлять булыжник в <ItemLink id="interface" /> основной сети. Шина переключения
будет соединять подсеть с <ItemLink id="quartz_fiber" /> и разъединять их, отключая питание плоскостей.

<GameScene zoom="4" interactive={true}>
  <ImportStructure src="../assets/assemblies/regulated_cobble_gen.snbt" />

<BoxAnnotation color="#dddddd" min="3 2 2" max="7 2.3 3">
        (1) МЭ-плоскости уничтожения: интерфейса настроек нет; чары «Эффективность» и «Прочность» уменьшают
        энергопотребление.
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2 2 2" max="2.3 3 3">
        (2) МЭ-шина хранения: стандартные настройки.
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.3 2.3 2" max="2.7 2.7 2.3">
        (3) МЭ-шина переключения: крайне важно установить её в подсети, а не в основной сети.
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2.3 3 2.3" max="2.7 3.3 2.7">
        (4) МЭ-излучатель уровня: заданы булыжник и нужное количество; выбран режим «Излучать, когда уровни находятся
        ниже предела».
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1 2 3" max="2 3 2">
        (5) МЭ-интерфейс: стандартные настройки.
  </BoxAnnotation>

<DiamondAnnotation pos="0 2.5 1.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

<DiamondAnnotation pos="5 1.5 3.5" color="#00ff00">
        Затопленные ступени удерживают воду на месте и не дают ей превратить лаву в обсидиан.
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* У <ItemLink id="annihilation_plane" /> (1) нет интерфейса настроек. Чары «Эффективность» и «Прочность» уменьшают
  энергопотребление.
* <ItemLink id="storage_bus" /> (2) использует стандартные настройки.
* <ItemLink id="toggle_bus" /> (3) обязательно установите со стороны подсети от Кварцевого волокна, а не в основной сети.
  Иначе при каждом переключении будет перезагружаться основная сеть.
* В <ItemLink id="level_emitter" /> (4) задайте булыжник и нужное количество, затем выберите «Излучать, когда уровни
  находятся ниже предела».
* <ItemLink id="interface" /> (5) использует стандартные настройки.

## Принцип работы

1. Генератор создаёт булыжник.
2. <ItemLink id="annihilation_plane" /> разрушает булыжник.
3. <ItemLink id="storage_bus" /> помещает булыжник в <ItemLink id="interface" />, отправляя его в основную сеть.
4. Когда запас булыжника в основной сети превышает заданное значение, <ItemLink id="level_emitter" /> прекращает
   подавать сигнал и выключает <ItemLink id="toggle_bus" />.
5. Подсеть лишается питания, и плоскости уничтожения прекращают работу.
