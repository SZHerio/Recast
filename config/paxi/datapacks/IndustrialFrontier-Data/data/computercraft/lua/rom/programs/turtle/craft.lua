-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not turtle then
    printError("\210\240\229\225\243\229\242\241\255 \247\229\240\229\239\224\245\224")
    return
end

if not turtle.craft then
    print("\210\240\229\225\243\229\242\241\255 \247\229\240\229\239\224\245\224 \241 \226\229\240\241\242\224\234\238\236")
    return
end

local tArgs = { ... }
local nLimit = tonumber(tArgs[1])

if not nLimit and tArgs[1] ~= "all" then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " all|<number>")
    return
end

local nCrafted = 0
local nOldCount = turtle.getItemCount(turtle.getSelectedSlot())
if turtle.craft(nLimit) then
    local nNewCount = turtle.getItemCount(turtle.getSelectedSlot())
    if not nLimit or nOldCount <= nLimit then
        nCrafted = nNewCount
    else
        nCrafted = nOldCount - nNewCount
    end
end

if nCrafted > 1 then
    print(nCrafted .. " - \241\238\231\228\224\237\238 \239\240\229\228\236\229\242\238\226")
elseif nCrafted == 1 then
    print("\209\238\231\228\224\237 1 \239\240\229\228\236\229\242")
else
    print("\205\232\247\229\227\238 \237\229 \241\238\231\228\224\237\238")
end
