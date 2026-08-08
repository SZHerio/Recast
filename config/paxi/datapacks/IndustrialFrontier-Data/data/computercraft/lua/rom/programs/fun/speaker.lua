-- SPDX-FileCopyrightText: 2021 The CC: Tweaked Developers
--
-- SPDX-License-Identifier: MPL-2.0

local function get_speakers(name)
    if name then
        local speaker = peripheral.wrap(name)
        if speaker == nil then
            error(("\196\232\237\224\236\232\234 %q \237\229 \241\243\249\229\241\242\226\243\229\242"):format(name), 0)
            return
        elseif not peripheral.hasType(name, "speaker") then
            error(("%q \237\229 \255\226\235\255\229\242\241\255 \228\232\237\224\236\232\234\238\236"):format(name), 0)
        end

        return { speaker }
    else
        local speakers = { peripheral.find("speaker") }
        if #speakers == 0 then
            error("\196\232\237\224\236\232\234\232 \237\229 \239\238\228\234\235\254\247\229\237\251", 0)
        end
        return speakers
    end
end

local function pcm_decoder(chunk)
    local buffer = {}
    for i = 1, #chunk do
        buffer[i] = chunk:byte(i) - 128
    end
    return buffer
end

local function report_invalid_format(format)
    printError(("\207\240\238\227\240\224\236\236\224 speaker \237\229 \226\238\241\239\240\238\232\231\226\238\228\232\242 \244\224\233\235\251 %s."):format(format))
    local pp = require "cc.pretty"
    pp.print("\194\226\229\228\232\242\229 '" .. pp.text("help speaker", colours.lightGrey) .. "', \247\242\238\225\251 \243\231\237\224\242\252 \238 \239\238\228\228\229\240\230\232\226\224\229\236\251\245 \244\238\240\236\224\242\224\245.")
end


local cmd = ...
if cmd == "stop" then
    local _, name = ...
    for _, speaker in pairs(get_speakers(name)) do speaker.stop() end
elseif cmd == "play" then
    local _, file, name = ...
    if not file then
        error("\200\241\239\238\235\252\231\238\226\224\237\232\229: speaker play <file or url> [speaker]", 0)
    end

    local speaker = get_speakers(name)[1]

    local handle, err
    if http and file:match("^https?://") then
        print("\199\224\227\240\243\231\234\224...")
        handle, err = http.get(file)
    else
        handle, err = fs.open(shell.resolve(file), "r")
    end

    if not handle then
        printError("\205\229 \243\228\224\235\238\241\252 \226\238\241\239\240\238\232\231\226\229\241\242\232 \224\243\228\232\238:")
        error(err, 0)
    end

    local start = handle.read(4)
    local pcm = false
    local size = 16 * 1024 - 4
    if start == "RIFF" then
        handle.read(4)
        if handle.read(8) ~= "WAVEfmt " then
            handle.close()
            error("\205\229 \243\228\224\235\238\241\252 \226\238\241\239\240\238\232\231\226\229\241\242\232 \224\243\228\232\238: \237\229\239\238\228\228\229\240\230\232\226\224\229\236\251\233 \244\224\233\235 WAV", 0)
        end

        local fmtsize = ("<I4"):unpack(handle.read(4))
        local fmt = handle.read(fmtsize)
        local format, channels, rate, _, _, bits = ("<I2I2I4I4I2I2"):unpack(fmt)
        if not ((format == 1 and bits == 8) or (format == 0xFFFE and bits == 1)) then
            handle.close()
            error("\205\229 \243\228\224\235\238\241\252 \226\238\241\239\240\238\232\231\226\229\241\242\232 \224\243\228\232\238: \237\229\239\238\228\228\229\240\230\232\226\224\229\236\251\233 \244\224\233\235 WAV", 0)
        end
        if channels ~= 1 or rate ~= 48000 then
            print("\207\240\229\228\243\239\240\229\230\228\229\237\232\229: \239\238\228\228\229\240\230\232\226\224\254\242\241\255 \242\238\235\252\234\238 \236\238\237\238\244\238\237\232\247\229\241\234\232\229 \244\224\233\235\251 WAV \241 \247\224\241\242\238\242\238\233 48 \234\195\246. \221\242\238\242 \244\224\233\235 \236\238\230\229\242 \226\238\241\239\240\238\232\231\226\238\228\232\242\252\241\255 \237\229\239\240\224\226\232\235\252\237\238.")
        end
        if format == 0xFFFE then
            local guid = fmt:sub(25)
            if guid ~= "\x3A\xC1\xFA\x38\x81\x1D\x43\x61\xA4\x0D\xCE\x53\xCA\x60\x7C\xD1" then -- DFPWM format GUID
                handle.close()
                error("\205\229 \243\228\224\235\238\241\252 \226\238\241\239\240\238\232\231\226\229\241\242\232 \224\243\228\232\238: \237\229\239\238\228\228\229\240\230\232\226\224\229\236\251\233 \244\224\233\235 WAV", 0)
            end
            size = size + 4
        else
            pcm = true
            size = 16 * 1024 * 8
        end

        repeat
            local chunk = handle.read(4)
            if chunk == nil then
                handle.close()
                error("\205\229 \243\228\224\235\238\241\252 \226\238\241\239\240\238\232\231\226\229\241\242\232 \224\243\228\232\238: \239\238\226\240\229\230\228\184\237\237\251\233 \244\224\233\235 WAV", 0)
            elseif chunk ~= "data" then -- Ignore extra chunks
                local size = ("<I4"):unpack(handle.read(4))
                handle.read(size)
            end
        until chunk == "data"

        handle.read(4)
        start = nil
    -- Detect several other common audio files.
    elseif start == "OggS" then return report_invalid_format("Ogg")
    elseif start == "fLaC" then return report_invalid_format("FLAC")
    elseif start:sub(1, 3) == "ID3" then return report_invalid_format("MP3")
    elseif start == "<!DO" --[[<!DOCTYPE]] then return report_invalid_format("HTML")
    end

    print("\194\238\241\239\240\238\232\231\226\238\228\232\242\241\255 " .. file)

    local decoder = pcm and pcm_decoder or require "cc.audio.dfpwm".make_decoder()
    while true do
        local chunk = handle.read(size)
        if not chunk then break end
        if start then
            chunk, start = start .. chunk, nil
            size = size + 4
        end

        local buffer = decoder(chunk)
        while not speaker.playAudio(buffer) do
            os.pullEvent("speaker_audio_empty")
        end
    end

    handle.close()
elseif cmd == "sound" then
    local _, sound, volume, pitch, name = ...

    if not sound then
        error("\200\241\239\238\235\252\231\238\226\224\237\232\229: speaker sound <sound> [volume] [pitch] [speaker]", 0)
        return
    end

    if volume then
        volume = tonumber(volume)
        if not volume then
            error("\195\240\238\236\234\238\241\242\252 \228\238\235\230\237\224 \225\251\242\252 \247\232\241\235\238\236", 0)
        end
        if volume < 0 or volume > 3 then
            error("\195\240\238\236\234\238\241\242\252 \228\238\235\230\237\224 \225\251\242\252 \238\242 0 \228\238 3", 0)
        end
    end

    if pitch then
        pitch = tonumber(pitch)
        if not pitch then
            error("\194\251\241\238\242\224 \242\238\237\224 \228\238\235\230\237\224 \225\251\242\252 \247\232\241\235\238\236", 0)
        end
        if pitch < 0 or pitch > 2 then
            error("\194\251\241\238\242\224 \242\238\237\224 \228\238\235\230\237\224 \225\251\242\252 \238\242 0 \228\238 2", 0)
        end
    end

    local speaker = get_speakers(name)[1]

    if speaker.playSound(sound, volume, pitch) then
        print(("\199\226\243\234 %q \226\238\241\239\240\238\232\231\226\229\228\184\237 \247\229\240\229\231 \228\232\237\224\236\232\234 %q \241 \227\240\238\236\234\238\241\242\252\254 %s \232 \226\251\241\238\242\238\233 \242\238\237\224 %s."):format(
            sound, peripheral.getName(speaker), volume or 1, pitch or 1
        ))
    else
        error(("\205\229 \243\228\224\235\238\241\252 \226\238\241\239\240\238\232\231\226\229\241\242\232 \231\226\243\234 %q"):format(sound), 0)
    end
else
    local programName = arg[0] or fs.getName(shell.getRunningProgram())
    print("\200\241\239\238\235\252\231\238\226\224\237\232\229:")
    print(programName .. " play <file or url> [speaker]")
    print(programName .. " sound <sound> [volume] [pitch] [speaker]")
    print(programName .. " stop [speaker]")
end
