-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local function printUsage()
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\194\224\240\232\224\237\242\251 \232\241\239\238\235\252\231\238\226\224\237\232\255:")
    print(programName .. " get")
    print(programName .. " get <drive>")
    print(programName .. " set <text>")
    print(programName .. " set <drive> <text>")
    print(programName .. " clear")
    print(programName .. " clear <drive>")
end

local function checkDrive(sDrive)
    if peripheral.getType(sDrive) == "drive" then
        -- Check the disk exists
        local bData = disk.hasData(sDrive)
        if not bData then
            print("\194 \239\240\232\226\238\228\229 " .. sDrive .. " \237\229\242 \228\232\241\234\229\242\251")
            return false
        end
    else
        print("\196\232\241\234\238\226\238\228 \237\229 \237\224\233\228\229\237: " .. sDrive)
        return false
    end
    return true
end

local function get(sDrive)
    if sDrive ~= nil then
        if checkDrive(sDrive) then
            local sLabel = disk.getLabel(sDrive)
            if sLabel then
                print("\204\229\242\234\224 \228\232\241\234\229\242\251: \"" .. sLabel .. "\"")
            else
                print("\211 \228\232\241\234\229\242\251 \237\229\242 \236\229\242\234\232")
            end
        end
    else
        local sLabel = os.getComputerLabel()
        if sLabel then
            print("\204\229\242\234\224 \234\238\236\239\252\254\242\229\240\224: \"" .. sLabel .. "\"")
        else
            print("\211 \234\238\236\239\252\254\242\229\240\224 \237\229\242 \236\229\242\234\232")
        end
    end
end

local function set(sDrive, sText)
    if sDrive ~= nil then
        if checkDrive(sDrive) then
            disk.setLabel(sDrive, sText)
            local sLabel = disk.getLabel(sDrive)
            if sLabel then
                print("\204\229\242\234\224 \228\232\241\234\229\242\251 \243\241\242\224\237\238\226\235\229\237\224: \"" .. sLabel .. "\"")
            else
                print("\204\229\242\234\224 \228\232\241\234\229\242\251 \243\228\224\235\229\237\224")
            end
        end
    else
        os.setComputerLabel(sText)
        local sLabel = os.getComputerLabel()
        if sLabel then
            print("\204\229\242\234\224 \234\238\236\239\252\254\242\229\240\224 \243\241\242\224\237\238\226\235\229\237\224: \"" .. sLabel .. "\"")
        else
            print("\204\229\242\234\224 \234\238\236\239\252\254\242\229\240\224 \243\228\224\235\229\237\224")
        end
    end
end

local tArgs = { ... }
local sCommand = tArgs[1]
if sCommand == "get" then
    -- Get a label
    if #tArgs == 1 then
        get(nil)
    elseif #tArgs == 2 then
        get(tArgs[2])
    else
        printUsage()
    end
elseif sCommand == "set" then
    -- Set a label
    if #tArgs == 2 then
        set(nil, tArgs[2])
    elseif #tArgs == 3 then
        set(tArgs[2], tArgs[3])
    else
        printUsage()
    end
elseif sCommand == "clear" then
    -- Clear a label
    if #tArgs == 1 then
        set(nil, nil)
    elseif #tArgs == 2 then
        set(tArgs[2], nil)
    else
        printUsage()
    end
else
    printUsage()
end
