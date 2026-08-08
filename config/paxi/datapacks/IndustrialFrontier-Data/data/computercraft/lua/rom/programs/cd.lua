-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }
if #tArgs < 1 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <path>")
    return
end

local sNewDir = shell.resolve(tArgs[1])
if fs.isDir(sNewDir) then
    shell.setDir(sNewDir)
else
    print("\221\242\238 \237\229 \234\224\242\224\235\238\227")
    return
end
