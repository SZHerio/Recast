-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not turtle then
    printError("\210\240\229\225\243\229\242\241\255 \247\229\240\229\239\224\245\224")
    return
end

local tArgs = { ... }
local function printUsage()
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <slot> <side>")
end

if #tArgs ~= 2 then
    printUsage()
    return
end

local function equip(nSlot, fnEquipFunction)
    turtle.select(nSlot)
    local nOldCount = turtle.getItemCount(nSlot)
    if nOldCount == 0 then
        print("\205\229\247\229\227\238 \243\241\242\224\237\224\226\235\232\226\224\242\252")
    elseif fnEquipFunction() then
        local nNewCount = turtle.getItemCount(nSlot)
        if nNewCount > 0 then
            print("\207\240\229\228\236\229\242\251 \239\238\236\229\237\255\237\251 \236\229\241\242\224\236\232")
        else
            print("\207\240\229\228\236\229\242 \243\241\242\224\237\238\226\235\229\237")
        end
    else
        print("\221\242\238\242 \239\240\229\228\236\229\242 \237\229\235\252\231\255 \243\241\242\224\237\238\226\232\242\252")
    end
end

local nSlot = tonumber(tArgs[1])
local sSide = tArgs[2]
if sSide == "left" then
    equip(nSlot, turtle.equipLeft)
elseif sSide == "right" then
    equip(nSlot, turtle.equipRight)
else
    printUsage()
    return
end
