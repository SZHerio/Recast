---
navigation:
  parent: example-setups/example-setups-index.md
  title: Ферма аметиста
  icon: minecraft:amethyst_shard
---

# Ферма аметиста

<ItemLink id="growth_accelerator" /> действует на аметист, но обычный способ фильтрации
[почек истинного кварца](../items-blocks-machines/budding_certus.md) с помощью <ItemLink id="annihilation_plane" /> для
аметиста не подходит. Незрелая почка истинного кварца оставляет <ItemLink id="certus_quartz_dust" />, а незрелая почка
аметиста не оставляет ничего. МЭ-плоскость уничтожения всегда сможет её сломать, потому что сеть всегда может сохранить
«ничего».

Решение — наложить на МЭ-плоскость уничтожения «Шёлковое касание». Тогда незрелые почки аметиста начинают оставлять
предметы — блоки соответствующих стадий почки, — и их можно отфильтровать.

После этого <ItemLink id="minecraft:amethyst_cluster" /> нужно снова разместить с помощью
<ItemLink id="formation_plane" /> и повторно разрушить другой <ItemLink id="annihilation_plane" />, уже без «Шёлкового
касания». Так система получит <ItemLink id="minecraft:amethyst_shard" />.

Друза имеет направление, поэтому прямо напротив МЭ-плоскости формирования должна находиться твёрдая грань блока.

<GameScene zoom="6" interactive={true}>
  <ImportStructure src="../assets/assemblies/amethyst_farm.snbt" />

  <BoxAnnotation color="#dddddd" min="2.7 1 1" max="3 2 2">
        (1) МЭ-плоскость уничтожения № 1: интерфейса настроек нет, наложены чары «Шёлковое касание».
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="2 1 1" max="2.3 2 2">
        (2) МЭ-плоскость формирования: фильтр настроен на Аметистовую друзу.
        <ItemImage id="minecraft:amethyst_cluster" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1.3 0.7 1" max="2 1 2">
        (3) МЭ-плоскость уничтожения № 2: интерфейса настроек нет, можно наложить чары «Удача».
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="1 0 1" max="1.3 1 2">
        (4) МЭ-шина хранения № 1: фильтр настроен на Осколок аметиста.
        <ItemImage id="minecraft:amethyst_shard" scale="2" />
  </BoxAnnotation>

  <BoxAnnotation color="#dddddd" min="0 0 .7" max="1 1 1">
        (5) МЭ-шина хранения № 2: фильтр настроен на Осколок аметиста, приоритет выше основного хранилища.
        <ItemImage id="minecraft:amethyst_shard" scale="2" />
  </BoxAnnotation>

<DiamondAnnotation pos="0 0.5 0.5" color="#00ff00">
        К основной сети
    </DiamondAnnotation>

  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Настройки

* У первой <ItemLink id="annihilation_plane" /> (1) нет интерфейса настроек; на неё обязательно наложите
  «Шёлковое касание».
* Фильтр <ItemLink id="formation_plane" /> (2) настройте на <ItemLink id="minecraft:amethyst_cluster" />.
* У второй <ItemLink id="annihilation_plane" /> (3) нет интерфейса настроек, но на неё можно наложить «Удачу».
* Фильтр первой <ItemLink id="storage_bus" /> (4) настройте на <ItemLink id="minecraft:amethyst_shard" />.
* Фильтр второй <ItemLink id="storage_bus" /> (5) настройте на <ItemLink id="minecraft:amethyst_shard" />, а её
  [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) установите выше приоритета основного хранилища.

## Принцип работы

1. Первая <ItemLink id="annihilation_plane" /> пытается разрушить блок перед собой, но может разрушить только
   <ItemLink id="minecraft:amethyst_cluster" />. Единственное хранилище подсети — <ItemLink id="formation_plane" /> с
   фильтром на аметистовую друзу. Это работает только благодаря «Шёлковому касанию»: без него незрелая почка не оставляет
   предмета, поэтому плоскость тоже смогла бы её разрушить.
2. <ItemLink id="formation_plane" /> размещает друзу на блоке напротив себя.
3. Вторая <ItemLink id="annihilation_plane" /> разрушает друзу и получает <ItemLink id="minecraft:amethyst_shard" />.
4. Первая <ItemLink id="storage_bus" /> помещает осколки в бочку. Строго говоря, фильтр здесь необязателен, поскольку
   второй плоскости уничтожения должны встречаться только полностью выросшие друзы.
5. Вторая <ItemLink id="storage_bus" /> предоставляет основной сети доступ ко всем осколкам аметиста в бочке. Высокий
   [приоритет](../ae2-mechanics/import-export-storage.md#storage-priority) заставляет систему возвращать осколки в эту
   бочку, а не отправлять их в основное хранилище.
