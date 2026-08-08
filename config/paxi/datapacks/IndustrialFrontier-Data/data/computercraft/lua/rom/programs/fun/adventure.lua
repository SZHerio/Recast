-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tBiomes = {
    "\226 \235\229\241\243",
    "\226 \241\238\241\237\238\226\238\236 \235\229\241\243",
    "\239\238 \234\238\235\229\237\238 \226 \225\238\235\238\242\229",
    "\241\240\229\228\232 \227\238\240",
    "\226 \239\243\241\242\251\237\229",
    "\237\224 \242\240\224\226\255\237\232\241\242\238\233 \240\224\226\237\232\237\229",
    "\226 \239\240\238\236\184\240\231\248\229\233 \242\243\237\228\240\229",
}

local function hasTrees(_nBiome)
    return _nBiome <= 3
end

local function hasStone(_nBiome)
    return _nBiome == 4
end

local function hasRivers(_nBiome)
    return _nBiome ~= 3 and _nBiome ~= 5
end

local items = {
    ["\237\229\242 \247\224\255"] = {
        droppable = false,
        desc = "\209\238\225\229\240\232\242\229\241\252, \228\240\243\230\232\249\229.",
    },
    ["\241\226\232\237\252\255"] = {
        heavy = true,
        creature = true,
        drops = { "\241\226\232\237\232\237\224" },
        aliases = { "pig" },
        desc = "\211 \241\226\232\237\252\232 \234\226\224\228\240\224\242\237\251\233 \239\255\242\224\247\238\234.",
    },
    ["\234\238\240\238\226\224"] = {
        heavy = true,
        creature = true,
        aliases = { "cow" },
        desc = "\202\238\240\238\226\224 \225\229\231\243\247\224\241\242\237\238 \241\236\238\242\240\232\242 \237\224 \226\224\241.",
    },
    ["\238\226\246\224"] = {
        heavy = true,
        creature = true,
        hitDrops = { "\248\229\240\241\242\252" },
        aliases = { "sheep" },
        desc = "\206\226\246\224 \239\243\248\232\241\242\224\255.",
    },
    ["\234\243\240\232\246\224"] = {
        heavy = true,
        creature = true,
        drops = { "\234\243\240\255\242\232\237\224" },
        aliases = { "chicken" },
        desc = "\202\243\240\232\246\224 \226\251\227\235\255\228\232\242 \224\239\239\229\242\232\242\237\238.",
    },
    ["\234\240\232\239\229\240"] = {
        heavy = true,
        creature = true,
        monster = true,
        aliases = { "creeper" },
        desc = "\202\240\232\239\229\240\243 \255\226\237\238 \237\229 \245\226\224\242\224\229\242 \238\225\250\255\242\232\233.",
    },
    ["\241\234\229\235\229\242"] = {
        heavy = true,
        creature = true,
        monster = true,
        aliases = { "skeleton" },
        nocturnal = true,
        desc = "\202\238\241\242\252 \227\238\235\238\226\251 \241\238\229\228\232\237\229\237\224 \241 \248\229\229\233, \248\229\255 - \241 \227\240\243\228\237\238\233 \234\235\229\242\234\238\233, \242\224 - \241 \240\243\234\238\233, \240\243\234\224 \228\229\240\230\232\242 \235\243\234, \224 \235\243\234 \237\224\239\240\224\226\235\229\237 \237\224 \226\224\241.",
    },
    ["\231\238\236\225\232"] = {
        heavy = true,
        creature = true,
        monster = true,
        aliases = { "zombie" },
        nocturnal = true,
        desc = "\197\236\243 \226\241\229\227\238 \235\232\248\252 \245\238\247\229\242\241\255 \241\250\229\241\242\252 \226\224\248 \236\238\231\227.",
    },
    ["\239\224\243\234"] = {
        heavy = true,
        creature = true,
        monster = true,
        aliases = { "spider" },
        desc = "\205\224 \226\224\241 \241\236\238\242\240\255\242 \228\229\241\255\242\234\232 \227\235\224\231.",
    },
    ["\226\245\238\228 \226 \239\229\249\229\240\243"] = {
        heavy = true,
        aliases = { "cave entance", "cave", "entrance" },
        desc = "\194\245\238\228 \226 \239\229\249\229\240\243 \242\184\236\229\237, \237\238, \239\238\245\238\230\229, \242\243\228\224 \236\238\230\237\238 \241\239\243\241\242\232\242\252\241\255.",
    },
    ["\226\251\245\238\228 \237\224 \239\238\226\229\240\245\237\238\241\242\252"] = {
        heavy = true,
        aliases = { "exit to the surface", "exit", "opening" },
        desc = "\209\234\226\238\231\252 \238\242\226\229\240\241\242\232\229 \229\228\226\224 \226\232\228\237\238 \237\229\225\238.",
    },
    ["\240\229\234\224"] = {
        heavy = true,
        aliases = { "river" },
        desc = "\208\229\234\224 \226\229\235\232\247\229\241\242\226\229\237\237\238 \242\229\247\184\242 \234 \227\238\240\232\231\238\237\242\243. \193\238\235\252\248\229 \238\237\224 \237\232\247\229\227\238 \237\229 \228\229\235\224\229\242.",
    },
    ["\228\240\229\226\229\241\232\237\224"] = {
        aliases = { "wood" },
        material = true,
        desc = "\200\231 \253\242\238\233 \228\240\229\226\229\241\232\237\251 \235\229\227\234\238 \241\228\229\235\224\242\252 \228\238\241\234\232.",
    },
    ["\228\238\241\234\232"] = {
        aliases = { "planks", "wooden planks", "wood planks" },
        material = true,
        desc = "\200\231 \253\242\232\245 \228\238\241\238\234 \235\229\227\234\238 \241\228\229\235\224\242\252 \239\224\235\234\232.",
    },
    ["\239\224\235\234\232"] = {
        aliases = { "sticks", "wooden sticks", "wood sticks" },
        desc = "\206\242\235\232\247\237\224\255 \240\243\234\238\255\242\252 \228\235\255 \244\224\234\229\235\238\226 \232\235\232 \234\232\240\234\232.",
    },
    ["\226\229\240\241\242\224\234"] = {
        aliases = { "crafting table", "craft table", "work bench", "workbench", "crafting bench", "table" },
        desc = "\221\242\238 \226\229\240\241\242\224\234. \207\238 \241\229\234\240\229\242\243: \226 \253\242\238\233 \232\227\240\229 \238\237 \237\232\247\229\227\238 \237\229 \228\229\235\224\229\242 - \232\237\241\242\240\243\236\229\237\242\251 \236\238\230\237\238 \241\238\231\228\224\226\224\242\252 \227\228\229 \243\227\238\228\237\238.",
    },
    ["\239\229\247\252"] = {
        aliases = { "furnace" },
        desc = "\221\242\238 \239\229\247\252. \204\229\230\228\243 \237\224\236\232: \226 \253\242\238\233 \232\227\240\229 \238\237\224 \237\232\247\229\227\238 \237\229 \228\229\235\224\229\242.",
    },
    ["\228\229\240\229\226\255\237\237\224\255 \234\232\240\234\224"] = {
        aliases = { "pickaxe", "pick", "wooden pick", "wooden pickaxe", "wood pick", "wood pickaxe" },
        tool = true,
        toolLevel = 1,
        toolType = "pick",
        desc = "\221\242\224 \234\232\240\234\224 \239\238\228\245\238\228\232\242 \228\235\255 \228\238\225\251\247\232 \234\224\236\237\255 \232 \243\227\235\255.",
    },
    ["\234\224\236\229\237\237\224\255 \234\232\240\234\224"] = {
        aliases = { "pickaxe", "pick", "stone pick", "stone pickaxe" },
        tool = true,
        toolLevel = 2,
        toolType = "pick",
        desc = "\221\242\224 \234\232\240\234\224 \239\238\228\245\238\228\232\242 \228\235\255 \228\238\225\251\247\232 \230\229\235\229\231\224.",
    },
    ["\230\229\235\229\231\237\224\255 \234\232\240\234\224"] = {
        aliases = { "pickaxe", "pick", "iron pick", "iron pickaxe" },
        tool = true,
        toolLevel = 3,
        toolType = "pick",
        desc = "\221\242\224 \234\232\240\234\224 \228\238\241\242\224\242\238\247\237\238 \239\240\238\247\237\224 \228\235\255 \228\238\225\251\247\232 \224\235\236\224\231\238\226.",
    },
    ["\224\235\236\224\231\237\224\255 \234\232\240\234\224"] = {
        aliases = { "pickaxe", "pick", "diamond pick", "diamond pickaxe" },
        tool = true,
        toolLevel = 4,
        toolType = "pick",
        desc = "\203\243\247\248\224\255. \202\232\240\234\224. \205\224 \241\226\229\242\229.",
    },
    ["a wooden sword"] = {
        aliases = { "sword", "wooden sword", "wood sword" },
        tool = true,
        toolLevel = 1,
        toolType = "sword",
        desc = "\213\235\232\239\234\232\233, \237\238 \235\243\247\248\229, \247\229\236 \237\232\247\229\227\238.",
    },
    ["a stone sword"] = {
        aliases = { "sword", "stone sword" },
        tool = true,
        toolLevel = 2,
        toolType = "sword",
        desc = "\194\239\238\235\237\229 \245\238\240\238\248\232\233 \236\229\247.",
    },
    ["an iron sword"] = {
        aliases = { "sword", "iron sword" },
        tool = true,
        toolLevel = 3,
        toolType = "sword",
        desc = "\221\242\232\236 \236\229\247\238\236 \236\238\230\237\238 \241\240\224\231\232\242\252 \235\254\225\238\227\238 \226\240\224\227\224.",
    },
    ["a diamond sword"] = {
        aliases = { "sword", "diamond sword" },
        tool = true,
        toolLevel = 4,
        toolType = "sword",
        desc = "\203\243\247\248\232\233. \204\229\247. \205\224 \241\226\229\242\229.",
    },
    ["\228\229\240\229\226\255\237\237\224\255 \235\238\239\224\242\224"] = {
        aliases = { "shovel", "wooden shovel", "wood shovel" },
        tool = true,
        toolLevel = 1,
        toolType = "shovel",
        desc = "\207\238\228\245\238\228\232\242 \228\235\255 \240\251\242\252\255 \255\236.",
    },
    ["\234\224\236\229\237\237\224\255 \235\238\239\224\242\224"] = {
        aliases = { "shovel", "stone shovel" },
        tool = true,
        toolLevel = 2,
        toolType = "shovel",
        desc = "\207\238\228\245\238\228\232\242 \228\235\255 \240\251\242\252\255 \255\236.",
    },
    ["\230\229\235\229\231\237\224\255 \235\238\239\224\242\224"] = {
        aliases = { "shovel", "iron shovel" },
        tool = true,
        toolLevel = 3,
        toolType = "shovel",
        desc = "\207\238\228\245\238\228\232\242 \228\235\255 \240\251\242\252\255 \255\236.",
    },
    ["\224\235\236\224\231\237\224\255 \235\238\239\224\242\224"] = {
        aliases = { "shovel", "diamond shovel" },
        tool = true,
        toolLevel = 4,
        toolType = "shovel",
        desc = "\207\238\228\245\238\228\232\242 \228\235\255 \240\251\242\252\255 \255\236.",
    },
    ["\243\227\238\235\252"] = {
        aliases = { "coal" },
        ore = true,
        toolLevel = 1,
        toolType = "pick",
        desc = "\200\231 \253\242\238\227\238 \243\227\235\255 \239\238\235\243\247\224\242\241\255 \244\224\234\229\235\251 - \225\251\235\224 \225\251 \234\232\240\234\224, \247\242\238\225\251 \229\227\238 \228\238\225\251\242\252.",
    },
    ["\231\229\236\235\255"] = {
        aliases = { "dirt" },
        material = true,
        desc = "\207\238\247\229\236\243 \225\251 \237\229 \239\238\241\242\240\238\232\242\252 \245\232\230\232\237\243 \232\231 \227\240\255\231\232?",
    },
    ["\234\224\236\229\237\252"] = {
        aliases = { "stone", "cobblestone" },
        material = true,
        ore = true,
        infinite = true,
        toolLevel = 1,
        toolType = "pick",
        desc = "\202\224\236\229\237\252 \239\240\232\227\238\228\232\242\241\255 \228\235\255 \241\242\240\238\232\242\229\235\252\241\242\226\224 \232 \232\231\227\238\242\238\226\235\229\237\232\255 \234\224\236\229\237\237\251\245 \234\232\240\238\234.",
    },
    ["\230\229\235\229\231\238"] = {
        aliases = { "iron" },
        material = true,
        ore = true,
        toolLevel = 2,
        toolType = "pick",
        desc = "\198\229\235\229\231\238 \226\251\227\235\255\228\232\242 \239\240\238\247\237\251\236; \228\235\255 \229\227\238 \228\238\225\251\247\232 \239\238\237\224\228\238\225\232\242\241\255 \234\224\236\229\237\237\224\255 \234\232\240\234\224.",
    },
    ["\224\235\236\224\231\251"] = {
        aliases = { "diamond", "diamonds" },
        material = true,
        ore = true,
        toolLevel = 3,
        toolType = "pick",
        desc = "\209\226\229\240\234\224\229\242, \240\229\228\234\238 \226\241\242\240\229\247\224\229\242\241\255, \224 \225\229\231 \230\229\235\229\231\237\238\233 \234\232\240\234\232 \229\184 \237\229 \228\238\225\251\242\252.",
    },
    ["\244\224\234\229\235\251"] = {
        aliases = { "torches", "torch" },
        desc = "\200\245 \245\226\224\242\232\242 \237\224\228\238\235\227\238.",
    },
    ["\244\224\234\229\235"] = {
        aliases = { "torch" },
        desc = "\195\238\240\232, \238\227\238\237\252, \241\232\255\233 \255\240\247\229 \232 \238\241\226\229\242\232 \241\229\227\238\228\237\255 \236\238\254 \239\229\249\229\240\243.",
    },
    ["\248\229\240\241\242\252"] = {
        aliases = { "wool" },
        material = true,
        desc = "\204\255\227\234\224\255 \232 \245\238\240\238\248\238 \239\238\228\245\238\228\232\242 \228\235\255 \241\242\240\238\232\242\229\235\252\241\242\226\224.",
    },
    ["\241\226\232\237\232\237\224"] = {
        aliases = { "pork", "porkchops" },
        food = true,
        desc = "\194\234\243\241\237\238 \232 \239\232\242\224\242\229\235\252\237\238.",
    },
    ["\234\243\240\255\242\232\237\224"] = {
        aliases = { "chicken" },
        food = true,
        desc = "\207\224\235\252\247\232\234\232 \238\225\235\232\230\229\248\252.",
    },
}

local tAnimals = {
    "\241\226\232\237\252\255", "\234\238\240\238\226\224", "\238\226\246\224", "\234\243\240\232\246\224",
}

local tMonsters = {
    "\234\240\232\239\229\240", "\241\234\229\235\229\242", "\231\238\236\225\232", "\239\224\243\234",
}

local tRecipes = {
    ["\228\238\241\234\232"] = { "\228\240\229\226\229\241\232\237\224" },
    ["\239\224\235\234\232"] = { "\228\238\241\234\232" },
    ["\226\229\240\241\242\224\234"] = { "\228\238\241\234\232" },
    ["\239\229\247\252"] = { "\234\224\236\229\237\252" },
    ["\244\224\234\229\235\251"] = { "\239\224\235\234\232", "\243\227\238\235\252" },

    ["\228\229\240\229\226\255\237\237\224\255 \234\232\240\234\224"] = { "\228\238\241\234\232", "\239\224\235\234\232" },
    ["\234\224\236\229\237\237\224\255 \234\232\240\234\224"] = { "\234\224\236\229\237\252", "\239\224\235\234\232" },
    ["\230\229\235\229\231\237\224\255 \234\232\240\234\224"] = { "\230\229\235\229\231\238", "\239\224\235\234\232" },
    ["\224\235\236\224\231\237\224\255 \234\232\240\234\224"] = { "\224\235\236\224\231\251", "\239\224\235\234\232" },

    ["a wooden sword"] = { "\228\238\241\234\232", "\239\224\235\234\232" },
    ["a stone sword"] = { "\234\224\236\229\237\252", "\239\224\235\234\232" },
    ["an iron sword"] = { "\230\229\235\229\231\238", "\239\224\235\234\232" },
    ["a diamond sword"] = { "\224\235\236\224\231\251", "\239\224\235\234\232" },

    ["\228\229\240\229\226\255\237\237\224\255 \235\238\239\224\242\224"] = { "\228\238\241\234\232", "\239\224\235\234\232" },
    ["\234\224\236\229\237\237\224\255 \235\238\239\224\242\224"] = { "\234\224\236\229\237\252", "\239\224\235\234\232" },
    ["\230\229\235\229\231\237\224\255 \235\238\239\224\242\224"] = { "\230\229\235\229\231\238", "\239\224\235\234\232" },
    ["\224\235\236\224\231\237\224\255 \235\238\239\224\242\224"] = { "\224\235\236\224\231\251", "\239\224\235\234\232" },
}

local tGoWest = {
    "(\242\224\236 \230\232\226\184\242\241\255 \225\229\231 \231\224\225\238\242)",
    "(\232 \226\238\234\240\243\227 \239\240\238\241\242\238\240)",
    "(\237\224\247\224\242\252 \230\232\231\237\252 \241 \237\243\235\255)",
    "(\226\238\242 \247\242\238 \236\251 \241\228\229\235\224\229\236)",
    "(\231\232\236\238\233 \241\232\255\229\242 \241\238\235\237\246\229)",
    "(\243 \237\224\241 \226\241\184 \225\243\228\229\242 \245\238\240\238\248\238)",
    "(\239\238\228 \227\238\235\243\225\251\236\232 \237\229\225\229\241\224\236\232)",
    "(\232 \236\237\238\227\238\229 \229\249\184)",
}
local nGoWest = 0

local bRunning = true
local tMap = { { {} } }
local x, y, z = 0, 0, 0
local inventory = {
    ["\237\229\242 \247\224\255"] = items["\237\229\242 \247\224\255"],
}

local nTurn = 0
local nTimeInRoom = 0
local bInjured = false

local tDayCycle = {
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\229\233\247\224\241 \228\229\237\252.",
    "\209\238\235\237\246\229 \241\224\228\232\242\241\255.",
    "\209\229\233\247\224\241 \237\238\247\252.",
    "\209\229\233\247\224\241 \237\238\247\252.",
    "\209\229\233\247\224\241 \237\238\247\252.",
    "\209\229\233\247\224\241 \237\238\247\252.",
    "\209\229\233\247\224\241 \237\238\247\252.",
    "\209\238\235\237\246\229 \226\238\241\245\238\228\232\242.",
}

local function getTimeOfDay()
    return math.fmod(math.floor(nTurn / 3), #tDayCycle) + 1
end

local function isSunny()
    return getTimeOfDay() < 10
end

local function getRoom(x, y, z, dontCreate)
    tMap[x] = tMap[x] or {}
    tMap[x][y] = tMap[x][y] or {}
    if not tMap[x][y][z] and dontCreate ~= true then
         local room = {
             items = {},
             exits = {},
             nMonsters = 0,
         }
        tMap[x][y][z] = room

        if y == 0 then
            -- Room is above ground

            -- Pick biome
            room.nBiome = math.random(1, #tBiomes)
            room.trees = hasTrees(room.nBiome)

            -- Add animals
            if math.random(1, 3) == 1 then
                for _ = 1, math.random(1, 2) do
                    local sAnimal = tAnimals[math.random(1, #tAnimals)]
                    room.items[sAnimal] = items[sAnimal]
                end
            end

            -- Add surface ore
            if math.random(1, 5) == 1 or hasStone(room.nBiome) then
                room.items["\234\224\236\229\237\252"] = items["\234\224\236\229\237\252"]
            end
            if math.random(1, 8) == 1 then
                room.items["\243\227\238\235\252"] = items["\243\227\238\235\252"]
            end
            if math.random(1, 8) == 1 and hasRivers(room.nBiome) then
                room.items["\240\229\234\224"] = items["\240\229\234\224"]
            end

            -- Add exits
            room.exits = {
                ["north"] = true,
                ["south"] = true,
                ["east"] = true,
                ["west"] = true,
            }
            if math.random(1, 8) == 1 then
                room.exits.down = true
                room.items["\226\245\238\228 \226 \239\229\249\229\240\243"] = items["\226\245\238\228 \226 \239\229\249\229\240\243"]
            end

        else
            -- Room is underground
            -- Add exits
            local function tryExit(sDir, sOpp, x, y, z)
                local adj = getRoom(x, y, z, true)
                if adj then
                    if adj.exits[sOpp] then
                        room.exits[sDir] = true
                    end
                else
                    if math.random(1, 3) == 1 then
                        room.exits[sDir] = true
                    end
                end
            end

            if y == -1 then
                local above = getRoom(x, y + 1, z)
                if above.exits.down then
                    room.exits.up = true
                    room.items["\226\251\245\238\228 \237\224 \239\238\226\229\240\245\237\238\241\242\252"] = items["\226\251\245\238\228 \237\224 \239\238\226\229\240\245\237\238\241\242\252"]
                end
            else
                tryExit("up", "down", x, y + 1, z)
            end

            if y > -3 then
                tryExit("down", "up", x, y - 1, z)
            end

            tryExit("east", "west", x - 1, y, z)
            tryExit("west", "east", x + 1, y, z)
            tryExit("north", "south", x, y, z + 1)
            tryExit("south", "north", x, y, z - 1)

            -- Add ores
            room.items["\234\224\236\229\237\252"] = items["\234\224\236\229\237\252"]
            if math.random(1, 3) == 1 then
                room.items["\243\227\238\235\252"] = items["\243\227\238\235\252"]
            end
            if math.random(1, 8) == 1 then
                room.items["\230\229\235\229\231\238"] = items["\230\229\235\229\231\238"]
            end
            if y == -3 and math.random(1, 15) == 1 then
                room.items["\224\235\236\224\231\251"] = items["\224\235\236\224\231\251"]
            end

            -- Turn out the lights
            room.dark = true
        end
    end
    return tMap[x][y][z]
end

local function itemize(t)
    local item = next(t)
    if item == nil then
        return "\237\232\247\229\227\238"
    end

    local text = ""
    while item do
        text = text .. item

        local nextItem = next(t, item)
        if nextItem ~= nil then
            local nextNextItem = next(t, nextItem)
            if nextNextItem == nil then
                text = text .. " \232 "
            else
                text = text .. ", "
            end
        end
        item = nextItem
    end
    return text
end

local function findItem(_tList, _sQuery)
    for sItem, tItem in pairs(_tList) do
        if sItem == _sQuery then
            return sItem
        end
        if tItem.aliases ~= nil then
            for _, sAlias in pairs(tItem.aliases) do
                if sAlias == _sQuery then
                    return sItem
                end
            end
        end
    end
    return nil
end

local tMatches = {
    ["wait"] = {
        "wait",
    },
    ["look"] = {
        "look at the ([%a ]+)",
        "look at ([%a ]+)",
        "look",
        "inspect ([%a ]+)",
        "inspect the ([%a ]+)",
        "inspect",
    },
    ["inventory"] = {
        "check self",
        "check inventory",
        "inventory",
        "i",
    },
    ["go"] = {
        "go (%a+)",
        "travel (%a+)",
        "walk (%a+)",
        "run (%a+)",
        "go",
    },
    ["dig"] = {
        "dig (%a+) using ([%a ]+)",
        "dig (%a+) with ([%a ]+)",
        "dig (%a+)",
        "dig",
    },
    ["take"] = {
        "pick up the ([%a ]+)",
        "pick up ([%a ]+)",
        "pickup ([%a ]+)",
        "take the ([%a ]+)",
        "take ([%a ]+)",
        "take",
    },
    ["drop"] = {
        "put down the ([%a ]+)",
        "put down ([%a ]+)",
        "drop the ([%a ]+)",
        "drop ([%a ]+)",
        "drop",
    },
    ["place"] = {
        "place the ([%a ]+)",
        "place ([%a ]+)",
        "place",
    },
    ["cbreak"] = {
        "punch the ([%a ]+)",
        "punch ([%a ]+)",
        "punch",
        "break the ([%a ]+) with the ([%a ]+)",
        "break ([%a ]+) with ([%a ]+) ",
        "break the ([%a ]+)",
        "break ([%a ]+)",
        "break",
    },
    ["mine"] = {
        "mine the ([%a ]+) with the ([%a ]+)",
        "mine ([%a ]+) with ([%a ]+)",
        "mine ([%a ]+)",
        "mine",
    },
    ["attack"] = {
        "attack the ([%a ]+) with the ([%a ]+)",
        "attack ([%a ]+) with ([%a ]+)",
        "attack ([%a ]+)",
        "attack",
        "kill the ([%a ]+) with the ([%a ]+)",
        "kill ([%a ]+) with ([%a ]+)",
        "kill ([%a ]+)",
        "kill",
        "hit the ([%a ]+) with the ([%a ]+)",
        "hit ([%a ]+) with ([%a ]+)",
        "hit ([%a ]+)",
        "hit",
    },
    ["craft"] = {
        "craft a ([%a ]+)",
        "craft some ([%a ]+)",
        "craft ([%a ]+)",
        "craft",
        "make a ([%a ]+)",
        "make some ([%a ]+)",
        "make ([%a ]+)",
        "make",
    },
    ["build"] = {
        "build ([%a ]+) out of ([%a ]+)",
        "build ([%a ]+) from ([%a ]+)",
        "build ([%a ]+)",
        "build",
    },
    ["eat"] = {
        "eat a ([%a ]+)",
        "eat the ([%a ]+)",
        "eat ([%a ]+)",
        "eat",
    },
    ["help"] = {
        "help me",
        "help",
    },
    ["exit"] = {
        "exit",
        "quit",
        "goodbye",
        "good bye",
        "bye",
        "farewell",
    },
}

local commands = {}
local function doCommand(text)
    if text == "" then
        commands.noinput()
        return
    end

    for sCommand, t in pairs(tMatches) do
        for _, sMatch in pairs(t) do
            local tCaptures = { string.match(text, "^" .. sMatch .. "$") }
            if #tCaptures ~= 0 then
                local fnCommand = commands[sCommand]
                if #tCaptures == 1 and tCaptures[1] == sMatch then
                    fnCommand()
                else
                    fnCommand(table.unpack(tCaptures))
                end
                return
            end
        end
    end
    commands.badinput()
end

function commands.wait()
    print("\194\240\229\236\255 \232\228\184\242...")
end

function commands.look(_sTarget)
    local room = getRoom(x, y, z)
    if room.dark then
        print("\199\228\229\241\252 \234\240\238\236\229\248\237\224\255 \242\252\236\224.")
        return
    end

    if _sTarget == nil then
        -- Look at the world
        if y == 0 then
            io.write("\194\251 \241\242\238\232\242\229 " .. tBiomes[room.nBiome] .. ". ")
            print(tDayCycle[getTimeOfDay()])
        else
            io.write("\194\251 \239\238\228 \231\229\236\235\184\233. ")
            if next(room.exits) ~= nil then
                print("\204\238\230\237\238 \239\238\233\242\232: " .. itemize(room.exits) .. ".")
            else
                print()
            end
        end
        if next(room.items) ~= nil then
            print("\199\228\229\241\252 \229\241\242\252 " .. itemize(room.items) .. ".")
        end
        if room.trees then
            print("\199\228\229\241\252 \240\224\241\242\243\242 \228\229\240\229\226\252\255.")
        end

    else
        -- Look at stuff
        if room.trees and (_sTarget == "tree" or _sTarget == "trees") then
            print("\207\238\245\238\230\229, \253\242\232 \228\229\240\229\226\252\255 \235\229\227\234\238 \241\235\238\236\224\242\252.")
        elseif _sTarget == "self" or _sTarget == "myself" then
            print("\206\247\229\237\252 \228\224\230\229 \237\232\247\229\227\238.")
        else
            local tItem = nil
            local sItem = findItem(room.items, _sTarget)
            if sItem then
                tItem = room.items[sItem]
            else
                sItem = findItem(inventory, _sTarget)
                if sItem then
                    tItem = inventory[sItem]
                end
            end

            if tItem then
                print(tItem.desc or "\205\232\247\229\227\238 \239\240\232\236\229\247\224\242\229\235\252\237\238\227\238 \226 \253\242\238\236 \237\229\242: " .. sItem .. ".")
            else
                print("\199\228\229\241\252 \237\229\242 " .. _sTarget .. ".")
            end
        end
    end
end

function commands.go(_sDir)
    local room = getRoom(x, y, z)
    if _sDir == nil then
        print("\202\243\228\224 \232\228\242\232?")
        return
    end

    if nGoWest ~= nil then
        if _sDir == "west" then
            nGoWest = nGoWest + 1
            if nGoWest > #tGoWest then
                nGoWest = 1
            end
            print(tGoWest[nGoWest])
        else
            if nGoWest > 0 or nTurn > 6 then
                nGoWest = nil
            end
        end
    end

    if room.exits[_sDir] == nil then
        print("\210\243\228\224 \239\240\238\233\242\232 \237\229\235\252\231\255.")
        return
    end

    if _sDir == "north" then
        z = z + 1
    elseif _sDir == "south" then
        z = z - 1
    elseif _sDir == "east" then
        x = x - 1
    elseif _sDir == "west" then
        x = x + 1
    elseif _sDir == "up" then
        y = y + 1
    elseif _sDir == "down" then
        y = y - 1
    else
        print("\223 \237\229 \239\238\237\232\236\224\254 \253\242\238 \237\224\239\240\224\226\235\229\237\232\229.")
        return
    end

    nTimeInRoom = 0
    doCommand("look")
end

function commands.dig(_sDir, _sTool)
    local room = getRoom(x, y, z)
    if _sDir == nil then
        print("\195\228\229 \234\238\239\224\242\252?")
        return
    end

    local sTool = nil
    local tTool = nil
    if _sTool ~= nil then
        sTool = findItem(inventory, _sTool)
        if not sTool then
            print("\211 \226\224\241 \237\229\242 " .. _sTool .. ".")
            return
        end
        tTool = inventory[sTool]
    end

    local bActuallyDigging = room.exits[_sDir] ~= true
    if bActuallyDigging then
        if sTool == nil or tTool.toolType ~= "pick" then
            print("\215\242\238\225\251 \239\240\238\225\232\242\252\241\255 \241\234\226\238\231\252 \234\224\236\229\237\252, \237\243\230\237\224 \234\232\240\234\224.")
            return
        end
    end

    if _sDir == "north" then
        room.exits.north = true
        z = z + 1
        getRoom(x, y, z).exits.south = true

    elseif _sDir == "south" then
        room.exits.south = true
        z = z - 1
        getRoom(x, y, z).exits.north = true

    elseif _sDir == "east" then
        room.exits.east = true
        x = x - 1
        getRoom(x, y, z).exits.west = true

    elseif _sDir == "west" then
        room.exits.west = true
        x = x + 1
        getRoom(x, y, z).exits.east = true

    elseif _sDir == "up" then
        if y == 0 then
            print("\194 \253\242\238\236 \237\224\239\240\224\226\235\229\237\232\232 \234\238\239\224\242\252 \237\229\235\252\231\255.")
            return
        end

        room.exits.up = true
        if y == -1 then
            room.items["\226\251\245\238\228 \237\224 \239\238\226\229\240\245\237\238\241\242\252"] = items["\226\251\245\238\228 \237\224 \239\238\226\229\240\245\237\238\241\242\252"]
        end
        y = y + 1

        room = getRoom(x, y, z)
        room.exits.down = true
        if y == 0 then
            room.items["\226\245\238\228 \226 \239\229\249\229\240\243"] = items["\226\245\238\228 \226 \239\229\249\229\240\243"]
        end

    elseif _sDir == "down" then
        if y <= -3 then
            print("\194\251 \243\239\232\240\224\229\242\229\241\252 \226 \234\238\240\229\237\237\243\254 \239\238\240\238\228\243.")
            return
        end

        room.exits.down = true
        if y == 0 then
            room.items["\226\245\238\228 \226 \239\229\249\229\240\243"] = items["\226\245\238\228 \226 \239\229\249\229\240\243"]
        end
        y = y - 1

        room = getRoom(x, y, z)
        room.exits.up = true
        if y == -1 then
            room.items["\226\251\245\238\228 \237\224 \239\238\226\229\240\245\237\238\241\242\252"] = items["\226\251\245\238\228 \237\224 \239\238\226\229\240\245\237\238\241\242\252"]
        end

    else
        print("\223 \237\229 \239\238\237\232\236\224\254 \253\242\238 \237\224\239\240\224\226\235\229\237\232\229.")
        return
    end

    --
    if bActuallyDigging then
        if _sDir == "down" and y == -1 or
           _sDir == "up" and y == 0 then
            inventory["\231\229\236\235\255"] = items["\231\229\236\235\255"]
            inventory["\234\224\236\229\237\252"] = items["\234\224\236\229\237\252"]
            print("\205\224\239\240\224\226\235\229\237\232\229 \240\224\241\234\238\239\238\234: " .. _sDir .. "; \232\237\241\242\240\243\236\229\237\242: " .. sTool .. ". \196\238\225\251\242\238 \237\229\236\237\238\227\238 \231\229\236\235\232 \232 \234\224\236\237\255.")
        else
            inventory["\234\224\236\229\237\252"] = items["\234\224\236\229\237\252"]
            print("\205\224\239\240\224\226\235\229\237\232\229 \240\224\241\234\238\239\238\234: " .. _sDir .. "; \232\237\241\242\240\243\236\229\237\242: " .. sTool .. ". \196\238\225\251\242\238 \237\229\236\237\238\227\238 \234\224\236\237\255.")
        end
    end

    nTimeInRoom = 0
    doCommand("look")
end

function commands.inventory()
    print("\211 \226\224\241 \241 \241\238\225\238\233: " .. itemize(inventory) .. ".")
end

function commands.drop(_sItem)
    if _sItem == nil then
        print("\215\242\238 \226\251\225\240\238\241\232\242\252?")
        return
    end

    local room = getRoom(x, y, z)
    local sItem = findItem(inventory, _sItem)
    if sItem then
        local tItem = inventory[sItem]
        if tItem.droppable == false then
            print("\221\242\238 \237\229\235\252\231\255 \226\251\225\240\238\241\232\242\252.")
        else
            room.items[sItem] = tItem
            inventory[sItem] = nil
            print("\194\251\225\240\238\248\229\237\238.")
        end
    else
        print("\211 \226\224\241 \237\229\242 " .. _sItem .. ".")
    end
end

function commands.place(_sItem)
    if _sItem == nil then
        print("\215\242\238 \239\238\241\242\224\226\232\242\252?")
        return
    end

    if _sItem == "torch" or _sItem == "\244\224\234\229\235" then
        local room = getRoom(x, y, z)
        if inventory["\244\224\234\229\235\251"] or inventory["\244\224\234\229\235"] then
            inventory["\244\224\234\229\235"] = nil
            room.items["\244\224\234\229\235"] = items["\244\224\234\229\235"]
            if room.dark then
                print("\207\235\224\236\255 \244\224\234\229\235\224 \238\241\226\229\249\224\229\242 \239\229\249\229\240\243.")
                room.dark = false
            elseif y == 0 and not isSunny() then
                print("\205\238\247\252 \241\242\224\237\238\226\232\242\241\255 \237\229\236\237\238\227\238 \241\226\229\242\235\229\229.")
            else
                print("\211\241\242\224\237\238\226\235\229\237\238.")
            end
        else
            print("\211 \226\224\241 \237\229\242 \244\224\234\229\235\238\226.")
        end
        return
    end

    commands.drop(_sItem)
end

function commands.take(_sItem)
    if _sItem == nil then
        print("\215\242\238 \226\231\255\242\252?")
        return
    end

    local room = getRoom(x, y, z)
    local sItem = findItem(room.items, _sItem)
    if sItem then
        local tItem = room.items[sItem]
        if tItem.heavy == true then
            print("\221\242\238 \237\229\235\252\231\255 \243\237\229\241\242\232: " .. sItem .. ".")
        elseif tItem.ore == true then
            print("\221\242\243 \240\243\228\243 \237\243\230\237\238 \228\238\225\251\242\252 \234\232\240\234\238\233.")
        else
            if tItem.infinite ~= true then
                room.items[sItem] = nil
            end
            inventory[sItem] = tItem

            if inventory["\244\224\234\229\235\251"] and inventory["\244\224\234\229\235"] then
                inventory["\244\224\234\229\235"] = nil
            end
            if sItem == "\244\224\234\229\235" and y < 0 then
                room.dark = true
                print("\207\229\249\229\240\224 \239\238\227\240\243\230\224\229\242\241\255 \226\238 \242\252\236\243.")
            else
                print("\194\231\255\242\238.")
            end
        end
    else
        print("\199\228\229\241\252 \237\229\242 " .. _sItem .. ".")
    end
end

function commands.mine(_sItem, _sTool)
    if _sItem == nil then
        print("\215\242\238 \228\238\225\251\242\252?")
        return
    end
    if _sTool == nil then
        print("\215\229\236 \228\238\225\251\242\252 " .. _sItem .. "?")
        return
    end
    commands.cbreak(_sItem, _sTool)
end

function commands.attack(_sItem, _sTool)
    if _sItem == nil then
        print("\202\238\227\238 \224\242\224\234\238\226\224\242\252?")
        return
    end
    commands.cbreak(_sItem, _sTool)
end

function commands.cbreak(_sItem, _sTool)
    if _sItem == nil then
        print("\215\242\238 \241\235\238\236\224\242\252?")
        return
    end

    local sTool = nil
    if _sTool ~= nil then
        sTool = findItem(inventory, _sTool)
        if sTool == nil then
            print("\211 \226\224\241 \237\229\242 " .. _sTool .. ".")
            return
        end
    end

    local room = getRoom(x, y, z)
    if _sItem == "tree" or _sItem == "trees" or _sItem == "a tree" then
        print("\196\229\240\229\226\238 \240\224\241\239\224\228\224\229\242\241\255 \237\224 \225\235\238\234\232 \228\240\229\226\229\241\232\237\251, \232 \226\251 \232\245 \239\238\228\225\232\240\224\229\242\229.")
        inventory["\228\240\229\226\229\241\232\237\224"] = items["\228\240\229\226\229\241\232\237\224"]
        return
    elseif _sItem == "self" or _sItem == "myself" then
        if term.isColour() then
            term.setTextColour(colours.red)
        end
        print("\194\251 \239\238\227\232\225\235\232.")
        print("\209\247\184\242: &e0")
        term.setTextColour(colours.white)
        bRunning = false
        return
    end

    local sItem = findItem(room.items, _sItem)
    if sItem then
        local tItem = room.items[sItem]
        if tItem.ore == true then
            -- Breaking ore
            if not sTool then
                print("\215\242\238\225\251 \228\238\225\251\242\252 \253\242\243 \240\243\228\243, \237\243\230\229\237 \232\237\241\242\240\243\236\229\237\242.")
                return
            end
            local tTool = inventory[sTool]
            if tTool.tool then
                if tTool.toolLevel < tItem.toolLevel then
                    print(sTool .. " - \239\240\238\247\237\238\241\242\232 \253\242\238\227\238 \232\237\241\242\240\243\236\229\237\242\224 \237\229\228\238\241\242\224\242\238\247\237\238 \228\235\255 \253\242\238\233 \240\243\228\251.")
                elseif tTool.toolType ~= tItem.toolType then
                    print("\196\235\255 \253\242\238\233 \240\243\228\251 \237\243\230\229\237 \232\237\241\242\240\243\236\229\237\242 \228\240\243\227\238\227\238 \242\232\239\224.")
                else
                    print("\208\243\228\224 \240\224\241\234\224\235\251\226\224\229\242\241\255 \232 \238\241\242\224\226\235\255\229\242 " .. sItem .. "; \226\251 \239\238\228\225\232\240\224\229\242\229 \228\238\225\251\247\243.")
                    inventory[sItem] = items[sItem]
                    if tItem.infinite ~= true then
                        room.items[sItem] = nil
                    end
                end
            else
                print("\205\229\235\252\231\255 \240\224\231\240\243\248\232\242\252 \238\225\250\229\234\242: " .. sItem .. "; \232\237\241\242\240\243\236\229\237\242: " .. sTool .. ".")
            end

        elseif tItem.creature == true then
            -- Fighting monsters (or pigs)
            local toolLevel = 0
            local tTool = nil
            if sTool then
                tTool = inventory[sTool]
                if tTool.toolType == "sword" then
                    toolLevel = tTool.toolLevel
                end
            end

            local tChances = { 0.2, 0.4, 0.55, 0.8, 1 }
            if math.random() <= tChances[toolLevel + 1] then
                room.items[sItem] = nil
                print("\209\243\249\229\241\242\226\238 \171" .. sItem .. "\187 \239\238\227\232\225\224\229\242.")

                if tItem.drops then
                    for _, sDrop in pairs(tItem.drops) do
                        if not room.items[sDrop] then
                            print("\209\243\249\229\241\242\226\238 \171" .. sItem .. "\187 \238\241\242\224\226\235\255\229\242 \239\238\241\235\229 \241\229\225\255: " .. sDrop .. ".")
                            room.items[sDrop] = items[sDrop]
                        end
                    end
                end

                if tItem.monster then
                    room.nMonsters = room.nMonsters - 1
                end
            else
                print("\209\243\249\229\241\242\226\238 \171" .. sItem .. "\187 \240\224\237\229\237\238 \226\224\248\232\236 \243\228\224\240\238\236.")
            end

            if tItem.hitDrops then
                for _, sDrop in pairs(tItem.hitDrops) do
                    if not room.items[sDrop] then
                        print("\209\243\249\229\241\242\226\238 \171" .. sItem .. "\187 \238\241\242\224\226\235\255\229\242 \239\238\241\235\229 \241\229\225\255: " .. sDrop .. ".")
                        room.items[sDrop] = items[sDrop]
                    end
                end
            end

        else
            print("\205\229\235\252\231\255 \240\224\231\240\243\248\232\242\252 \238\225\250\229\234\242: " .. sItem .. ".")
        end
    else
        print("\199\228\229\241\252 \237\229\242 " .. _sItem .. ".")
    end
end

function commands.craft(_sItem)
    if _sItem == nil then
        print("\215\242\238 \241\238\231\228\224\242\252?")
        return
    end

    if _sItem == "computer" or _sItem == "a computer" then
        print("\209\238\231\228\224\226 \234\238\236\239\252\254\242\229\240 \226\237\243\242\240\232 \234\238\236\239\252\254\242\229\240\224 \226\237\243\242\240\232 \234\238\236\239\252\254\242\229\240\224, \226\251 \240\224\231\240\251\226\224\229\242\229 \239\240\238\241\242\240\224\237\241\242\226\238-\226\240\229\236\255 \232 \239\238\239\224\228\224\229\242\229 \226 \235\238\226\243\248\234\243, \232\231 \234\238\242\238\240\238\233 \241\236\229\240\242\237\238\236\243 \237\229 \226\251\225\240\224\242\252\241\255.")
        if term.isColour() then
            term.setTextColour(colours.red)
        end
        print("\194\251 \239\238\227\232\225\235\232.")
        print("\209\247\184\242: &e0")
        term.setTextColour(colours.white)
        bRunning = false
        return
    end

    local sItem = findItem(items, _sItem)
    local tRecipe = sItem and tRecipes[sItem] or nil
    if tRecipe then
        for _, sReq in ipairs(tRecipe) do
            if inventory[sReq] == nil then
                print("\205\229 \245\226\224\242\224\229\242 \234\238\236\239\238\237\229\237\242\238\226 \228\235\255 \240\229\246\229\239\242\224: " .. sItem .. ".")
                return
            end
        end

        for _, sReq in ipairs(tRecipe) do
            inventory[sReq] = nil
        end
        inventory[sItem] = items[sItem]
        if inventory["\244\224\234\229\235\251"] and inventory["\244\224\234\229\235"] then
            inventory["\244\224\234\229\235"] = nil
        end
        print("\195\238\242\238\226\238.")
    else
        print("\205\229\232\231\226\229\241\242\237\251\233 \240\229\246\229\239\242: " .. (sItem or _sItem) .. ".")
    end
end

function commands.build(_sThing, _sMaterial)
    if _sThing == nil then
        print("\215\242\238 \239\238\241\242\240\238\232\242\252?")
        return
    end

    local sMaterial = nil
    if _sMaterial == nil then
        for sItem, tItem in pairs(inventory) do
            if tItem.material then
                sMaterial = sItem
                break
            end
        end
        if sMaterial == nil then
            print("\211 \226\224\241 \237\229\242 \241\242\240\238\232\242\229\235\252\237\251\245 \236\224\242\229\240\232\224\235\238\226.")
            return
        end
    else
        sMaterial = findItem(inventory, _sMaterial)
        if not sMaterial then
            print("\211 \226\224\241 \237\229\242 " .. _sMaterial)
            return
        end

        if inventory[sMaterial].material ~= true then
            print(sMaterial .. " \237\229 \239\238\228\245\238\228\232\242 \228\235\255 \241\242\240\238\232\242\229\235\252\241\242\226\224.")
            return
        end
    end

    local alias = nil
    if string.sub(_sThing, 1, 1) == "a" then
        alias = string.match(_sThing, "a ([%a ]+)")
    end

    local room = getRoom(x, y, z)
    inventory[sMaterial] = nil
    room.items[_sThing] = {
        heavy = true,
        aliases = { alias },
        desc = "\195\235\255\228\255 \237\224 \241\226\238\184 \242\226\238\240\229\237\232\229 (\236\224\242\229\240\232\224\235: " .. sMaterial .. "), \226\224\241 \239\229\240\229\239\238\235\237\255\229\242 \227\238\240\228\238\241\242\252.",
    }

    print("\209\242\240\238\232\242\229\235\252\241\242\226\238 \231\224\226\229\240\248\229\237\238.")
end

function commands.help()
    local sText =
        "\196\238\225\240\238 \239\238\230\224\235\238\226\224\242\252 \226 adventure - \226\229\235\232\247\224\233\248\243\254 \242\229\234\241\242\238\226\243\254 \232\227\240\243 \237\224 CraftOS. " ..
        "\194\226\238\228\232\242\229 \228\229\233\241\242\226\232\255, \247\242\238\225\251 \239\229\240\229\236\229\249\224\242\252\241\255 \239\238 \236\232\240\243, " ..
        "\224 \232\227\240\224 \238\239\232\248\229\242 \240\229\231\243\235\252\242\224\242. \196\238\241\242\243\239\237\251\229 \228\229\233\241\242\226\232\255: go, look, inspect, inventory, " ..
        "take, drop, place, punch, attack, mine, dig, craft, build, eat \232 exit."
    print(sText)
end

function commands.eat(_sItem)
    if _sItem == nil then
        print("\215\242\238 \241\250\229\241\242\252?")
        return
    end

    local sItem = findItem(inventory, _sItem)
    if not sItem then
        print("\211 \226\224\241 \237\229\242 " .. _sItem .. ".")
        return
    end

    local tItem = inventory[sItem]
    if tItem.food then
        print("\193\251\235\238 \238\247\229\237\252 \226\234\243\241\237\238!")
        inventory[sItem] = nil

        if bInjured then
            print("\194\251 \225\238\235\252\248\229 \237\229 \240\224\237\229\237\251.")
            bInjured = false
        end
    else
        print("\221\242\238\242 \239\240\229\228\236\229\242 \237\229\235\252\231\255 \241\250\229\241\242\252: " .. sItem .. ".")
    end
end

function commands.exit()
    bRunning = false
end

function commands.badinput()
    local tResponses = {
        "\223 \237\229 \239\238\237\232\236\224\254.",
        "\223 \226\224\241 \237\229 \239\238\237\232\236\224\254.",
        "\210\224\234 \241\228\229\235\224\242\252 \237\229\235\252\231\255.",
        "\205\229\242.",
        "\192?",
        "\207\238\226\242\238\240\232\242\229?",
        "\215\242\238 \231\224 \225\229\231\243\236\232\229.",
        "\195\238\226\238\240\232\242\229 \255\241\237\229\229.",
        "\223 \239\238\228\243\236\224\254.",
        "\194\229\240\237\184\236\241\255 \234 \253\242\238\236\243 \239\238\231\230\229.",
        "\194 \253\242\238\236 \237\229\242 \237\232\234\224\234\238\227\238 \241\236\251\241\235\224.",
        "\215\242\238?",
    }
    print(tResponses[math.random(1, #tResponses)])
end

function commands.noinput()
    local tResponses = {
        "\195\238\226\238\240\232\242\229 \227\240\238\236\247\229.",
        "\195\238\226\238\240\232\242\229 \240\224\231\225\238\240\247\232\226\238.",
        "\195\238\226\238\240\232\242\229 \227\240\238\236\247\229.",
        "\205\229 \241\242\229\241\237\255\233\242\229\241\252.",
        "\209\234\224\230\232\242\229 \241\235\238\226\224\236\232.",
    }
    print(tResponses[math.random(1, #tResponses)])
end

local function simulate()
    local bNewMonstersThisRoom = false

    -- Spawn monsters in nearby rooms
    for sx = -2, 2 do
        for sy = -1, 1 do
            for sz = -2, 2 do
                local h = y + sy
                if h >= -3 and h <= 0 then
                    local room = getRoom(x + sx, h, z + sz)

                    -- Spawn monsters
                    if room.nMonsters < 2 and
                       (h == 0 and not isSunny() and not room.items["\244\224\234\229\235"] or room.dark) and
                       math.random(1, 6) == 1 then

                        local sMonster = tMonsters[math.random(1, #tMonsters)]
                        if room.items[sMonster] == nil then
                               room.items[sMonster] = items[sMonster]
                               room.nMonsters = room.nMonsters + 1

                               if sx == 0 and sy == 0 and sz == 0 and not room.dark then
                                   print("\200\231 \242\229\236\237\238\242\251 \239\238\255\226\235\255\229\242\241\255 \241\243\249\229\241\242\226\238: " .. sMonster .. ".")
                                   bNewMonstersThisRoom = true
                               end
                        end
                    end

                    -- Burn monsters
                    if h == 0 and isSunny() then
                        for _, sMonster in ipairs(tMonsters) do
                            if room.items[sMonster] and items[sMonster].nocturnal then
                                room.items[sMonster] = nil
                                   if sx == 0 and sy == 0 and sz == 0 and not room.dark then
                                       print("\207\238\228 \255\240\234\232\236 \241\238\235\237\246\229\236 " .. sMonster .. " \226\241\239\251\245\232\226\224\229\242 \232 \239\238\227\232\225\224\229\242.")
                                   end
                                   room.nMonsters = room.nMonsters - 1
                               end
                        end
                    end
                end
            end
        end
    end

    -- Make monsters attack
    local room = getRoom(x, y, z)
    if nTimeInRoom >= 2 and not bNewMonstersThisRoom then
        for _, sMonster in ipairs(tMonsters) do
            if room.items[sMonster] then
                if math.random(1, 4) == 1 and
                   not (y == 0 and isSunny() and sMonster == "\239\224\243\234") then
                    if sMonster == "\234\240\232\239\229\240" then
                        if room.dark then
                            print("\202\240\232\239\229\240 \226\231\240\251\226\224\229\242\241\255.")
                        else
                            print("\202\240\232\239\229\240 \226\231\240\251\226\224\229\242\241\255.")
                        end
                        room.items[sMonster] = nil
                        room.nMonsters = room.nMonsters - 1
                    else
                        if room.dark then
                            print("\209\243\249\229\241\242\226\238 \171" .. sMonster .. "\187 \224\242\224\234\243\229\242 \226\224\241.")
                        else
                            print("\209\243\249\229\241\242\226\238 \171" .. sMonster .. "\187 \224\242\224\234\243\229\242 \226\224\241.")
                        end
                    end

                    if bInjured then
                        if term.isColour() then
                            term.setTextColour(colours.red)
                        end
                        print("\194\251 \239\238\227\232\225\235\232.")
                        print("\209\247\184\242: &e0")
                        term.setTextColour(colours.white)
                        bRunning = false
                        return
                    else
                        bInjured = true
                    end

                    break
                end
            end
        end
    end

    -- Always print this
    if bInjured then
        if term.isColour() then
            term.setTextColour(colours.red)
        end
        print("\194\251 \240\224\237\229\237\251.")
        term.setTextColour(colours.white)
    end

    -- Advance time
    nTurn = nTurn + 1
    nTimeInRoom = nTimeInRoom + 1
end

doCommand("look")
simulate()

local tCommandHistory = {}
while bRunning do
    if term.isColour() then
        term.setTextColour(colours.yellow)
    end
    write("? ")
    term.setTextColour(colours.white)

    local sRawLine = read(nil, tCommandHistory)
    table.insert(tCommandHistory, sRawLine)

    local sLine = nil
    for match in string.gmatch(sRawLine, "%a+") do
        if sLine then
            sLine = sLine .. " " .. string.lower(match)
        else
            sLine = string.lower(match)
        end
    end

    doCommand(sLine or "")
    if bRunning then
        simulate()
    end
end
