-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

local tPeripherals = peripheral.getNames()
print("\207\238\228\234\235\254\247\184\237\237\224\255 \239\229\240\232\244\229\240\232\255:")
if #tPeripherals > 0 then
    for n = 1, #tPeripherals do
        local sPeripheral = tPeripherals[n]
        print(sPeripheral .. " (" .. table.concat({ peripheral.getType(sPeripheral) }, ", ") .. ")")
    end
else
    print("\205\229\242")
end
