-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

-- Get file to edit
local tArgs = { ... }
if #tArgs == 0 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <path>")
    return
end

-- Error checking
local sPath = shell.resolve(tArgs[1])
local bReadOnly = fs.isReadOnly(sPath)
if fs.exists(sPath) and fs.isDir(sPath) then
    print("\205\229\235\252\231\255 \240\229\228\224\234\242\232\240\238\226\224\242\252 \234\224\242\224\235\238\227.")
    return
end

-- Create .lua files by default
if not fs.exists(sPath) and not string.find(sPath, "%.") then
    local sExtension = settings.get("edit.default_extension")
    if sExtension ~= "" and type(sExtension) == "string" then
        sPath = sPath .. "." .. sExtension
    end
end

local x, y = 1, 1
local w, h = term.getSize()
local scrollX, scrollY = 0, 0

local tLines, tLineLexStates = {}, {}
local bRunning = true

-- Colours
local isColour = term.isColour()
local highlightColour, keywordColour, textColour, bgColour, errorColour
if isColour then
    bgColour = colours.black
    textColour = colours.white
    highlightColour = colours.yellow
    keywordColour = colours.yellow
    errorColour = colours.red
else
    bgColour = colours.black
    textColour = colours.white
    highlightColour = colours.white
    keywordColour = colours.white
    errorColour = colours.white
end

-- Menus
local menu  = require "cc.internal.menu"
local current_menu
local menu_items = {}
if not bReadOnly then
    table.insert(menu_items, "\209\238\245\240\224\237\232\242\252")
end
if shell.openTab then
    table.insert(menu_items, "\199\224\239\243\241\242\232\242\252")
end
if peripheral.find("printer") then
    table.insert(menu_items, "\207\229\247\224\242\252")
end
table.insert(menu_items, "\194\251\233\242\232")

local status_ok, status_text
local function set_status(text, ok)
    status_ok = ok ~= false
    status_text = text
end

if bReadOnly then
    set_status("\212\224\233\235 \228\238\241\242\243\239\229\237 \242\238\235\252\234\238 \228\235\255 \247\242\229\237\232\255", false)
elseif fs.getFreeSpace(sPath) < 1024 then
    set_status("\205\224 \228\232\241\234\229 \236\224\235\238 \236\229\241\242\224", false)
else
    local message
    if term.isColour() then
        message = "\205\224\230\236\232\242\229 Ctrl \232\235\232 \249\184\235\234\237\232\242\229 \231\228\229\241\252, \247\242\238\225\251 \238\242\234\240\251\242\252 \236\229\237\254"
    else
        message = "\205\224\230\236\232\242\229 Ctrl, \247\242\238\225\251 \238\242\234\240\251\242\252 \236\229\237\254"
    end

    if #message > w - 5 then
        message = "\205\224\230\236\232\242\229 Ctrl, \247\242\238\225\251 \238\242\234\240\251\242\252 \236\229\237\254"
    end

    set_status(message)
end

local function load(_sPath)
    tLines = {}
    if fs.exists(_sPath) then
        local file = io.open(_sPath, "r")
        local sLine = file:read()
        while sLine do
            table.insert(tLines, sLine)
            table.insert(tLineLexStates, false)
            sLine = file:read()
        end
        file:close()
    end

    if #tLines == 0 then
        table.insert(tLines, "")
        table.insert(tLineLexStates, false)
    end
end

local function save(_sPath, fWrite)
    -- Create intervening folder
    local sDir = _sPath:sub(1, _sPath:len() - fs.getName(_sPath):len())
    if not fs.exists(sDir) then
        fs.makeDir(sDir)
    end

    -- Save
    local file, fileerr
    local function innerSave()
        file, fileerr = fs.open(_sPath, "w")
        if file then
            if file then
                fWrite(file)
            end
        else
            error("\205\229 \243\228\224\235\238\241\252 \238\242\234\240\251\242\252 " .. _sPath)
        end
    end

    local ok, err = pcall(innerSave)
    if file then
        file.close()
    end
    return ok, err, fileerr
end


local tokens = require "cc.internal.syntax.parser".tokens
local lex_one = require "cc.internal.syntax.lexer".lex_one

local token_colours = {
    [tokens.STRING] = isColour and colours.red or textColour,
    [tokens.COMMENT] = isColour and colours.green or colours.lightGrey,
    [tokens.NUMBER] = isColour and colours.magenta or textColour,
    -- Keywords
    [tokens.AND] = keywordColour,
    [tokens.BREAK] = keywordColour,
    [tokens.DO] = keywordColour,
    [tokens.ELSE] = keywordColour,
    [tokens.ELSEIF] = keywordColour,
    [tokens.END] = keywordColour,
    [tokens.FALSE] = keywordColour,
    [tokens.FOR] = keywordColour,
    [tokens.FUNCTION] = keywordColour,
    [tokens.GOTO] = keywordColour,
    [tokens.IF] = keywordColour,
    [tokens.IN] = keywordColour,
    [tokens.LOCAL] = keywordColour,
    [tokens.NIL] = keywordColour,
    [tokens.NOT] = keywordColour,
    [tokens.OR] = keywordColour,
    [tokens.REPEAT] = keywordColour,
    [tokens.RETURN] = keywordColour,
    [tokens.THEN] = keywordColour,
    [tokens.TRUE] = keywordColour,
    [tokens.UNTIL] = keywordColour,
    [tokens.WHILE] = keywordColour,
}
-- Fill in the remaining tokens.
for _, token in pairs(tokens) do
    if not token_colours[token] then token_colours[token] = textColour end
end

local lex_context = { line = function() end, report = function() end }

local tCompletions
local nCompletion

local tCompleteEnv = _ENV
local function complete(sLine)
    if settings.get("edit.autocomplete") then
        local nStartPos = string.find(sLine, "[a-zA-Z0-9_%.:]+$")
        if nStartPos then
            sLine = string.sub(sLine, nStartPos)
        end
        if #sLine > 0 then
            return textutils.complete(sLine, tCompleteEnv)
        end
    end
    return nil
end

local function recomplete()
    local sLine = tLines[y]
    if not bReadOnly and x == #sLine + 1 then
        tCompletions = complete(sLine)
        if tCompletions and #tCompletions > 0 then
            nCompletion = 1
        else
            nCompletion = nil
        end
    else
        tCompletions = nil
        nCompletion = nil
    end
end

local function writeCompletion(sLine)
    if nCompletion then
        local sCompletion = tCompletions[nCompletion]
        term.setTextColor(colours.white)
        term.setBackgroundColor(colours.grey)
        term.write(sCompletion)
        term.setTextColor(textColour)
        term.setBackgroundColor(bgColour)
    end
end

--- Check if two values are equal. If both values are lists, then the contents will be
-- checked for equality, to a depth of 1.
--
-- @param x The first value.
-- @param x The second value.
-- @treturn boolean Whether the values are equal.
local function shallowEqual(x, y)
    if x == y then return true end

    if type(x) ~= "table" or type(y) ~= "table" then return false end
    if #x ~= #y then return false end

    for i = 1, #x do if x[i] ~= y[i] then return false end end
    return true
end

local function redrawLines(line, endLine)
    if not endLine then endLine = line end

    local colour = term.getTextColour()

    -- Highlight all lines between line and endLine, highlighting further lines if their
    -- lexer state has changed and aborting at the end of the screen.
    local changed = false
    while (changed or line <= endLine) and line - scrollY < h do
        term.setCursorPos(1 - scrollX, line - scrollY)
        term.clearLine()

        local contents = tLines[line]
        if not contents then break end

        -- Lex our first token, either taking our continuation state (if present) or
        -- the default lexer.
        local pos, token, _, finish, continuation = 1
        local lex_state = tLineLexStates[line]
        if lex_state then
            token, finish, _, continuation = lex_state[1](lex_context, contents, table.unpack(lex_state, 2))
        else
            token, _, finish, _, continuation = lex_one(lex_context, contents, 1)
        end

        while token do
            -- Print out that token
            local new_colour = token_colours[token]
            if new_colour ~= colour then
                term.setTextColor(new_colour)
                colour = new_colour
            end
            term.write(contents:sub(pos, finish))

            pos = finish + 1

            -- If we have a continuation, then we've reached the end of the line. Abort.
            if continuation then break end

            -- Otherwise lex another token and continue.
            token, _, finish, _, continuation = lex_one(lex_context, contents, pos)
        end

        -- Print the rest of the line. We don't strictly speaking need this, as it will
        -- only ever contain whitespace.
        term.write(contents:sub(pos))

        if line == y and x == #contents + 1 then
            writeCompletion()
            colour = term.getTextColour()
        end

        line = line + 1

        -- Update the lext state of the next line. If that has changed, then
        -- re-highlight it too. We store the continuation as nil rather than
        -- false, to ensure we use the array part of the table.
        if continuation == nil then continuation = false end
        if tLineLexStates[line] ~= nil and not shallowEqual(tLineLexStates[line], continuation) then
            tLineLexStates[line] = continuation or false
            changed = true
        else
            changed = false
        end
    end

    term.setTextColor(colours.white)
    term.setCursorPos(x - scrollX, y - scrollY)
end

local function redrawText()
    redrawLines(scrollY + 1, scrollY + h - 1)
end

local function redrawMenu()
    -- Clear line
    term.setCursorPos(1, h)
    term.clearLine()

    -- Draw line numbers
    term.setCursorPos(w - #("\209\242\240. " .. y) + 1, h)
    term.setTextColour(highlightColour)
    term.write("\209\242\240. ")
    term.setTextColour(textColour)
    term.write(y)

    term.setCursorPos(1, h)
    if current_menu then
        -- Draw menu
        menu.draw(current_menu)
    else
        -- Draw status
        term.setTextColour(status_ok and highlightColour or errorColour)
        term.write(status_text)
        term.setTextColour(textColour)
    end

    -- Reset cursor
    term.setCursorPos(x - scrollX, y - scrollY)
    term.setCursorBlink(not current_menu)
end

local tMenuFuncs = {
    Save = function()
        if bReadOnly then
            set_status("\196\238\241\242\243\239 \231\224\239\240\229\249\184\237", false)
        else
            local ok, _, fileerr = save(sPath, function(file)
                for _, sLine in ipairs(tLines) do
                    file.write(sLine .. "\n")
                end
            end)
            if ok then
                set_status("\209\238\245\240\224\237\229\237\238 \226 " .. sPath)
            else
                if fileerr then
                    set_status("\206\248\232\225\234\224 \241\238\245\240\224\237\229\237\232\255: " .. fileerr, false)
                else
                    set_status("\205\229 \243\228\224\235\238\241\252 \241\238\245\240\224\237\232\242\252 \226 " .. sPath, false)
                end
            end
        end
        redrawMenu()
    end,
    Print = function()
        local printer = peripheral.find("printer")
        if not printer then
            set_status("\207\240\232\237\242\229\240 \237\229 \239\238\228\234\235\254\247\184\237", false)
            return
        end

        local nPage = 0
        local sName = fs.getName(sPath)
        if printer.getInkLevel() < 1 then
            set_status("\194 \239\240\232\237\242\229\240\229 \231\224\234\238\237\247\232\235\232\241\252 \247\229\240\237\232\235\224", false)
            return
        elseif printer.getPaperLevel() < 1 then
            set_status("\194 \239\240\232\237\242\229\240\229 \231\224\234\238\237\247\232\235\224\241\252 \225\243\236\224\227\224", false)
            return
        end

        local screenTerminal = term.current()
        local printerTerminal = {
            getCursorPos = printer.getCursorPos,
            setCursorPos = printer.setCursorPos,
            getSize = printer.getPageSize,
            write = printer.write,
        }
        printerTerminal.scroll = function()
            if nPage == 1 then
                printer.setPageTitle(sName .. " (\241\242\240\224\237\232\246\224 " .. nPage .. ")")
            end

            while not printer.newPage() do
                if printer.getInkLevel() < 1 then
                    set_status("\194 \239\240\232\237\242\229\240\229 \231\224\234\238\237\247\232\235\232\241\252 \247\229\240\237\232\235\224 - \231\224\239\240\224\226\252\242\229 \229\227\238", false)
                elseif printer.getPaperLevel() < 1 then
                    set_status("\194 \239\240\232\237\242\229\240\229 \231\224\234\238\237\247\232\235\224\241\252 \225\243\236\224\227\224 - \228\238\225\224\226\252\242\229 \229\184", false)
                else
                    set_status("\194\251\245\238\228\237\238\233 \235\238\242\238\234 \239\240\232\237\242\229\240\224 \231\224\239\238\235\237\229\237 - \238\241\226\238\225\238\228\232\242\229 \229\227\238", false)
                end

                term.redirect(screenTerminal)
                redrawMenu()
                term.redirect(printerTerminal)

                sleep(0.5)
            end

            nPage = nPage + 1
            if nPage == 1 then
                printer.setPageTitle(sName)
            else
                printer.setPageTitle(sName .. " (\241\242\240\224\237\232\246\224 " .. nPage .. ")")
            end
        end

        local old_menu = current_menu
        current_menu = nil
        term.redirect(printerTerminal)
        local ok, error = pcall(function()
            term.scroll()
            for _, sLine in ipairs(tLines) do
                print(sLine)
            end
        end)
        term.redirect(screenTerminal)
        if not ok then
            print(error)
        end

        while not printer.endPage() do
            set_status("\194\251\245\238\228\237\238\233 \235\238\242\238\234 \239\240\232\237\242\229\240\224 \231\224\239\238\235\237\229\237 - \238\241\226\238\225\238\228\232\242\229 \229\227\238")
            redrawMenu()
            sleep(0.5)
        end
        current_menu = old_menu

        if nPage > 1 then
            set_status("\205\224\239\229\247\224\242\224\237\238 \241\242\240\224\237\232\246: " .. nPage .. "")
        else
            set_status("\205\224\239\229\247\224\242\224\237\224 1 \241\242\240\224\237\232\246\224")
        end
        redrawMenu()
    end,
    Exit = function()
        bRunning = false
    end,
    Run = function()
        local sTitle = fs.getName(sPath)
        if sTitle:sub(-4) == ".lua" then
            sTitle = sTitle:sub(1, -5)
        end
        local sTempPath = bReadOnly and ".temp." .. sTitle or fs.combine(fs.getDir(sPath), ".temp." .. sTitle)
        if fs.exists(sTempPath) then
            set_status("\205\229 \243\228\224\235\238\241\252 \241\238\245\240\224\237\232\242\252 \226 " .. sTempPath, false)
            return
        end
        local ok = save(sTempPath, function(file)
            local runHandler = [[return require("cc.internal.edit_runner")(%q, %q, %q)]]
            file.write(runHandler:format(sTitle, "@/" .. sPath, table.concat(tLines, "\n")))
        end)
        if ok then
            local nTask = shell.openTab("/" .. sTempPath)
            if nTask then
                shell.switchTab(nTask)
            else
                set_status("\205\229 \243\228\224\235\238\241\252 \231\224\239\243\241\242\232\242\252 \231\224\228\224\247\243", false)
            end
            fs.delete(sTempPath)
        else
            set_status("\205\229 \243\228\224\235\238\241\252 \241\238\245\240\224\237\232\242\252 \226 " .. sTempPath, false)
        end
        redrawMenu()
    end,
}

local function setCursor(newX, newY)
    local _, oldY = x, y
    x, y = newX, newY
    local screenX = x - scrollX
    local screenY = y - scrollY

    local bRedraw = false
    if screenX < 1 then
        scrollX = x - 1
        screenX = 1
        bRedraw = true
    elseif screenX > w then
        scrollX = x - w
        screenX = w
        bRedraw = true
    end

    if screenY < 1 then
        scrollY = y - 1
        screenY = 1
        bRedraw = true
    elseif screenY > h - 1 then
        scrollY = y - (h - 1)
        screenY = h - 1
        bRedraw = true
    end

    recomplete()
    if bRedraw then
        redrawText()
    elseif y ~= oldY then
        redrawLines(math.min(y, oldY), math.max(y, oldY))
    else
        redrawLines(y)
    end

    redrawMenu()
end

-- Actual program functionality begins
load(sPath)

term.setBackgroundColour(bgColour)
term.clear()
term.setCursorPos(x, y)
term.setCursorBlink(true)

recomplete()
redrawText()
redrawMenu()

local function acceptCompletion()
    if nCompletion then
        -- Append the completion
        local sCompletion = tCompletions[nCompletion]
        tLines[y] = tLines[y] .. sCompletion
        setCursor(x + #sCompletion, y)
    end
end

local function handleMenuEvent(event)
    assert(current_menu)

    local result = menu.handle_event(current_menu, table.unpack(event, 1, event.n))
    if result == false then
        current_menu = nil
        redrawMenu()
    elseif result ~= nil then
        tMenuFuncs[result]()
        current_menu = nil
        redrawMenu()
    end
end

-- Handle input
while bRunning do
    local event = table.pack(os.pullEvent())
    if event[1] == "key" then
        if current_menu then
            handleMenuEvent(event)
        else
            local key = event[2]
            if key == keys.up then
                if nCompletion then
                    -- Cycle completions
                    nCompletion = nCompletion - 1
                    if nCompletion < 1 then
                        nCompletion = #tCompletions
                    end
                    redrawLines(y)

                elseif y > 1 then
                    -- Move cursor up
                    setCursor(
                        math.min(x, #tLines[y - 1] + 1),
                        y - 1
                    )
                end

            elseif key == keys.down then
                if nCompletion then
                    -- Cycle completions
                    nCompletion = nCompletion + 1
                    if nCompletion > #tCompletions then
                        nCompletion = 1
                    end
                    redrawLines(y)

                elseif y < #tLines then
                    -- Move cursor down
                    setCursor(
                        math.min(x, #tLines[y + 1] + 1),
                        y + 1
                    )
                end

            elseif key == keys.tab and not bReadOnly then
                if nCompletion and x == #tLines[y] + 1 then
                    -- Accept autocomplete
                    acceptCompletion()
                else
                    -- Indent line
                    local sLine = tLines[y]
                    tLines[y] = string.sub(sLine, 1, x - 1) .. "    " .. string.sub(sLine, x)
                    setCursor(x + 4, y)
                end

            elseif key == keys.pageUp then
                -- Move up a page
                local newY
                if y - (h - 1) >= 1 then
                    newY = y - (h - 1)
                else
                    newY = 1
                end
                setCursor(
                    math.min(x, #tLines[newY] + 1),
                    newY
                )
            elseif key == keys.pageDown then
                -- Move down a page
                local newY
                if y + (h - 1) <= #tLines then
                    newY = y + (h - 1)
                else
                    newY = #tLines
                end
                local newX = math.min(x, #tLines[newY] + 1)
                setCursor(newX, newY)

            elseif key == keys.home then
                -- Move cursor to the beginning
                if x > 1 then
                    setCursor(1, y)
                end

            elseif key == keys["end"] then
                -- Move cursor to the end
                local nLimit = #tLines[y] + 1
                if x < nLimit then
                    setCursor(nLimit, y)
                end

            elseif key == keys.left then
                if x > 1 then
                    -- Move cursor left
                    setCursor(x - 1, y)
                elseif x == 1 and y > 1 then
                    setCursor(#tLines[y - 1] + 1, y - 1)
                end

            elseif key == keys.right then
                local nLimit = #tLines[y] + 1
                if x < nLimit then
                    -- Move cursor right
                    setCursor(x + 1, y)
                elseif nCompletion and x == #tLines[y] + 1 then
                    -- Accept autocomplete
                    acceptCompletion()
                elseif x == nLimit and y < #tLines then
                    -- Go to next line
                    setCursor(1, y + 1)
                end

            elseif key == keys.delete and not bReadOnly then
                local nLimit = #tLines[y] + 1
                if x < nLimit then
                    local sLine = tLines[y]
                    tLines[y] = string.sub(sLine, 1, x - 1) .. string.sub(sLine, x + 1)
                    recomplete()
                    redrawLines(y)
                elseif y < #tLines then
                    tLines[y] = tLines[y] .. tLines[y + 1]
                    table.remove(tLines, y + 1)
                    table.remove(tLineLexStates, y + 1)
                    recomplete()
                    redrawText()
                end

            elseif key == keys.backspace and not bReadOnly then
                if x > 1 then
                    -- Remove character
                    local sLine = tLines[y]
                    if x > 4 and string.sub(sLine, x - 4, x - 1) == "    " and not string.sub(sLine, 1, x - 1):find("%S") then
                        tLines[y] = string.sub(sLine, 1, x - 5) .. string.sub(sLine, x)
                        setCursor(x - 4, y)
                    else
                        tLines[y] = string.sub(sLine, 1, x - 2) .. string.sub(sLine, x)
                        setCursor(x - 1, y)
                    end
                elseif y > 1 then
                    -- Remove newline
                    local sPrevLen = #tLines[y - 1]
                    tLines[y - 1] = tLines[y - 1] .. tLines[y]
                    table.remove(tLines, y)
                    table.remove(tLineLexStates, y)
                    setCursor(sPrevLen + 1, y - 1)
                    redrawText()
                end

            elseif (key == keys.enter or key == keys.numPadEnter) and not bReadOnly then
                -- Newline
                local sLine = tLines[y]
                local _, spaces = string.find(sLine, "^[ ]+")
                if not spaces then
                    spaces = 0
                end
                tLines[y] = string.sub(sLine, 1, x - 1)
                table.insert(tLines, y + 1, string.rep(' ', spaces) .. string.sub(sLine, x))
                table.insert(tLineLexStates, y + 1, false)
                setCursor(spaces + 1, y + 1)
                redrawText()

            elseif key == keys.leftCtrl or key == keys.rightCtrl then
                current_menu = menu.create(menu_items)
                redrawMenu()
            end
        end
    elseif event[1] == "char" then
        if current_menu then
            handleMenuEvent(event)
        elseif not bReadOnly then
            -- Input text
            local sLine = tLines[y]
            tLines[y] = string.sub(sLine, 1, x - 1) .. event[2] .. string.sub(sLine, x)
            setCursor(x + 1, y)
        end

    elseif event[1] == "paste" and not bReadOnly then
        -- Close menu if open
        if current_menu then
            current_menu = nil
            redrawMenu()
        end

        -- Input text
        local text = event[2]
        local sLine = tLines[y]
        tLines[y] = string.sub(sLine, 1, x - 1) .. text .. string.sub(sLine, x)
        setCursor(x + #text, y)

    elseif event[1] == "mouse_click" then
        local button, cx, cy = event[2], event[3], event[4]
        if current_menu then
            handleMenuEvent(event)
        else
            if button == 1 then
                -- Left click
                if cy < h then
                    local newY = math.min(math.max(scrollY + cy, 1), #tLines)
                    local newX = math.min(math.max(scrollX + cx, 1), #tLines[newY] + 1)
                    setCursor(newX, newY)
                else
                    current_menu = menu.create(menu_items)
                    redrawMenu()
                end
            end
        end

    elseif event[1] == "mouse_scroll" then
        if not current_menu then
            local direction = event[2]
            if direction == -1 then
                -- Scroll up
                if scrollY > 0 then
                    -- Move cursor up
                    scrollY = scrollY - 1
                    redrawText()
                end

            elseif direction == 1 then
                -- Scroll down
                local nMaxScroll = #tLines - (h - 1)
                if scrollY < nMaxScroll then
                    -- Move cursor down
                    scrollY = scrollY + 1
                    redrawText()
                end

            end
        end

    elseif event[1] == "term_resize" then
        w, h = term.getSize()
        setCursor(x, y)
        term.clear()
        redrawMenu()
        redrawText()

    end
end

-- Cleanup
term.clear()
term.setCursorBlink(false)
term.setCursorPos(1, 1)
