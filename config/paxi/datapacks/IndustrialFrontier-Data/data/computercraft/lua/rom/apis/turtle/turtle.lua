-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

--- @module turtle

if not turtle then
    error("\205\229\235\252\231\255 \231\224\227\240\243\231\232\242\252 API turtle \237\224 \238\225\251\247\237\238\236 \234\238\236\239\252\254\242\229\240\229", 2)
end

--- The builtin turtle API, without any generated helper functions.
--
-- @deprecated Historically this table behaved differently to the main turtle API, but this is no longer the case. You
-- should not need to use it.
native = turtle.native or turtle

local function addCraftMethod(object)
    if peripheral.getType("left") == "workbench" then
        object.craft = function(...)
            return peripheral.call("left", "craft", ...)
        end
    elseif peripheral.getType("right") == "workbench" then
        object.craft = function(...)
            return peripheral.call("right", "craft", ...)
        end
    else
        object.craft = nil
    end
end

-- Put commands into environment table
local env = _ENV
for k, v in pairs(native) do
    if k == "equipLeft" or k == "equipRight" then
        env[k] = function(...)
            local result, err = v(...)
            addCraftMethod(turtle)
            return result, err
        end
    else
        env[k] = v
    end
end
addCraftMethod(env)
