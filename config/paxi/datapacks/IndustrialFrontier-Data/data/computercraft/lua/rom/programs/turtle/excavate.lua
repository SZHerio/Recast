-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not turtle then
    printError("\210\240\229\225\243\229\242\241\255 \247\229\240\229\239\224\245\224")
    return
end

local tArgs = { ... }
if #tArgs ~= 1 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <diameter>")
    return
end

-- Mine in a quarry pattern until we hit something we can't dig
local size = tonumber(tArgs[1])
if size < 1 then
    print("\196\232\224\236\229\242\240 \234\224\240\252\229\240\224 \228\238\235\230\229\237 \225\251\242\252 \239\238\235\238\230\232\242\229\235\252\237\251\236 \247\232\241\235\238\236")
    return
end

local depth = 0
local unloaded = 0
local collected = 0

local xPos, zPos = 0, 0
local xDir, zDir = 0, 1

local goTo -- Filled in further down
local refuel -- Filled in further down

local function unload(_bKeepOneFuelStack)
    print("\194\251\227\240\243\230\224\254 \239\240\229\228\236\229\242\251...")
    for n = 1, 16 do
        local nCount = turtle.getItemCount(n)
        if nCount > 0 then
            turtle.select(n)
            local bDrop = true
            if _bKeepOneFuelStack and turtle.refuel(0) then
                bDrop = false
                _bKeepOneFuelStack = false
            end
            if bDrop then
                turtle.drop()
                unloaded = unloaded + nCount
            end
        end
    end
    collected = 0
    turtle.select(1)
end

local function returnSupplies()
    local x, y, z, xd, zd = xPos, depth, zPos, xDir, zDir
    print("\194\238\231\226\240\224\249\224\254\241\252 \237\224 \239\238\226\229\240\245\237\238\241\242\252...")
    goTo(0, 0, 0, 0, -1)

    local fuelNeeded = 2 * (x + y + z) + 1
    if not refuel(fuelNeeded) then
        unload(true)
        print("\206\230\232\228\224\254 \242\238\239\235\232\226\238")
        while not refuel(fuelNeeded) do
            os.pullEvent("turtle_inventory")
        end
    else
        unload(true)
    end

    print("\207\240\238\228\238\235\230\224\254 \228\238\225\251\247\243...")
    goTo(x, y, z, xd, zd)
end

local function collect()
    local bFull = true
    local nTotalItems = 0
    for n = 1, 16 do
        local nCount = turtle.getItemCount(n)
        if nCount == 0 then
            bFull = false
        end
        nTotalItems = nTotalItems + nCount
    end

    if nTotalItems > collected then
        collected = nTotalItems
        if math.fmod(collected + unloaded, 50) == 0 then
            print("\196\238\225\251\242\238 \239\240\229\228\236\229\242\238\226: " .. collected + unloaded .. ".")
        end
    end

    if bFull then
        print("\209\226\238\225\238\228\237\251\245 \255\247\229\229\234 \237\229 \238\241\242\224\235\238\241\252.")
        return false
    end
    return true
end

function refuel(amount)
    local fuelLevel = turtle.getFuelLevel()
    if fuelLevel == "unlimited" then
        return true
    end

    local needed = amount or xPos + zPos + depth + 2
    if turtle.getFuelLevel() < needed then
        for n = 1, 16 do
            if turtle.getItemCount(n) > 0 then
                turtle.select(n)
                if turtle.refuel(1) then
                    while turtle.getItemCount(n) > 0 and turtle.getFuelLevel() < needed do
                        turtle.refuel(1)
                    end
                    if turtle.getFuelLevel() >= needed then
                        turtle.select(1)
                        return true
                    end
                end
            end
        end
        turtle.select(1)
        return false
    end

    return true
end

local function tryForwards()
    if not refuel() then
        print("\205\229\228\238\241\242\224\242\238\247\237\238 \242\238\239\235\232\226\224")
        returnSupplies()
    end

    while not turtle.forward() do
        if turtle.detect() then
            if turtle.dig() then
                if not collect() then
                    returnSupplies()
                end
            else
                return false
            end
        elseif turtle.attack() then
            if not collect() then
                returnSupplies()
            end
        else
            sleep(0.5)
        end
    end

    xPos = xPos + xDir
    zPos = zPos + zDir
    return true
end

local function tryDown()
    if not refuel() then
        print("\205\229\228\238\241\242\224\242\238\247\237\238 \242\238\239\235\232\226\224")
        returnSupplies()
    end

    while not turtle.down() do
        if turtle.detectDown() then
            if turtle.digDown() then
                if not collect() then
                    returnSupplies()
                end
            else
                return false
            end
        elseif turtle.attackDown() then
            if not collect() then
                returnSupplies()
            end
        else
            sleep(0.5)
        end
    end

    depth = depth + 1
    if math.fmod(depth, 10) == 0 then
        print("\195\235\243\225\232\237\224: " .. depth .. " \236.")
    end

    return true
end

local function turnLeft()
    turtle.turnLeft()
    xDir, zDir = -zDir, xDir
end

local function turnRight()
    turtle.turnRight()
    xDir, zDir = zDir, -xDir
end

function goTo(x, y, z, xd, zd)
    while depth > y do
        if turtle.up() then
            depth = depth - 1
        elseif turtle.digUp() or turtle.attackUp() then
            collect()
        else
            sleep(0.5)
        end
    end

    if xPos > x then
        while xDir ~= -1 do
            turnLeft()
        end
        while xPos > x do
            if turtle.forward() then
                xPos = xPos - 1
            elseif turtle.dig() or turtle.attack() then
                collect()
            else
                sleep(0.5)
            end
        end
    elseif xPos < x then
        while xDir ~= 1 do
            turnLeft()
        end
        while xPos < x do
            if turtle.forward() then
                xPos = xPos + 1
            elseif turtle.dig() or turtle.attack() then
                collect()
            else
                sleep(0.5)
            end
        end
    end

    if zPos > z then
        while zDir ~= -1 do
            turnLeft()
        end
        while zPos > z do
            if turtle.forward() then
                zPos = zPos - 1
            elseif turtle.dig() or turtle.attack() then
                collect()
            else
                sleep(0.5)
            end
        end
    elseif zPos < z then
        while zDir ~= 1 do
            turnLeft()
        end
        while zPos < z do
            if turtle.forward() then
                zPos = zPos + 1
            elseif turtle.dig() or turtle.attack() then
                collect()
            else
                sleep(0.5)
            end
        end
    end

    while depth < y do
        if turtle.down() then
            depth = depth + 1
        elseif turtle.digDown() or turtle.attackDown() then
            collect()
        else
            sleep(0.5)
        end
    end

    while zDir ~= zd or xDir ~= xd do
        turnLeft()
    end
end

if not refuel() then
    print("\210\238\239\235\232\226\238 \231\224\234\238\237\247\232\235\238\241\252")
    return
end

print("\205\224\247\232\237\224\254 \240\224\231\240\224\225\238\242\234\243 \234\224\240\252\229\240\224...")

local reseal = false
turtle.select(1)
if turtle.digDown() then
    reseal = true
end

local alternate = 0
local done = false
while not done do
    for n = 1, size do
        for _ = 1, size - 1 do
            if not tryForwards() then
                done = true
                break
            end
        end
        if done then
            break
        end
        if n < size then
            if math.fmod(n + alternate, 2) == 0 then
                turnLeft()
                if not tryForwards() then
                    done = true
                    break
                end
                turnLeft()
            else
                turnRight()
                if not tryForwards() then
                    done = true
                    break
                end
                turnRight()
            end
        end
    end
    if done then
        break
    end

    if size > 1 then
        if math.fmod(size, 2) == 0 then
            turnRight()
        else
            if alternate == 0 then
                turnLeft()
            else
                turnRight()
            end
            alternate = 1 - alternate
        end
    end

    if not tryDown() then
        done = true
        break
    end
end

print("\194\238\231\226\240\224\249\224\254\241\252 \237\224 \239\238\226\229\240\245\237\238\241\242\252...")

-- Return to where we started
goTo(0, 0, 0, 0, -1)
unload(false)
goTo(0, 0, 0, 0, 1)

-- Seal the hole
if reseal then
    turtle.placeDown()
end

print("\196\238\225\251\242\238 \239\240\229\228\236\229\242\238\226: " .. collected + unloaded .. ".")
