-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }
if #tArgs < 1 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <path>")
    return
end

local sPath = shell.resolve(tArgs[1])
if fs.exists(sPath) then
    if fs.isDir(sPath) then
        print("\234\224\242\224\235\238\227")
    else
        print("\244\224\233\235")
    end
else
    print("\207\243\242\252 \237\229 \237\224\233\228\229\237")
end
