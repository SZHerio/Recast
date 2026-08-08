-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local args = table.pack(...)

if args.n < 1 then
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229: " .. programName .. " <paths>")
    return
end

for i = 1, args.n do
    local files = fs.find(shell.resolve(args[i]))
    if #files > 0 then
        for _, file in ipairs(files) do
            if fs.isReadOnly(file) then
                printError("\205\229\235\252\231\255 \243\228\224\235\232\242\252 \244\224\233\235 \242\238\235\252\234\238 \228\235\255 \247\242\229\237\232\255 /" .. file)
            elseif fs.isDriveRoot(file) then
                printError("\205\229\235\252\231\255 \243\228\224\235\232\242\252 \242\238\247\234\243 \236\238\237\242\232\240\238\226\224\237\232\255 /" .. file)
                if fs.isDir(file) then
                    print("\215\242\238\225\251 \243\228\224\235\232\242\252 \229\184 \241\238\228\229\240\230\232\236\238\229, \226\251\239\238\235\237\232\242\229 rm /" .. fs.combine(file, "*"))
                end
            else
                local ok, err = pcall(fs.delete, file)
                if not ok then
                    printError((err:gsub("^pcall: ", "")))
                end
            end
        end
    else
        printError(args[i] .. ": \239\238\228\245\238\228\255\249\232\229 \244\224\233\235\251 \237\229 \237\224\233\228\229\237\251")
    end
end
