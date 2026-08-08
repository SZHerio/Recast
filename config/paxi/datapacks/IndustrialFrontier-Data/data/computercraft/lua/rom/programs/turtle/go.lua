-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not turtle then
    printError("\210\240\229\225\243\229\242\241\255 \247\229\240\229\239\224\245\224")
    return
end

local tArgs = { ... }
if #tArgs < 1 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <direction> <distance>")
    return
end

local tHandlers = {
    ["fd"] = turtle.forward,
    ["forward"] = turtle.forward,
    ["forwards"] = turtle.forward,
    ["bk"] = turtle.back,
    ["back"] = turtle.back,
    ["up"] = turtle.up,
    ["dn"] = turtle.down,
    ["down"] = turtle.down,
    ["lt"] = turtle.turnLeft,
    ["left"] = turtle.turnLeft,
    ["rt"] = turtle.turnRight,
    ["right"] = turtle.turnRight,
}

local nArg = 1
while nArg <= #tArgs do
    local sDirection = tArgs[nArg]
    local nDistance = 1
    if nArg < #tArgs then
        local num = tonumber(tArgs[nArg + 1])
        if num then
            nDistance = num
            nArg = nArg + 1
        end
    end
    nArg = nArg + 1

    local fnHandler = tHandlers[string.lower(sDirection)]
    if fnHandler then
        while nDistance > 0 do
            if fnHandler() then
                nDistance = nDistance - 1
            elseif turtle.getFuelLevel() == 0 then
                print("\210\238\239\235\232\226\238 \231\224\234\238\237\247\232\235\238\241\252")
                return
            else
                sleep(0.5)
            end
        end
    else
        print("\205\229\232\231\226\229\241\242\237\238\229 \237\224\239\240\224\226\235\229\237\232\229: " .. sDirection)
        print("\196\238\241\242\243\239\237\251\229 \226\224\240\232\224\237\242\251: forward, back, up, down")
        return
    end

end
