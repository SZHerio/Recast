-- SPDX-FileCopyrightText: 2022 The CC: Tweaked Developers
--
-- SPDX-License-Identifier: MPL-2.0

require "cc.completion"

print("\207\229\240\229\242\224\249\232\242\229 \244\224\233\235\251, \247\242\238\225\251 \239\229\240\229\237\229\241\242\232 \232\245 \237\224 \253\242\238\242 \234\238\236\239\252\254\242\229\240")

local files
while true do
    local event, arg = os.pullEvent()
    if event == "file_transfer" then
        files = arg.getFiles()
        break
    elseif event == "key" and arg == keys.q then
        return
    end
end

if #files == 0 then
  printError("\205\229\242 \244\224\233\235\238\226 \228\235\255 \239\229\240\229\237\238\241\224")
  return
end

local ok, err = require("cc.internal.import")(files)
if not ok and err then printError(err) end
