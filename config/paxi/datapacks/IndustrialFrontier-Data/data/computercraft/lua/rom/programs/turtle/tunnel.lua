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
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <length>")
    return
end

-- Mine in a quarry pattern until we hit something we can't dig
local length = tonumber(tArgs[1])
if length < 1 then
    print("\196\235\232\237\224 \242\243\237\237\229\235\255 \228\238\235\230\237\224 \225\251\242\252 \239\238\235\238\230\232\242\229\235\252\237\251\236 \247\232\241\235\238\236")
    return
end
local collected = 0

local function collect()
    collected = collected + 1
    if math.fmod(collected, 25) == 0 then
        print("\196\238\225\251\242\238 \239\240\229\228\236\229\242\238\226: " .. collected .. ".")
    end
end

local function tryDig()
    while turtle.detect() do
        if turtle.dig() then
            collect()
            sleep(0.5)
        else
            return false
        end
    end
    return true
end

local function tryDigUp()
    while turtle.detectUp() do
        if turtle.digUp() then
            collect()
            sleep(0.5)
        else
            return false
        end
    end
    return true
end

local function tryDigDown()
    while turtle.detectDown() do
        if turtle.digDown() then
            collect()
            sleep(0.5)
        else
            return false
        end
    end
    return true
end

local function refuel()
    local fuelLevel = turtle.getFuelLevel()
    if fuelLevel == "unlimited" or fuelLevel > 0 then
        return
    end

    local function tryRefuel()
        for n = 1, 16 do
            if turtle.getItemCount(n) > 0 then
                turtle.select(n)
                if turtle.refuel(1) then
                    turtle.select(1)
                    return true
                end
            end
        end
        turtle.select(1)
        return false
    end

    if not tryRefuel() then
        print("\196\238\225\224\226\252\242\229 \242\238\239\235\232\226\238, \247\242\238\225\251 \239\240\238\228\238\235\230\232\242\252.")
        while not tryRefuel() do
            os.pullEvent("turtle_inventory")
        end
        print("\207\240\238\228\238\235\230\224\254 \239\240\238\234\235\224\228\251\226\224\242\252 \242\243\237\237\229\235\252.")
    end
end

local function tryUp()
    refuel()
    while not turtle.up() do
        if turtle.detectUp() then
            if not tryDigUp() then
                return false
            end
        elseif turtle.attackUp() then
            collect()
        else
            sleep(0.5)
        end
    end
    return true
end

local function tryDown()
    refuel()
    while not turtle.down() do
        if turtle.detectDown() then
            if not tryDigDown() then
                return false
            end
        elseif turtle.attackDown() then
            collect()
        else
            sleep(0.5)
        end
    end
    return true
end

local function tryForward()
    refuel()
    while not turtle.forward() do
        if turtle.detect() then
            if not tryDig() then
                return false
            end
        elseif turtle.attack() then
            collect()
        else
            sleep(0.5)
        end
    end
    return true
end

print("\207\240\238\234\235\224\228\251\226\224\254 \242\243\237\237\229\235\252...")

for n = 1, length do
    turtle.placeDown()
    tryDigUp()
    turtle.turnLeft()
    tryDig()
    tryUp()
    tryDig()
    turtle.turnRight()
    turtle.turnRight()
    tryDig()
    tryDown()
    tryDig()
    turtle.turnLeft()

    if n < length then
        tryDig()
        if not tryForward() then
            print("\207\240\238\234\235\224\228\234\224 \242\243\237\237\229\235\255 \239\240\229\240\226\224\237\224.")
            break
        end
    else
        print("\210\243\237\237\229\235\252 \227\238\242\238\226.")
    end

end

--[[
print( "Returning to start..." )

-- Return to where we started
turtle.turnLeft()
turtle.turnLeft()
while depth > 0 do
    if turtle.forward() then
        depth = depth - 1
    else
        turtle.dig()
    end
end
turtle.turnRight()
turtle.turnRight()
]]

print("\210\243\237\237\229\235\252 \227\238\242\238\226.")
print("\196\238\225\251\242\238 \239\240\229\228\236\229\242\238\226: " .. collected .. ".")
