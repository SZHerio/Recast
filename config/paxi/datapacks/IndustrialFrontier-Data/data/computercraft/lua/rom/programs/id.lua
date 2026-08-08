-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local sDrive = nil
local tArgs = { ... }
if #tArgs > 0 then
    sDrive = tostring(tArgs[1])
end

if sDrive == nil then
    print("\221\242\238 \234\238\236\239\252\254\242\229\240 \185" .. os.getComputerID())

    local label = os.getComputerLabel()
    if label then
        print("\204\229\242\234\224 \253\242\238\227\238 \234\238\236\239\252\254\242\229\240\224: \"" .. label .. "\"")
    end

else
    if disk.hasAudio(sDrive) then
        local title = disk.getAudioTitle(sDrive)
        if title then
            print("\192\243\228\232\238\231\224\239\232\241\252: \"" .. title .. "\"")
        else
            print("\197\241\242\252 \224\243\228\232\238\231\224\239\232\241\252 \225\229\231 \237\224\231\226\224\237\232\255")
        end
        return
    end

    if not disk.hasData(sDrive) then
        print("\194 \239\240\232\226\238\228\229 \237\229\242 \228\232\241\234\229\242\251: " .. sDrive)
        return
    end

    local id = disk.getID(sDrive)
    if id then
        print("\205\238\236\229\240 \228\232\241\234\229\242\251: " .. id)
    else
        print("\200\241\242\238\247\237\232\234 \228\224\237\237\251\245 \237\229 \255\226\235\255\229\242\241\255 \228\232\241\234\229\242\238\233")
    end

    local label = disk.getLabel(sDrive)
    if label then
        print("\204\229\242\234\224: \"" .. label .. "\"")
    end
end
