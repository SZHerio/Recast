-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }
if not commands then
    printError("\210\240\229\225\243\229\242\241\255 \234\238\236\224\237\228\237\251\233 \234\238\236\239\252\254\242\229\240.")
    return
end
if #tArgs == 0 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    printError("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <command>")
    return
end

local function printSuccess(text)
    if term.isColor() then
        term.setTextColor(colors.green)
    end
    print(text)
    term.setTextColor(colors.white)
end

local sCommand = string.lower(tArgs[1])
for n = 2, #tArgs do
    sCommand = sCommand .. " " .. tArgs[n]
end

local bResult, tOutput = commands.exec(sCommand)
if bResult then
    printSuccess("\211\241\239\229\248\237\238")
    if #tOutput > 0 then
        for n = 1, #tOutput do
            print(tOutput[n])
        end
    end
else
    printError("\206\248\232\225\234\224")
    if #tOutput > 0 then
        for n = 1, #tOutput do
            print(tOutput[n])
        end
    end
end
