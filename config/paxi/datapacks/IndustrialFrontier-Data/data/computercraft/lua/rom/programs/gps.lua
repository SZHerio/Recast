-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local function printUsage()
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\194\224\240\232\224\237\242\251 \232\241\239\238\235\252\231\238\226\224\237\232\255:")
    print(programName .. " host")
    print(programName .. " host <x> <y> <z>")
    print(programName .. " locate")
end

local tArgs = { ... }
if #tArgs < 1 then
    printUsage()
    return
end

 local sCommand = tArgs[1]
if sCommand == "locate" then
    -- "gps locate"
    -- Just locate this computer (this will print the results)
    gps.locate(2, true)

elseif sCommand == "host" then
    -- "gps host"
    -- Act as a GPS host
    if pocket then
        print("\209\229\240\226\229\240\251 GPS \228\238\235\230\237\251 \238\241\242\224\226\224\242\252\241\255 \237\229\239\238\228\226\232\230\237\251\236\232")
        return
    end

    -- Find a modem
    local sModemSide = nil
    for _, sSide in ipairs(rs.getSides()) do
        if peripheral.getType(sSide) == "modem" and peripheral.call(sSide, "isWireless") then
            sModemSide = sSide
            break
        end
    end

    if sModemSide == nil then
        print("\193\229\241\239\240\238\226\238\228\237\251\229 \236\238\228\229\236\251 \237\229 \237\224\233\228\229\237\251. \210\240\229\225\243\229\242\241\255 \238\228\232\237 \236\238\228\229\236.")
        return
    end

    -- Determine position
    local x, y, z
    if #tArgs >= 4 then
        -- Position is manually specified
        x = tonumber(tArgs[2])
        y = tonumber(tArgs[3])
        z = tonumber(tArgs[4])
        if x == nil or y == nil or z == nil then
            printUsage()
            return
        end
        print("\202\238\238\240\228\232\237\224\242\251: " .. x .. "," .. y .. "," .. z)
    else
        -- Position is to be determined using locate
        x, y, z = gps.locate(2, true)
        if x == nil then
            print("\199\224\239\243\241\242\232\242\229 \"gps host <x> <y> <z>\", \247\242\238\225\251 \231\224\228\224\242\252 \234\238\238\240\228\232\237\224\242\251 \226\240\243\247\237\243\254")
            return
        end
    end

    -- Open a channel
    local modem = peripheral.wrap(sModemSide)
    print("\206\242\234\240\251\226\224\254 \234\224\237\224\235 \237\224 \236\238\228\229\236\229 " .. sModemSide)
    modem.open(gps.CHANNEL_GPS)

    -- Serve requests indefinitely
    local nServed = 0
    while true do
        local e, p1, p2, p3, p4, p5 = os.pullEvent("modem_message")
        if e == "modem_message" then
            -- We received a message from a modem
            local sSide, sChannel, sReplyChannel, sMessage, nDistance = p1, p2, p3, p4, p5
            if sSide == sModemSide and sChannel == gps.CHANNEL_GPS and sMessage == "PING" and nDistance then
                -- We received a ping message on the GPS channel, send a response
                modem.transmit(sReplyChannel, gps.CHANNEL_GPS, { x, y, z })

                -- Print the number of requests handled
                nServed = nServed + 1
                if nServed > 1 then
                    local _, y = term.getCursorPos()
                    term.setCursorPos(1, y - 1)
                end
                print(nServed .. " - \238\225\240\224\225\238\242\224\237\238 \231\224\239\240\238\241\238\226 GPS")
            end
        end
    end
else
    -- "gps somethingelse"
    -- Error
    printUsage()
end
