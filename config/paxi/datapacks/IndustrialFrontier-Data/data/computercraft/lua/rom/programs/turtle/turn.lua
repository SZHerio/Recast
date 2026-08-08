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
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <direction> <turns>")
    return
end

local tHandlers = {
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
        for _ = 1, nDistance do
            fnHandler(nArg)
        end
    else
        print("\205\229\232\231\226\229\241\242\237\238\229 \237\224\239\240\224\226\235\229\237\232\229: " .. sDirection)
        print("\196\238\239\243\241\242\232\236\251\229 \231\237\224\247\229\237\232\255: left, right")
        return
    end
end
