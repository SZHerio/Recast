-- SPDX-FileCopyrightText: 2017 Daniel Ratcliffe
--
-- SPDX-License-Identifier: LicenseRef-CCPL

if not turtle then
    printError("\210\240\229\225\243\229\242\241\255 \247\229\240\229\239\224\245\224")
end

local tMoves = {
    function()
        turtle.up()
        turtle.down()
    end,
    function()
        turtle.up()
        turtle.turnLeft()
        turtle.turnLeft()
        turtle.turnLeft()
        turtle.turnLeft()
        turtle.down()
    end,
    function()
        turtle.up()
        turtle.turnRight()
        turtle.turnRight()
        turtle.turnRight()
        turtle.turnRight()
        turtle.down()
    end,
    function()
        turtle.turnLeft()
        turtle.turnLeft()
        turtle.turnLeft()
        turtle.turnLeft()
    end,
    function()
        turtle.turnRight()
        turtle.turnRight()
        turtle.turnRight()
        turtle.turnRight()
    end,
    function()
        turtle.turnLeft()
        turtle.back()
        turtle.back()
        turtle.turnRight()
        turtle.turnRight()
        turtle.back()
        turtle.back()
        turtle.turnLeft()
    end,
    function()
        turtle.turnRight()
        turtle.back()
        turtle.back()
        turtle.turnLeft()
        turtle.turnLeft()
        turtle.back()
        turtle.back()
        turtle.turnRight()
    end,
    function()
        turtle.back()
        turtle.turnLeft()
        turtle.back()
        turtle.turnLeft()
        turtle.back()
        turtle.turnLeft()
        turtle.back()
        turtle.turnLeft()
    end,
    function()
        turtle.back()
        turtle.turnRight()
        turtle.back()
        turtle.turnRight()
        turtle.back()
        turtle.turnRight()
        turtle.back()
        turtle.turnRight()
    end,
}

textutils.slowWrite("\195\238\242\238\226\235\254\241\252 \231\224\230\232\227\224\242\252.")
textutils.slowPrint("..", 0.75)

local sAudio = nil
for _, sName in pairs(peripheral.getNames()) do
    if disk.hasAudio(sName) then
        disk.playAudio(sName)
        print("\210\224\237\246\243\254 \239\238\228 " .. disk.getAudioTitle(sName))
        sAudio = sName
        break
    end
end

print("\205\224\230\236\232\242\229 \235\254\225\243\254 \234\235\224\226\232\248\243, \247\242\238\225\251 \238\241\242\224\237\238\226\232\242\252 \242\224\237\229\246")

parallel.waitForAny(
    function() os.pullEvent("key") end,
    function()
        while true do
            tMoves[math.random(1, #tMoves)]()
        end
    end
)

if sAudio then
    disk.stopAudio(sAudio)
end
