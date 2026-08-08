-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }

if #tArgs < 1 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <paths>")
    return
end

for _, v in ipairs(tArgs) do
    local sNewDir = shell.resolve(v)
    if fs.exists(sNewDir) and not fs.isDir(sNewDir) then
        printError(v .. ": \239\243\242\252 \237\224\231\237\224\247\229\237\232\255 \243\230\229 \241\243\249\229\241\242\226\243\229\242")
    elseif fs.isReadOnly(sNewDir) then
        printError(v .. ": \228\238\241\242\243\239 \231\224\239\240\229\249\184\237")
    else
        fs.makeDir(sNewDir)
    end
end
