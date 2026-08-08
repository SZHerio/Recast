---
navigation:
  parent: items-blocks-machines/items-blocks-machines-index.md
  title: Зарядник
  icon: charger
  position: 310
categories:
- machines
item_ids:
- ae2:charger
---

# Зарядник

<BlockImage id="charger" scale="8" />

Зарядник позволяет заряжать поддерживаемые инструменты и <ItemLink id="certus_quartz_crystal" />.

Энергию можно подать сверху или снизу через [кабели](cables.md) AE2 либо энергетические кабели других модов. Зарядник
принимает как энергию AE2 (AE), так и Forge Energy (FE). Предметы можно подавать и забирать с любой стороны. Извлечь можно
только готовый результат, поэтому фильтр, защищающий незаряженные кристаллы от преждевременного извлечения, не нужен.
Для удобства автоматизации зарядник поворачивается с помощью <ItemLink id="certus_quartz_wrench" />.

С помощью зарядника можно получить <ItemLink id="charged_certus_quartz_crystal" /> из
<ItemLink id="certus_quartz_crystal" />, а <ItemLink id="meteorite_compass" /> — из
<ItemLink id="minecraft:compass" />.

Для ручного питания установите <ItemLink id="crank" /> сверху или снизу и нажимайте по рукояти правой кнопкой мыши, пока
предмет не зарядится.

Зарядник также служит рабочим местом для жителя AE2.

## Простая автоматизация

Возможность поворачивать зарядник позволяет частично автоматизировать его, например так:

<GameScene zoom="4" background="transparent">
  <ImportStructure src="../assets/assemblies/charger_hopper.snbt" />
  <IsometricCamera yaw="195" pitch="30" />
</GameScene>

## Рецепт

<RecipeFor id="charger" />
