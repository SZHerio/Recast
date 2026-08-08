-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not turtle then
    printError("\210\240\229\225\243\229\242\241\255 \247\229\240\229\239\224\245\224")
    return
end

local tArgs = { ... }
local nLimit = 1
if #tArgs > 1 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " [number]")
    return
elseif #tArgs > 0 then
    if tArgs[1] == "all" then
        nLimit = nil
    else
        nLimit = tonumber(tArgs[1])
        if not nLimit then
            print("\205\229\228\238\239\243\241\242\232\236\251\233 \239\240\229\228\229\235: \243\234\224\230\232\242\229 \247\232\241\235\238 \232\235\232 \"all\"")
            return
        end
    end
end

if turtle.getFuelLevel() ~= "unlimited" then
    for n = 1, 16 do
        -- Stop if we've reached the limit, or are fully refuelled.
        if nLimit and nLimit <= 0 or turtle.getFuelLevel() >= turtle.getFuelLimit() then
            break
        end

        local nCount = turtle.getItemCount(n)
        if nCount > 0 then
            turtle.select(n)
            if turtle.refuel(nLimit) and nLimit then
                local nNewCount = turtle.getItemCount(n)
                nLimit = nLimit - (nCount - nNewCount)
            end
        end
    end
    print("\211\240\238\226\229\237\252 \242\238\239\235\232\226\224: " .. turtle.getFuelLevel())
    if turtle.getFuelLevel() == turtle.getFuelLimit() then
        print("\196\238\241\242\232\227\237\243\242 \239\240\229\228\229\235 \231\224\239\224\241\224 \242\238\239\235\232\226\224")
    end
else
    print("\199\224\239\224\241 \242\238\239\235\232\226\224 \237\229 \238\227\240\224\237\232\247\229\237")
end
