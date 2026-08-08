-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not commands then
    printError("\210\240\229\225\243\229\242\241\255 \234\238\236\224\237\228\237\251\233 \234\238\236\239\252\254\242\229\240.")
    return
end

local tCommands = commands.list()
table.sort(tCommands)

if term.isColor() then
    term.setTextColor(colors.green)
end
print("\196\238\241\242\243\239\237\251\229 \234\238\236\224\237\228\251:")
term.setTextColor(colors.white)

textutils.pagedTabulate(tCommands)
