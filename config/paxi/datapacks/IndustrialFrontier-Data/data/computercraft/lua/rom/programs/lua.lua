-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }
if #tArgs > 0 then
    print("\221\242\238 \232\237\242\229\240\224\234\242\232\226\237\224\255 \234\238\237\241\238\235\252 Lua.")
    print("\215\242\238\225\251 \231\224\239\243\241\242\232\242\252 \239\240\238\227\240\224\236\236\243 Lua, \226\226\229\228\232\242\229 \229\184 \232\236\255.")
    return
end

local pretty = require "cc.pretty"
local exception = require "cc.internal.exception"

local running = true
local tCommandHistory = {}
local tEnv = {
    ["exit"] = setmetatable({}, {
        __tostring = function() return "\196\235\255 \226\251\245\238\228\224 \226\251\231\238\226\232\242\229 exit()." end,
        __call = function() running = false end,
    }),
    ["_echo"] = function(...)
        return ...
    end,
}
setmetatable(tEnv, { __index = _ENV })

-- Replace our require with new instance that loads from the current directory
-- rather than from /rom/programs. This makes it more friendly to use and closer
-- to what you'd expect.
do
    local make_package = require "cc.require".make
    local dir = shell.dir()
    tEnv.require, tEnv.package = make_package(tEnv, dir)
end

if term.isColour() then
    term.setTextColour(colours.yellow)
end
print("\200\237\242\229\240\224\234\242\232\226\237\224\255 \234\238\237\241\238\235\252 Lua.")
print("\196\235\255 \226\251\245\238\228\224 \226\251\231\238\226\232\242\229 exit().")
term.setTextColour(colours.white)

local chunk_idx, chunk_map = 1, {}
while running do
    --if term.isColour() then
    --    term.setTextColour( colours.yellow )
    --end
    write("lua> ")
    --term.setTextColour( colours.white )

    local input = read(nil, tCommandHistory, function(sLine)
        if settings.get("lua.autocomplete") then
            local nStartPos = string.find(sLine, "[a-zA-Z0-9_%.:]+$")
            if nStartPos then
                sLine = string.sub(sLine, nStartPos)
            end
            if #sLine > 0 then
                return textutils.complete(sLine, tEnv)
            end
        end
        return nil
    end)
    if input:match("%S") and tCommandHistory[#tCommandHistory] ~= input then
        table.insert(tCommandHistory, input)
    end
    if settings.get("lua.warn_against_use_of_local") and input:match("^%s*local%s+") then
        if term.isColour() then
            term.setTextColour(colours.yellow)
        end
       print("\215\242\238\225\251 \238\225\240\224\249\224\242\252\241\255 \234 \235\238\234\224\235\252\237\251\236 \239\229\240\229\236\229\237\237\251\236 \226 \241\235\229\228\243\254\249\232\245 \234\238\236\224\237\228\224\245, \243\225\229\240\232\242\229 \234\235\254\247\229\226\238\229 \241\235\238\226\238 local.")
       term.setTextColour(colours.white)
    end

    local name, offset = "=lua[" .. chunk_idx .. "]", 0

    local func, err = load(input, name, "t", tEnv)
    if load("return " .. input) then
        -- We wrap the expression with a call to _echo(...), which prevents tail
        -- calls (and thus confusing errors). Note we check this is a valid
        -- expression separately, to avoid accepting inputs like `)--` (which are
        -- parsed as `_echo()--)`.
        func = load("return _echo(" .. input .. "\n)", name, "t", tEnv)
        offset = 13
    end

    if func then
        chunk_map[name] = { contents = input, offset = offset }
        chunk_idx = chunk_idx + 1

        local results = table.pack(exception.try(func))
        if results[1] then
            for i = 2, results.n do
                local value = results[i]
                local ok, serialised = pcall(pretty.pretty, value, {
                    function_args = settings.get("lua.function_args"),
                    function_source = settings.get("lua.function_source"),
                })
                if ok then
                    pretty.print(serialised)
                else
                    print(tostring(value))
                end
            end
        else
            printError(results[2])
            exception.report(results[2], results[3], chunk_map)
        end
    else
        local parser = require "cc.internal.syntax"
        if parser.parse_repl(input) then printError(err) end
    end

end
