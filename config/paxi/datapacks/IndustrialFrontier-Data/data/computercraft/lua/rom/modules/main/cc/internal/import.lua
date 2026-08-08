-- SPDX-FileCopyrightText: 2023 The CC: Tweaked Developers
--
-- SPDX-License-Identifier: MPL-2.0

--[[- Upload a list of files, as received by the [`event!file_transfer`] event.

> [!DANGER]
> This is an internal module and SHOULD NOT be used in your own code. It may
> be removed or changed at any time.

@local
]]

local completion = require "cc.completion"

--- @tparam { file_transfer.TransferredFile ...} files The files to upload.
return function(files)
    local overwrite = {}
    for _, file in pairs(files) do
        local filename = file.getName()
        local path = shell.resolve(filename)
        if fs.exists(path) then
            if fs.isDir(path) then
                return nil, filename .. " \243\230\229 \255\226\235\255\229\242\241\255 \234\224\242\224\235\238\227\238\236."
            end

            overwrite[#overwrite + 1] = filename
        end
    end

    if #overwrite > 0 then
        table.sort(overwrite)
        printError("\209\235\229\228\243\254\249\232\229 \244\224\233\235\251 \225\243\228\243\242 \239\229\240\229\231\224\239\232\241\224\237\251:")
        textutils.pagedTabulate(colours.cyan, overwrite)

        while true do
            io.write("\207\229\240\229\231\224\239\232\241\224\242\252? (yes/no) ")
            local input = read(nil, nil, function(t)
                return completion.choice(t, { "yes", "no" })
            end)
            if not input then return end

            input = input:lower()
            if input == "" or input == "yes" or input == "y" then
                break
            elseif input == "no" or input == "n" then
                return
            end
        end
    end

    for _, file in pairs(files) do
        local filename = file.getName()
        print("\207\229\240\229\237\238\241 \244\224\233\235\224 " .. filename)

        local path = shell.resolve(filename)
        local handle, err = fs.open(path, "wb")
        if not handle then return nil, err end

        -- Write the file without loading it all into memory. This uses the same buffer size
        -- as BinaryReadHandle. It would be really nice to have a way to do this without
        -- multiple copies.
        while true do
            local chunk = file.read(8192)
            if not chunk then break end

            local ok, err = pcall(handle.write, chunk)
            if not ok then
                handle.close()

                -- Probably an out-of-space issue, just bail.
                if err:sub(1, 7) == "pcall: " then err = err:sub(8) end
                return nil, "\205\229 \243\228\224\235\238\241\252 \231\224\239\232\241\224\242\252 \244\224\233\235 (" .. err .. "). \212\224\233\235 \236\238\230\229\242 \225\251\242\252 \239\238\226\240\229\230\228\184\237"
            end
        end

        handle.close()
    end

    return true
end
