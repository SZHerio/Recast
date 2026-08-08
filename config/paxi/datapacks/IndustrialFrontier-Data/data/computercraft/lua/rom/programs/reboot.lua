-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if term.isColour() then
    term.setTextColour(colours.yellow)
end
print("\196\238 \241\226\232\228\224\237\232\255")
term.setTextColour(colours.white)

sleep(1)
os.reboot()
