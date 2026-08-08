-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

-- Get arguments
local tArgs = { ... }
if #tArgs == 0 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <drive>")
    return
end

local sDrive = tArgs[1]

-- Check the disk exists
local bPresent = disk.isPresent(sDrive)
if not bPresent then
    print("\194 \239\240\232\226\238\228\229 " .. sDrive .. " \237\232\247\229\227\238 \237\229\242")
    return
end

disk.eject(sDrive)
