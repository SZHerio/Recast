-- SPDX-FileCopyrightText: 2017 The CC: Tweaked Developers
--
-- SPDX-License-Identifier: MPL-2.0

if not pocket then
    printError("\210\240\229\225\243\229\242\241\255 \234\224\240\236\224\237\237\251\233 \234\238\236\239\252\254\242\229\240")
    return
end

local ok, err = pocket.unequipBack()
if not ok then
    printError(err)
else
    print("\207\240\229\228\236\229\242 \241\237\255\242")
end
