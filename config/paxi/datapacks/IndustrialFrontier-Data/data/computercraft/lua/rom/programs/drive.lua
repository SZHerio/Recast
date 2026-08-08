-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }

-- Get where a directory is mounted
local sPath = shell.dir()
if tArgs[1] ~= nil then
    sPath = shell.resolve(tArgs[1])
end

if fs.exists(sPath) then
    write(fs.getDrive(sPath) .. " (")
    local nSpace = fs.getFreeSpace(sPath)
    if nSpace >= 1000 * 1000 then
        print(math.floor(nSpace / (100 * 1000)) / 10 .. " \204\193 \241\226\238\225\238\228\237\238)")
    elseif nSpace >= 1000 then
        print(math.floor(nSpace / 100) / 10 .. " \202\193 \241\226\238\225\238\228\237\238)")
    else
        print(nSpace .. " \193 \241\226\238\225\238\228\237\238)")
    end
else
    print("\207\243\242\252 \237\229 \237\224\233\228\229\237")
end
