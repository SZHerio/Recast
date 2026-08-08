#!/usr/bin/env node
// Pure Node contract test. This does not start Minecraft, Forge or KubeJS.

const fs = require('fs')
const path = require('path')
const vm = require('vm')

class ListTag {
  constructor(values = []) {
    this.values = [...values]
  }
  add(value) {
    this.values.push(value)
  }
  size() {
    return this.values.length
  }
  remove(index) {
    return this.values.splice(index, 1)[0]
  }
  copy() {
    return new ListTag(this.values)
  }
}

function wrap(value) {
  if (value instanceof CompoundTag || value instanceof ListTag) return value
  if (Array.isArray(value)) return new ListTag(value.map(wrap))
  if (value && typeof value === 'object') return new CompoundTag(value)
  return value
}

class CompoundTag {
  constructor(initial = {}) {
    this.values = new Map(Object.entries(initial).map(([key, value]) => [key, wrap(value)]))
  }
  contains(key) {
    return this.values.has(key)
  }
  put(key, value) {
    this.values.set(key, wrap(value))
  }
  get(key) {
    return this.values.get(key)
  }
  putInt(key, value) {
    this.values.set(key, Number(value))
  }
  getInt(key) {
    return Number(this.values.get(key) || 0)
  }
  putBoolean(key, value) {
    this.values.set(key, Boolean(value))
  }
  getBoolean(key) {
    return Boolean(this.values.get(key))
  }
  putString(key, value) {
    this.values.set(key, String(value))
  }
  getString(key) {
    return String(this.values.get(key) || '')
  }
  copy() {
    const result = new CompoundTag()
    for (const [key, value] of this.values) {
      result.values.set(key, value && typeof value.copy === 'function' ? value.copy() : value)
    }
    return result
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

const completed = new Map()
const customCommands = new Map()
const log = []
const context = vm.createContext({
  Java: {
    loadClass(name) {
      if (name === 'dev.ftb.mods.ftbquests.quest.TeamData') {
        return {
          get(player) {
            return { getTeamId: () => player.teamId }
          },
        }
      }
      if (name === 'net.minecraft.nbt.StringTag') {
        return { valueOf: (value) => String(value) }
      }
      throw new Error(`Unexpected Java class in contract test: ${name}`)
    },
  },
  ServerEvents: {
    loaded() {},
    customCommand(name, callback) {
      customCommands.set(name, callback)
    },
  },
  FTBQuestsEvents: {
    completed(selector, callback) {
      completed.set(selector, callback)
    },
  },
  console: {
    info(message) {
      log.push(String(message))
    },
    error(message) {
      log.push(String(message))
    },
  },
})

const root = path.resolve(__dirname, '..')
for (const relative of [
  'kubejs/server_scripts/40_balance/m3_threat_director.js',
  'kubejs/server_scripts/10_progression/quest_commissioning_bridge.js',
]) {
  vm.runInContext(fs.readFileSync(path.join(root, relative), 'utf8'), context, { filename: relative })
}

assert(completed.size === 10, `expected 10 commissioning listeners, got ${completed.size}`)

const playersByName = new Map()
const server = {
  persistentData: new CompoundTag(),
  commands: [],
  getPlayerList() {
    return { getPlayerByName: (name) => playersByName.get(name) || null }
  },
  runCommandSilent(command) {
    this.commands.push(command)
  },
}
const messages = []
const player = {
  username: 'Engineer',
  uuid: '11111111-1111-1111-1111-111111111111',
  teamId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  tell(message) {
    messages.push(String(message))
  },
}
playersByName.set(player.username, player)

function completionEvent() {
  return {
    server,
    player,
    data: { getData: () => ({ getTeamId: () => player.teamId }) },
    onlineMembers: [player],
  }
}

// Helper calls stay in the original context so top-level const bindings remain visible.
context.server = server
context.player = player
const readEpoch = () => vm.runInContext("ifTeamStateForPlayer(server, player).getInt('tech_epoch')", context)

assert(readEpoch() === 0, 'new FTB Quests team must begin at P0')
completed.get('#if_commissioning_p0')(completionEvent())
assert(readEpoch() === 1, 'P0 commissioning must advance exactly to P1')
completed.get('#if_commissioning_p0')(completionEvent())
assert(readEpoch() === 1, 'replayed P0 event must be idempotent')
completed.get('#if_commissioning_p2')(completionEvent())
assert(readEpoch() === 1, 'out-of-order P2 event must not skip P1')
completed.get('#if_commissioning_p1')(completionEvent())
assert(readEpoch() === 2, 'P1 commissioning must advance to P2')

customCommands.get('if_advance_epoch')({ server, player })
assert(readEpoch() === 2, 'public custom_command recovery bypass must be inert')
vm.runInContext("ifAdminAdvanceEpoch(server, player, 'contract test')", context)
assert(readEpoch() === 3, 'operator recovery helper must advance exactly one epoch')

const teams = server.persistentData.get('industrial_frontier').get('teams')
assert(teams.contains(player.teamId), 'authoritative state must use the FTB Quests team UUID')
assert(!teams.contains(player.username), 'new state must not use username as persistent key')
const audit = server.persistentData.get('industrial_frontier').get('audit')
assert(audit.size() >= 5 && audit.size() <= 256, 'persistent audit must record transitions and respect its cap')

console.log('quest epoch bridge contract: PASS')
console.log('Minecraft/Forge/KubeJS were not started')
