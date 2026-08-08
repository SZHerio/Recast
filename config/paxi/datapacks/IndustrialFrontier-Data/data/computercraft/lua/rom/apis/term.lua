-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

--- @module term

local expect = dofile("rom/modules/main/cc/expect.lua").expect

local native = term.native and term.native() or term
local redirectTarget = native

local function wrap(_sFunction)
    return function(...)
        return redirectTarget[_sFunction](...)
    end
end

local term = _ENV

--- Redirects terminal output to a monitor, a [`window`], or any other custom
-- terminal object. Once the redirect is performed, any calls to a "term"
-- function - or to a function that makes use of a term function, as [`print`] -
-- will instead operate with the new terminal object.
--
-- A "terminal object" is simply a table that contains functions with the same
-- names - and general features - as those found in the term table. For example,
-- a wrapped monitor is suitable.
--
-- The redirect can be undone by pointing back to the previous terminal object
-- (which this function returns whenever you switch).
--
-- @tparam Redirect target The terminal redirect the [`term`] API will draw to.
-- @treturn Redirect The previous redirect object, as returned by
-- [`term.current`].
-- @since 1.31
-- @usage
-- Redirect to a monitor on the right of the computer.
--
--     term.redirect(peripheral.wrap("right"))
term.redirect = function(target)
    expect(1, target, "table")
    if target == term or target == _G.term then
        error("\205\229 \240\229\234\238\236\229\237\228\243\229\242\241\255 \239\229\240\229\237\224\239\240\224\226\235\255\242\252 \226\251\226\238\228 \226 term; \232\241\239\238\235\252\231\243\233\242\229 term.current()", 2)
    end
    for k, v in pairs(native) do
        if type(k) == "string" and type(v) == "function" then
            if type(target[k]) ~= "function" then
                target[k] = function()
                    error("\211 \238\225\250\229\234\242\224 \239\229\240\229\237\224\239\240\224\226\235\229\237\232\255 \237\229\242 \236\229\242\238\228\224 " .. k .. ".", 2)
                end
            end
        end
    end
    local oldRedirectTarget = redirectTarget
    redirectTarget = target
    return oldRedirectTarget
end

--- Returns the current terminal object of the computer.
--
-- @treturn Redirect The current terminal redirect
-- @since 1.6
-- @usage
-- Create a new [`window`] which draws to the current redirect target.
--
--     window.create(term.current(), 1, 1, 10, 10)
term.current = function()
    return redirectTarget
end

--- Get the native terminal object of the current computer.
--
-- It is recommended you do not use this function unless you absolutely have
-- to. In a multitasked environment, [`term.native`] will _not_ be the current
-- terminal object, and so drawing may interfere with other programs.
--
-- @treturn Redirect The native terminal redirect.
-- @since 1.6
term.native = function()
    return native
end

-- Some methods shouldn't go through redirects, so we move them to the main
-- term API.
for _, method in ipairs { "nativePaletteColor", "nativePaletteColour" } do
    term[method] = native[method]
    native[method] = nil
end

for k, v in pairs(native) do
    if type(k) == "string" and type(v) == "function" and rawget(term, k) == nil then
        term[k] = wrap(k)
    end
end
