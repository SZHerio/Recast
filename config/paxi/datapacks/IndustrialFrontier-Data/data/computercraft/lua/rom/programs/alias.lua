-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }
if #tArgs > 2 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <alias> <program>")
    return
end

local sAlias = tArgs[1]
local sProgram = tArgs[2]

if sAlias and sProgram then
    -- Set alias
    shell.setAlias(sAlias, sProgram)
elseif sAlias then
    -- Clear alias
    shell.clearAlias(sAlias)
else
    -- List aliases
    local tAliases = shell.aliases()
    local tList = {}
    for sAlias, sCommand in pairs(tAliases) do
        table.insert(tList, sAlias .. ":" .. sCommand)
    end
    table.sort(tList)
    textutils.pagedTabulate(tList)
end
