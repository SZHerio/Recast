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
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <side>")
end

if #tArgs ~= 1 then
    printUsage()
    return
end

local function unequip(fnEquipFunction)
    for nSlot = 1, 16 do
        local nOldCount = turtle.getItemCount(nSlot)
        if nOldCount == 0 then
            turtle.select(nSlot)
            if fnEquipFunction() then
                local nNewCount = turtle.getItemCount(nSlot)
                if nNewCount > 0 then
                    print("\207\240\229\228\236\229\242 \241\237\255\242")
                    return
                else
                    print("\205\229\247\229\227\238 \241\237\232\236\224\242\252")
                    return
                end
            end
        end
    end
    print("\205\229\242 \236\229\241\242\224 \228\235\255 \241\237\255\242\238\227\238 \239\240\229\228\236\229\242\224")
end

local sSide = tArgs[1]
if sSide == "left" then
    unequip(turtle.equipLeft)
elseif sSide == "right" then
    unequip(turtle.equipRight)
else
    printUsage()
    return
end
