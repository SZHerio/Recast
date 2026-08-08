-- SPDX-FileCopyrightText: 2020 The CC: Tweaked Developers
--
-- SPDX-License-Identifier: MPL-2.0

local date = os.date("*t")
if date.month == 1 and date.day == 1 then
    print("\209 \205\238\226\251\236 \227\238\228\238\236!")
elseif date.month == 12 and date.day == 24 then
    print("\209 \208\238\230\228\229\241\242\226\238\236!")
elseif date.month == 10 and date.day == 31 then
    print("\211-\243-\243-\243! \209\242\240\224\248\237\238!")
elseif date.month == 4 and date.day == 28 then
    print("Ed Balls")
else
    local tMotd = {}

    for sPath in string.gmatch(settings.get("motd.path"), "[^:]+") do
        if fs.exists(sPath) then
            for sLine in io.lines(sPath) do
                table.insert(tMotd, sLine)
            end
        end
    end

    if #tMotd == 0 then
        print("missingno")
    else
        print(tMotd[math.random(1, #tMotd)])
    end
end
