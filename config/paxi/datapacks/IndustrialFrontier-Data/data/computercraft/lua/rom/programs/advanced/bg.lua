-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not shell.openTab then
    printError("\210\240\229\225\243\229\242\241\255 multishell")
    return
end

local tArgs = { ... }
if #tArgs > 0 then
    shell.openTab(table.unpack(tArgs))
else
    shell.openTab("shell")
end
