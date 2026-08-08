-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tArgs = { ... }
if #tArgs < 2 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <source> <destination>")
    return
end

local sSource = shell.resolve(tArgs[1])
local sDest = shell.resolve(tArgs[2])
local tFiles = fs.find(sSource)

local function sanity_checks(source, dest)
    if fs.exists(dest) then
        printError("\207\243\242\252 \237\224\231\237\224\247\229\237\232\255 \243\230\229 \241\243\249\229\241\242\226\243\229\242")
        return false
    elseif fs.isReadOnly(dest) then
        printError("\207\243\242\252 \237\224\231\237\224\247\229\237\232\255 \228\238\241\242\243\239\229\237 \242\238\235\252\234\238 \228\235\255 \247\242\229\237\232\255")
        return false
    elseif fs.isDriveRoot(source) then
        printError("\205\229\235\252\231\255 \239\229\240\229\236\229\241\242\232\242\252 \242\238\247\234\243 \236\238\237\242\232\240\238\226\224\237\232\255 /" .. source)
        return false
    elseif fs.isReadOnly(source) then
        printError("\205\229\235\252\231\255 \239\229\240\229\236\229\241\242\232\242\252 \244\224\233\235 \242\238\235\252\234\238 \228\235\255 \247\242\229\237\232\255 /" .. source)
        return false
    end
    return true
end

if #tFiles > 0 then
    for _, sFile in ipairs(tFiles) do
        if fs.isDir(sDest) then
            local dest = fs.combine(sDest, fs.getName(sFile))
            if sanity_checks(sFile, dest) then
                fs.move(sFile, dest)
            end
        elseif #tFiles == 1 then
            if sanity_checks(sFile, sDest) then
                fs.move(sFile, sDest)
            end
        else
            printError("\205\229\241\234\238\235\252\234\238 \244\224\233\235\238\226 \237\229\235\252\231\255 \239\229\240\229\236\229\241\242\232\242\252 \226 \238\228\232\237 \244\224\233\235")
            return
        end
    end
else
    printError("\207\238\228\245\238\228\255\249\232\229 \244\224\233\235\251 \237\229 \237\224\233\228\229\237\251")
end
