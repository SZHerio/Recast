-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local function printUsage()
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229:")
    print(programName .. " <url> [filename]")
    print(programName .. " run <url>")
end

local tArgs = { ... }

local run = false
if tArgs[1] == "run" then
    table.remove(tArgs, 1)
    run = true
end

if #tArgs < 1 then
    printUsage()
    return
end

local url = table.remove(tArgs, 1)

if not http then
    printError("\196\235\255 wget \242\240\229\225\243\229\242\241\255 API http, \237\238 \238\237 \238\242\234\235\254\247\184\237")
    printError("\211\241\242\224\237\238\226\232\242\229 http.enabled = true \226 \234\238\237\244\232\227\243\240\224\246\232\232 \241\229\240\226\229\240\224 CC: Tweaked")
    return
end

local function getFilename(sUrl)
    sUrl = sUrl:gsub("[#?].*" , ""):gsub("/+$" , "")
    return sUrl:match("/([^/]+)$")
end

local function get(url)
    -- Check if the URL is valid
    local ok, err = http.checkURL(url)
    if not ok then
        printError(err or "\205\229\228\238\239\243\241\242\232\236\251\233 URL-\224\228\240\229\241.")
        return
    end

    write("\207\238\228\234\235\254\247\229\237\232\229 \234 " .. url .. "... ")

    local response, err = http.get(url)
    if not response then
        printError(err)
        return
    end

    print("\195\238\242\238\226\238.")

    local sResponse = response.readAll()
    response.close()
    return sResponse or ""
end

if run then
    local res = get(url)
    if not res then return end

    local func, err = load(res, getFilename(url), "t", _ENV)
    if not func then
        printError(err)
        return
    end

    local ok, err = pcall(func, table.unpack(tArgs))
    if not ok then
        printError(err)
    end
else
    local sFile = tArgs[1] or getFilename(url) or url
    local sPath = shell.resolve(sFile)
    if fs.exists(sPath) then
        print("\212\224\233\235 \243\230\229 \241\243\249\229\241\242\226\243\229\242")
        return
    end

    local res = get(url)
    if not res then return end

    local file, err = fs.open(sPath, "wb")
    if not file then
        printError("\205\229 \243\228\224\235\238\241\252 \241\238\245\240\224\237\232\242\252 \244\224\233\235: " .. err)
        return
    end

    file.write(res)
    file.close()

    print("\209\238\245\240\224\237\229\237\238 \234\224\234 " .. sFile)
end
