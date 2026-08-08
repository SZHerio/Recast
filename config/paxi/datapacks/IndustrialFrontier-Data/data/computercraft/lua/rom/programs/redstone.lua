-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }

local function printUsage()
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\194\224\240\232\224\237\242\251 \232\241\239\238\235\252\231\238\226\224\237\232\255:")
    print(programName .. " probe")
    print(programName .. " set <side> <value>")
    print(programName .. " set <side> <color> <value>")
    print(programName .. " pulse <side> <count> <period>")
end

local sCommand = tArgs[1]
if sCommand == "probe" then
    -- "redstone probe"
    -- Regular input
    print("\194\245\238\228\255\249\232\229 \241\232\227\237\224\235\251 \240\229\228\241\242\238\243\237\224: ")

    local count = 0
    local bundledCount = 0
    for _, sSide in ipairs(redstone.getSides()) do
        if redstone.getBundledInput(sSide) > 0 then
            bundledCount = bundledCount + 1
        end
        if redstone.getInput(sSide) then
            if count > 0 then
                io.write(", ")
            end
            io.write(sSide)
            count = count + 1
        end
    end
    if count > 0 then
        print(".")
    else
        print("\205\229\242.")
    end

    -- Bundled input
    if bundledCount > 0 then
        print()
        print("\194\245\238\228\255\249\232\229 \239\224\234\229\242\237\251\229 \241\232\227\237\224\235\251:")
        for _, sSide in ipairs(redstone.getSides()) do
            local nInput = redstone.getBundledInput(sSide)
            if nInput ~= 0 then
                write(sSide .. ": ")
                local count = 0
                for sColour, nColour in pairs(colors) do
                    if type(nColour) == "number" and colors.test(nInput, nColour) then
                        if count > 0 then
                            write(", ")
                        end
                        if term.isColour() then
                            term.setTextColour(nColour)
                        end
                        write(sColour)
                        if term.isColour() then
                            term.setTextColour(colours.white)
                        end
                        count = count + 1
                    end
                end
                print(".")
            end
        end
    end

elseif sCommand == "pulse" then
    -- "redstone pulse"
    local sSide = tArgs[2]
    local nCount = tonumber(tArgs[3]) or 1
    local nPeriod = tonumber(tArgs[4]) or 0.5
    for _ = 1, nCount do
        redstone.setOutput(sSide, true)
        sleep(nPeriod / 2)
        redstone.setOutput(sSide, false)
        sleep(nPeriod / 2)
    end

elseif sCommand == "set" then
    -- "redstone set"
    local sSide = tArgs[2]
    if #tArgs > 3 then
        -- Bundled cable output
        local sColour = tArgs[3]
        local nColour = colors[sColour] or colours[sColour]
        if type(nColour) ~= "number" then
            printError("\205\229\232\231\226\229\241\242\237\251\233 \246\226\229\242")
            return
        end

        local sValue = tArgs[4]
        if sValue == "true" then
            rs.setBundledOutput(sSide, colors.combine(rs.getBundledOutput(sSide), nColour))
        elseif sValue == "false" then
            rs.setBundledOutput(sSide, colors.subtract(rs.getBundledOutput(sSide), nColour))
        else
            print("\199\237\224\247\229\237\232\229 \228\238\235\230\237\238 \232\236\229\242\252 \242\232\239 boolean")
        end
    else
        -- Regular output
        local sValue = tArgs[3]
        local nValue = tonumber(sValue)
        if sValue == "true" then
            rs.setOutput(sSide, true)
        elseif sValue == "false" then
            rs.setOutput(sSide, false)
        elseif nValue and nValue >= 0 and nValue <= 15 then
            rs.setAnalogOutput(sSide, nValue)
        else
            print("\199\237\224\247\229\237\232\229 \228\238\235\230\237\238 \232\236\229\242\252 \242\232\239 boolean \232\235\232 \225\251\242\252 \247\232\241\235\238\236 \238\242 0 \228\238 15")
        end
    end

else
    -- Something else
    printUsage()

end
