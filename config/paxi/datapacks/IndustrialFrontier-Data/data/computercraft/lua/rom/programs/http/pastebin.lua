-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local function printUsage()
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\194\224\240\232\224\237\242\251 \232\241\239\238\235\252\231\238\226\224\237\232\255:")
    print(programName .. " put <filename>")
    print(programName .. " get <code> <filename>")
    print(programName .. " run <code> <arguments>")
end

local tArgs = { ... }
if #tArgs < 2 then
    printUsage()
    return
end

if not http then
    printError("\196\235\255 Pastebin \242\240\229\225\243\229\242\241\255 API http, \237\238 \238\237 \238\242\234\235\254\247\184\237")
    printError("\211\241\242\224\237\238\226\232\242\229 http.enabled = true \226 \234\238\237\244\232\227\243\240\224\246\232\232 \241\229\240\226\229\240\224 CC: Tweaked")
    return
end

--- Attempts to guess the pastebin ID from the given code or URL
local function extractId(paste)
    local patterns = {
        "^([%a%d]+)$",
        "^https?://pastebin.com/([%a%d]+)$",
        "^pastebin.com/([%a%d]+)$",
        "^https?://pastebin.com/raw/([%a%d]+)$",
        "^pastebin.com/raw/([%a%d]+)$",
    }

    for i = 1, #patterns do
        local code = paste:match(patterns[i])
        if code then return code end
    end

    return nil
end

local function get(url)
    local paste = extractId(url)
    if not paste then
        io.stderr:write("\205\229\228\238\239\243\241\242\232\236\251\233 \234\238\228 Pastebin.\n")
        io.write("\202\238\228 - \253\242\238 ID \226 \234\238\237\246\229 URL-\224\228\240\229\241\224 pastebin.com.\n")
        return
    end

    write("\207\238\228\234\235\254\247\229\237\232\229 \234 pastebin.com... ")
    -- Add a cache buster so that spam protection is re-checked
    local cacheBuster = ("%x"):format(math.random(0, 2 ^ 30))
    local response, err = http.get(
        "https://pastebin.com/raw/" .. textutils.urlEncode(paste) .. "?cb=" .. cacheBuster
    )

    if response then
        -- If spam protection is activated, we get redirected to /paste with Content-Type: text/html
        local headers = response.getResponseHeaders()
        if not headers["Content-Type"] or not headers["Content-Type"]:find("^text/plain") then
            io.stderr:write("\206\248\232\225\234\224.\n")
            print("Pastebin \231\224\225\235\238\234\232\240\238\226\224\235 \231\224\227\240\243\231\234\243 \232\231-\231\224 \231\224\249\232\242\251 \238\242 \241\239\224\236\224. \207\240\238\233\228\232\242\229 \239\240\238\226\229\240\234\243 CAPTCHA \226 \225\240\224\243\231\229\240\229: https://pastebin.com/" .. textutils.urlEncode(paste))
            return
        end

        print("\195\238\242\238\226\238.")

        local sResponse = response.readAll()
        response.close()
        return sResponse
    else
        io.stderr:write("\206\248\232\225\234\224.\n")
        print(err)
    end
end

local sCommand = tArgs[1]
if sCommand == "put" then
    -- Upload a file to pastebin.com
    -- Determine file to upload
    local sFile = tArgs[2]
    local sPath = shell.resolve(sFile)
    if not fs.exists(sPath) or fs.isDir(sPath) then
        print("\212\224\233\235 \237\229 \237\224\233\228\229\237")
        return
    end

    -- Read in the file
    local sName = fs.getName(sPath)
    local file = fs.open(sPath, "r")
    local sText = file.readAll()
    file.close()

    -- POST the contents to pastebin
    write("\207\238\228\234\235\254\247\229\237\232\229 \234 pastebin.com... ")
    local key = "0ec2eb25b6166c0c27a394ae118ad829"
    local response = http.post(
        "https://pastebin.com/api/api_post.php",
        "api_option=paste&" ..
        "api_dev_key=" .. key .. "&" ..
        "api_paste_format=lua&" ..
        "api_paste_name=" .. textutils.urlEncode(sName) .. "&" ..
        "api_paste_code=" .. textutils.urlEncode(sText)
    )

    if response then
        print("\195\238\242\238\226\238.")

        local sResponse = response.readAll()
        response.close()

        local sCode = string.match(sResponse, "[^/]+$")
        print("\199\224\227\240\243\230\229\237\238: " .. sResponse)
        print("\194\226\229\228\232\242\229 \"pastebin get " .. sCode .. "\", \247\242\238\225\251 \241\234\224\247\224\242\252 \244\224\233\235 \237\224 \235\254\225\238\236 \234\238\236\239\252\254\242\229\240\229")

    else
        print("\206\248\232\225\234\224.")
    end

elseif sCommand == "get" then
    -- Download a file from pastebin.com
    if #tArgs < 3 then
        printUsage()
        return
    end

    -- Determine file to download
    local sCode = tArgs[2]
    local sFile = tArgs[3]
    local sPath = shell.resolve(sFile)
    if fs.exists(sPath) then
        print("\212\224\233\235 \243\230\229 \241\243\249\229\241\242\226\243\229\242")
        return
    end

    -- GET the contents from pastebin
    local res = get(sCode)
    if res then
        local file = fs.open(sPath, "w")
        file.write(res)
        file.close()

        print("\209\238\245\240\224\237\229\237\238 \234\224\234 " .. sFile)
    end
elseif sCommand == "run" then
    local sCode = tArgs[2]

    local res = get(sCode)
    if res then
        local func, err = load(res, sCode, "t", _ENV)
        if not func then
            printError(err)
            return
        end
        local success, msg = pcall(func, select(3, ...))
        if not success then
            printError(msg)
        end
    end
else
    printUsage()
    return
end
