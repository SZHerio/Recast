const fs = require('fs')

const root = 'C:/Users/SZHerio/curseforge/minecraft/Instances/main1.20/'
const instance = JSON.parse(fs.readFileSync(root + 'minecraftinstance.json', 'utf8').replace(/^\uFEFF/, ''))

// CurseForge App не знает про моды, удалённые из папки руками: его метаданные
// продолжают их перечислять. Манифест обязан описывать то, что лежит в mods/,
// иначе импорт архива вернёт удалённое обратно.
const present = new Set(fs.readdirSync(root + 'mods').filter((n) => n.endsWith('.jar')))

const files = (instance.installedAddons || [])
  .filter((addon) => addon.addonID && addon.installedFile && addon.installedFile.id)
  .filter((addon) => present.has(addon.installedFile.fileName))
  .map((addon) => ({
    projectID: addon.addonID,
    fileID: addon.installedFile.id,
    required: true
  }))
  .sort((a, b) => a.projectID - b.projectID)

const manifest = {
  minecraft: {
    version: '1.20.1',
    modLoaders: [{ id: instance.baseModLoader.name, primary: true }]
  },
  manifestType: 'minecraftModpack',
  manifestVersion: 1,
  name: 'Recast',
  version: 'IF-M5-0001',
  author: 'SZHerio',
  files: files,
  overrides: 'overrides'
}

fs.writeFileSync(root + 'manifest.json', JSON.stringify(manifest, null, 2) + '\n')
console.log('модов в манифесте:', files.length, '| загрузчик:', instance.baseModLoader.name)

// Сверка с реальной папкой: манифест обязан объяснять каждый JAR, кроме
// зарегистрированного исключения.
const jars = fs.readdirSync(root + 'mods').filter((n) => n.endsWith('.jar'))
const named = new Set((instance.installedAddons || []).map((a) => a.installedFile && a.installedFile.fileName))
const unlisted = jars.filter((n) => !named.has(n))
console.log('JAR в папке:', jars.length, '| не описаны манифестом:', JSON.stringify(unlisted))
