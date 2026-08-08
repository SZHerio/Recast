-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }

local function printUsage()
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\194\224\240\232\224\237\242\251 \232\241\239\238\235\252\231\238\226\224\237\232\255:")
    print(programName .. " play")
    print(programName .. " play <drive>")
    print(programName .. " stop")
end

if #tArgs > 2 then
    printUsage()
    return
end

local sCommand = tArgs[1]
if sCommand == "stop" then
    -- Stop audio
    disk.stopAudio()

elseif sCommand == "play" or sCommand == nil then
    -- Play audio
    local sName = tArgs[2]
    if sName == nil then
        -- No disc specified, pick one at random
        local tNames = {}
        for _, sName in ipairs(peripheral.getNames()) do
            if disk.isPresent(sName) and disk.hasAudio(sName) then
                table.insert(tNames, sName)
            end
        end
        if #tNames == 0 then
            print("\194 \239\238\228\234\235\254\247\184\237\237\251\245 \228\232\241\234\238\226\238\228\224\245 \237\229\242 \236\243\231\251\234\224\235\252\237\251\245 \239\235\224\241\242\232\237\238\234")
            return
        end
        sName = tNames[math.random(1, #tNames)]
    end

    -- Play the disc
    if disk.isPresent(sName) and disk.hasAudio(sName) then
        print("\209\229\233\247\224\241 \232\227\240\224\229\242: " .. disk.getAudioTitle(sName))
        disk.playAudio(sName)
    else
        print("\194 \228\232\241\234\238\226\238\228\229 \237\229\242 \236\243\231\251\234\224\235\252\237\238\233 \239\235\224\241\242\232\237\234\232: " .. sName)
        return
    end

else
    printUsage()

end
