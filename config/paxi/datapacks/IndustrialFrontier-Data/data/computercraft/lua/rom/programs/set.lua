-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local pp = require "cc.pretty"

local tArgs = { ... }
if #tArgs == 0 then
    -- "set"
    local _, y = term.getCursorPos()
    local tSettings = {}
    for n, sName in ipairs(settings.getNames()) do
        tSettings[n] = textutils.serialize(sName) .. ": " .. textutils.serialize(settings.get(sName))
    end
    textutils.pagedPrint(table.concat(tSettings, "\n"), y - 3)

elseif #tArgs == 1 then
    -- "set foo"
    local sName = tArgs[1]
    local deets = settings.getDetails(sName)
    local msg = pp.text(sName, colors.cyan) .. ": " .. pp.pretty(deets.value)
    if deets.default ~= nil and deets.value ~= deets.default then
        msg = msg .. " (\239\238 \243\236\238\235\247\224\237\232\254: " .. pp.pretty(deets.default) .. ")"
    end
    pp.print(msg)
    if deets.description then print(deets.description) end

else
    -- "set foo bar"
    local sName = tArgs[1]
    local sValue = tArgs[2]
    local value
    if sValue == "true" then
        value = true
    elseif sValue == "false" then
        value = false
    elseif sValue == "nil" then
        value = nil
    elseif tonumber(sValue) then
        value = tonumber(sValue)
    else
        value = sValue
    end

    local option = settings.getDetails(sName)
    if value == nil then
        settings.unset(sName)
        print(textutils.serialize(sName) .. ": \231\237\224\247\229\237\232\229 \241\225\240\238\248\229\237\238")
    elseif option.type and option.type ~= type(value) then
        printError(("%s \237\229 \255\226\235\255\229\242\241\255 \228\238\239\243\241\242\232\236\251\236 \231\237\224\247\229\237\232\229\236 \242\232\239\224 %s."):format(textutils.serialize(sValue), option.type))
    else
        settings.set(sName, value)
        print(textutils.serialize(sName) .. ": " .. textutils.serialize(value))
    end

    if value ~= option.value then
        settings.save()
    end
end
