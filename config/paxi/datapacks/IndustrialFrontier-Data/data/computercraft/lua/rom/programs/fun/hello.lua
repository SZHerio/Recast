-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if term.isColour() then
    term.setTextColour(2 ^ math.random(0, 15))
end
textutils.slowPrint("\207\240\232\226\229\242, \236\232\240!")
term.setTextColour(colours.white)
