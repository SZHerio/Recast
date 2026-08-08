-- SPDX-FileCopyrightText: 2023 The CC: Tweaked Developers
--
-- SPDX-License-Identifier: MPL-2.0

--[[- The error messages reported by our lexer and parser.

> [!DANGER]
> This is an internal module and SHOULD NOT be used in your own code. It may
> be removed or changed at any time.

This provides a list of factory methods which take source positions and produce
appropriate error messages targeting that location. These error messages can
then be displayed to the user via [`cc.internal.error_printer`].

@local
]]

local pretty = require "cc.pretty"
local expect = require "cc.expect".expect
local tokens = require "cc.internal.syntax.parser".tokens

local function annotate(start_pos, end_pos, msg)
    if msg == nil and (type(end_pos) == "string" or type(end_pos) == "table" or type(end_pos) == "nil") then
        end_pos, msg = start_pos, end_pos
    end

    expect(1, start_pos, "number")
    expect(2, end_pos, "number")
    expect(3, msg, "string", "table", "nil")

    return { tag = "annotate", start_pos = start_pos, end_pos = end_pos, msg = msg or "" }
end

--- Format a string as a non-highlighted block of code.
--
-- @tparam string msg The code to format.
-- @treturn cc.pretty.Doc The formatted code.
local function code(msg) return pretty.text(msg, colours.lightGrey) end

--- Maps tokens to a more friendly version.
local token_names = setmetatable({
    -- Specific tokens.
    [tokens.IDENT] = "identifier",
    [tokens.NUMBER] = "number",
    [tokens.STRING] = "string",
    [tokens.EOF] = "end of file",
    -- Symbols and keywords
    [tokens.ADD] = code("+"),
    [tokens.AND] = code("and"),
    [tokens.BREAK] = code("break"),
    [tokens.CBRACE] = code("}"),
    [tokens.COLON] = code(":"),
    [tokens.COMMA] = code(","),
    [tokens.CONCAT] = code(".."),
    [tokens.CPAREN] = code(")"),
    [tokens.CSQUARE] = code("]"),
    [tokens.DIV] = code("/"),
    [tokens.DO] = code("do"),
    [tokens.DOT] = code("."),
    [tokens.DOTS] = code("..."),
    [tokens.DOUBLE_COLON] = code("::"),
    [tokens.ELSE] = code("else"),
    [tokens.ELSEIF] = code("elseif"),
    [tokens.END] = code("end"),
    [tokens.EQ] = code("=="),
    [tokens.EQUALS] = code("="),
    [tokens.FALSE] = code("false"),
    [tokens.FOR] = code("for"),
    [tokens.FUNCTION] = code("function"),
    [tokens.GE] = code(">="),
    [tokens.GOTO] = code("goto"),
    [tokens.GT] = code(">"),
    [tokens.IF] = code("if"),
    [tokens.IN] = code("in"),
    [tokens.LE] = code("<="),
    [tokens.LEN] = code("#"),
    [tokens.LOCAL] = code("local"),
    [tokens.LT] = code("<"),
    [tokens.MOD] = code("%"),
    [tokens.MUL] = code("*"),
    [tokens.NE] = code("~="),
    [tokens.NIL] = code("nil"),
    [tokens.NOT] = code("not"),
    [tokens.OBRACE] = code("{"),
    [tokens.OPAREN] = code("("),
    [tokens.OR] = code("or"),
    [tokens.OSQUARE] = code("["),
    [tokens.POW] = code("^"),
    [tokens.REPEAT] = code("repeat"),
    [tokens.RETURN] = code("return"),
    [tokens.SEMICOLON] = code(";"),
    [tokens.SUB] = code("-"),
    [tokens.THEN] = code("then"),
    [tokens.TRUE] = code("true"),
    [tokens.UNTIL] = code("until"),
    [tokens.WHILE] = code("while"),
}, { __index = function(_, name) error("No such token " .. tostring(name), 2) end })

local errors = {}

--------------------------------------------------------------------------------
-- Lexer errors
--------------------------------------------------------------------------------

--[[- A string which ends without a closing quote.

@tparam number start_pos The start position of the string.
@tparam number end_pos The end position of the string.
@tparam string quote The kind of quote (`"` or `'`).
@return The resulting parse error.
]]
function errors.unfinished_string(start_pos, end_pos, quote)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")
    expect(3, quote, "string")

    return {
        "\209\242\240\238\234\224 \237\229 \231\224\226\229\240\248\229\237\224. \194\238\231\236\238\230\237\238, \239\240\238\239\243\249\229\237\224 \231\224\234\240\251\226\224\254\249\224\255 \234\224\226\251\247\234\224 (" .. code(quote) .. ")?",
        annotate(start_pos, "\209\242\240\238\234\224 \237\224\247\232\237\224\229\242\241\255 \231\228\229\241\252."),
        annotate(end_pos, "\199\228\229\241\252 \238\230\232\228\224\235\224\241\252 \231\224\234\240\251\226\224\254\249\224\255 \234\224\226\251\247\234\224."),
    }
end

--[[- A string which ends with an escape sequence (so a literal `"foo\`). This
is slightly different from [`unfinished_string`], as we don't want to suggest
adding a quote.

@tparam number start_pos The start position of the string.
@tparam number end_pos The end position of the string.
@tparam string quote The kind of quote (`"` or `'`).
@return The resulting parse error.
]]
function errors.unfinished_string_escape(start_pos, end_pos, quote)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")
    expect(3, quote, "string")

    return {
        "\209\242\240\238\234\224 \237\229 \231\224\226\229\240\248\229\237\224.",
        annotate(start_pos, "\209\242\240\238\234\224 \237\224\247\232\237\224\229\242\241\255 \231\228\229\241\252."),
        annotate(end_pos, "\199\228\229\241\252 \237\224\247\232\237\224\229\242\241\255 \253\234\240\224\237\232\240\243\254\249\224\255 \239\238\241\235\229\228\238\226\224\242\229\235\252\237\238\241\242\252, \237\238 \239\238\241\235\229 \237\229\184 \237\232\247\229\227\238 \237\229\242."),
    }
end

--[[- A long string was never finished.

@tparam number start_pos The start position of the long string delimiter.
@tparam number end_pos The end position of the long string delimiter.
@tparam number ;em The length of the long string delimiter, excluding the first `[`.
@return The resulting parse error.
]]
function errors.unfinished_long_string(start_pos, end_pos, len)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")
    expect(3, len, "number")

    return {
        "\209\242\240\238\234\224 \242\224\234 \232 \237\229 \225\251\235\224 \231\224\226\229\240\248\229\237\224.",
        annotate(start_pos, end_pos, "\209\242\240\238\234\224 \237\224\247\224\235\224\241\252 \231\228\229\241\252."),
        "\196\224\235\229\229 \238\230\232\228\224\235\241\255 \231\224\234\240\251\226\224\254\249\232\233 \240\224\231\228\229\235\232\242\229\235\252 (" .. code("]" .. ("="):rep(len - 1) .. "]") .. ").",
    }
end

--[[- Malformed opening to a long string (i.e. `[=`).

@tparam number start_pos The start position of the long string delimiter.
@tparam number end_pos The end position of the long string delimiter.
@tparam number len The length of the long string delimiter, excluding the first `[`.
@return The resulting parse error.
]]
function errors.malformed_long_string(start_pos, end_pos, len)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")
    expect(3, len, "number")

    return {
        "\205\229\226\229\240\237\238\229 \237\224\247\224\235\238 \228\235\232\237\237\238\233 \241\242\240\238\234\232.",
        annotate(start_pos, end_pos),
        "\207\238\228\241\234\224\231\234\224: \247\242\238\225\251 \237\224\247\224\242\252 \231\228\229\241\252 \228\235\232\237\237\243\254 \241\242\240\238\234\243, \228\238\225\224\226\252\242\229 \229\249\184 \238\228\237\243 " .. code("[") .. ".",
    }
end

--[[- Malformed nesting of a long string.

@tparam number start_pos The start position of the long string delimiter.
@tparam number end_pos The end position of the long string delimiter.
@return The resulting parse error.
]]
function errors.nested_long_str(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        code("[[") .. " \237\229\235\252\231\255 \226\234\235\224\228\251\226\224\242\252 \226 \228\240\243\227\243\254 \234\238\237\241\242\240\243\234\246\232\254 " .. code("[[ ... ]]"),
        annotate(start_pos, end_pos),
    }
end

--[[- A malformed numeric literal.

@tparam number start_pos The start position of the number.
@tparam number end_pos The end position of the number.
@return The resulting parse error.
]]
function errors.malformed_number(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        "\221\242\238 \237\229\228\238\239\243\241\242\232\236\238\229 \247\232\241\235\238.",
        annotate(start_pos, end_pos),
        "\215\232\241\235\238 \237\243\230\237\238 \231\224\239\232\241\224\242\252 \226 \238\228\237\238\236 \232\231 \241\235\229\228\243\254\249\232\245 \244\238\240\236\224\242\238\226: " .. code("123") .. ", "
        .. code("3.14") .. ", " .. code("23e35") .. ", " .. code("0x01AF") .. ".",
    }
end

--[[- A long comment was never finished.

@tparam number start_pos The start position of the long string delimiter.
@tparam number end_pos The end position of the long string delimiter.
@tparam number len The length of the long string delimiter, excluding the first `[`.
@return The resulting parse error.
]]
function errors.unfinished_long_comment(start_pos, end_pos, len)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")
    expect(3, len, "number")

    return {
        "\202\238\236\236\229\237\242\224\240\232\233 \242\224\234 \232 \237\229 \225\251\235 \231\224\226\229\240\248\184\237.",
        annotate(start_pos, end_pos, "\202\238\236\236\229\237\242\224\240\232\233 \237\224\247\224\235\241\255 \231\228\229\241\252."),
        "\196\224\235\229\229 \238\230\232\228\224\235\241\255 \231\224\234\240\251\226\224\254\249\232\233 \240\224\231\228\229\235\232\242\229\235\252 (" .. code("]" .. ("="):rep(len - 1) .. "]") .. ").",
    }
end

--[[- `&&` was used instead of `and`.

@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.wrong_and(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        "\205\229\228\238\239\243\241\242\232\236\251\233 \241\232\236\226\238\235.",
        annotate(start_pos, end_pos),
        "\207\238\228\241\234\224\231\234\224: \231\224\236\229\237\232\242\229 \253\242\238\242 \241\232\236\226\238\235 \237\224 " .. code("and") .. " \228\235\255 \239\240\238\226\229\240\234\232 \232\241\242\232\237\237\238\241\242\232 \238\225\238\232\245 \231\237\224\247\229\237\232\233.",
    }
end

--[[- `||` was used instead of `or`.

@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.wrong_or(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        "\205\229\228\238\239\243\241\242\232\236\251\233 \241\232\236\226\238\235.",
        annotate(start_pos, end_pos),
        "\207\238\228\241\234\224\231\234\224: \231\224\236\229\237\232\242\229 \253\242\238\242 \241\232\236\226\238\235 \237\224 " .. code("or") .. " \228\235\255 \239\240\238\226\229\240\234\232 \232\241\242\232\237\237\238\241\242\232 \245\238\242\255 \225\251 \238\228\237\238\227\238 \231\237\224\247\229\237\232\255.",
    }
end

--[[- `!=` was used instead of `~=`.

@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.wrong_ne(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        "\205\229\228\238\239\243\241\242\232\236\251\233 \241\232\236\226\238\235.",
        annotate(start_pos, end_pos),
        "\207\238\228\241\234\224\231\234\224: \231\224\236\229\237\232\242\229 \253\242\238\242 \241\232\236\226\238\235 \237\224 " .. code("~=") .. " \228\235\255 \239\240\238\226\229\240\234\232 \237\229\240\224\226\229\237\241\242\226\224 \228\226\243\245 \231\237\224\247\229\237\232\233.",
    }
end

--[[- `!` was used instead of `not`.

@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.wrong_not(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        "\205\229\228\238\239\243\241\242\232\236\251\233 \241\232\236\226\238\235.",
        annotate(start_pos, end_pos),
        "\207\238\228\241\234\224\231\234\224: \231\224\236\229\237\232\242\229 \253\242\238\242 \241\232\236\226\238\235 \237\224 " .. code("not") .. " \228\235\255 \238\242\240\232\246\224\237\232\255 \235\238\227\232\247\229\241\234\238\227\238 \231\237\224\247\229\237\232\255.",
    }
end

--[[- An unexpected character was used.

@tparam number pos The position of this character.
@return The resulting parse error.
]]
function errors.unexpected_character(pos)
    expect(1, pos, "number")
    return {
        "\205\229\228\238\239\243\241\242\232\236\251\233 \241\232\236\226\238\235.",
        annotate(pos, "\221\242\238\242 \241\232\236\226\238\235 \237\229\235\252\231\255 \232\241\239\238\235\252\231\238\226\224\242\252 \226 \234\238\228\229 Lua."),
    }
end

--------------------------------------------------------------------------------
-- Expression parsing errors
--------------------------------------------------------------------------------

--[[- A fallback error when we expected an expression but received another token.

@tparam number token The token id.
@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.expected_expression(token, start_pos, end_pos)
    expect(1, token, "number")
    expect(2, start_pos, "number")
    expect(3, end_pos, "number")
    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ". \206\230\232\228\224\235\238\241\252 \226\251\240\224\230\229\237\232\229.",
        annotate(start_pos, end_pos),
    }
end

--[[- A fallback error when we expected a variable but received another token.

@tparam number token The token id.
@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.expected_var(token, start_pos, end_pos)
    expect(1, token, "number")
    expect(2, start_pos, "number")
    expect(3, end_pos, "number")
    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ". \206\230\232\228\224\235\238\241\252 \232\236\255 \239\229\240\229\236\229\237\237\238\233.",
        annotate(start_pos, end_pos),
    }
end

--[[- `=` was used in an expression context.

@tparam number start_pos The start position of the `=` token.
@tparam number end_pos The end position of the `=` token.
@return The resulting parse error.
]]
function errors.use_double_equals(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. code("=") .. " \226 \226\251\240\224\230\229\237\232\232.",
        annotate(start_pos, end_pos),
        "\207\238\228\241\234\224\231\234\224: \231\224\236\229\237\232\242\229 \253\242\238\242 \241\232\236\226\238\235 \237\224 " .. code("==") .. " \228\235\255 \239\240\238\226\229\240\234\232 \240\224\226\229\237\241\242\226\224 \228\226\243\245 \231\237\224\247\229\237\232\233.",
    }
end

--[[- `=` was used after an expression inside a table.

@tparam number start_pos The start position of the `=` token.
@tparam number end_pos The end position of the `=` token.
@return The resulting parse error.
]]
function errors.table_key_equals(start_pos, end_pos)
    expect(1, start_pos, "number")
    expect(2, end_pos, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. code("=") .. " \226 \226\251\240\224\230\229\237\232\232.",
        annotate(start_pos, end_pos),
        "\207\238\228\241\234\224\231\234\224: \231\224\234\235\254\247\232\242\229 \239\240\229\228\251\228\243\249\229\229 \226\251\240\224\230\229\237\232\229 \226 " .. code("[") .. " \232 " .. code("]") .. " - \242\238\227\228\224 \229\227\238 \236\238\230\237\238 \225\243\228\229\242 \232\241\239\238\235\252\231\238\226\224\242\252 \234\224\234 \234\235\254\247 \242\224\225\235\232\246\251.",
    }
end

--[[- There is a trailing comma in this list of function arguments.

@tparam number token The token id.
@tparam number token_start The start position of the token.
@tparam number token_end The end position of the token.
@tparam number prev The start position of the previous entry.
@treturn table The resulting parse error.
]]
function errors.missing_table_comma(token, token_start, token_end, prev)
    expect(1, token, "number")
    expect(2, token_start, "number")
    expect(3, token_end, "number")
    expect(4, prev, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. " \226 \242\224\225\235\232\246\229.",
        annotate(token_start, token_end),
        annotate(prev + 1, prev + 1, "\194\238\231\236\238\230\237\238, \231\228\229\241\252 \239\240\238\239\243\249\229\237\224 \231\224\239\255\242\224\255?"),
    }
end

--[[- There is a trailing comma in this list of function arguments.

@tparam number comma_start The start position of the `,` token.
@tparam number comma_end The end position of the `,` token.
@tparam number paren_start The start position of the `)` token.
@tparam number paren_end The end position of the `)` token.
@treturn table The resulting parse error.
]]
function errors.trailing_call_comma(comma_start, comma_end, paren_start, paren_end)
    expect(1, comma_start, "number")
    expect(2, comma_end, "number")
    expect(3, paren_start, "number")
    expect(4, paren_end, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. code(")") .. " \239\240\232 \226\251\231\238\226\229 \244\243\237\234\246\232\232.",
        annotate(paren_start, paren_end),
        annotate(comma_start, comma_end, "\207\238\228\241\234\224\231\234\224: \239\238\239\240\238\225\243\233\242\229 \243\225\240\224\242\252 " .. code(",") .. "."),
    }
end

--------------------------------------------------------------------------------
-- Statement parsing errors
--------------------------------------------------------------------------------

--[[- A fallback error when we expected a statement but received another token.

@tparam number token The token id.
@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.expected_statement(token, start_pos, end_pos)
    expect(1, token, "number")
    expect(2, start_pos, "number")
    expect(3, end_pos, "number")
    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ". \206\230\232\228\224\235\224\241\252 \232\237\241\242\240\243\234\246\232\255.",
        annotate(start_pos, end_pos),
    }
end

--[[- `local function` was used with a table identifier.

@tparam number local_start The start position of the `local` token.
@tparam number local_end The end position of the `local` token.
@tparam number dot_start The start position of the `.` token.
@tparam number dot_end The end position of the `.` token.
@return The resulting parse error.
]]
function errors.local_function_dot(local_start, local_end, dot_start, dot_end)
    expect(1, local_start, "number")
    expect(2, local_end, "number")
    expect(3, dot_start, "number")
    expect(4, dot_end, "number")

    return {
        "\205\229\235\252\231\255 \232\241\239\238\235\252\231\238\226\224\242\252 " .. code("local function") .. " \241 \234\235\254\247\238\236 \242\224\225\235\232\246\251.",
        annotate(dot_start, dot_end, code(".") .. " \237\224\245\238\228\232\242\241\255 \231\228\229\241\252."),
        annotate(local_start, local_end, "\207\238\228\241\234\224\231\234\224: " .. "\239\238\239\240\238\225\243\233\242\229 \243\225\240\224\242\252 " .. code("local") .. "."),
    }
end

--[[- A statement of the form `x.y`

@tparam number token The token id.
@tparam number pos The position right after this name.
@return The resulting parse error.
]]
function errors.standalone_name(token, pos)
    expect(1, token, "number")
    expect(2, pos, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. " \239\238\241\235\229 \232\236\229\237\232.",
        annotate(pos),
        "\194\251 \245\238\242\229\235\232 \239\240\232\241\226\238\232\242\252 \253\242\238\236\243 \231\237\224\247\229\237\232\229 \232\235\232 \226\251\231\226\224\242\252 \234\224\234 \244\243\237\234\246\232\254?",
    }
end

--[[- A statement of the form `x.y, z`

@tparam number token The token id.
@tparam number pos The position right after this name.
@return The resulting parse error.
]]
function errors.standalone_names(token, pos)
    expect(1, token, "number")
    expect(2, pos, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. " \239\238\241\235\229 \232\236\229\237\232.",
        annotate(pos),
        "\194\251 \245\238\242\229\235\232 \239\240\232\241\226\238\232\242\252 \253\242\238\236\243 \231\237\224\247\229\237\232\229?",
    }
end

--[[- A statement of the form `x.y`. This is similar to [`standalone_name`], but
when the next token is on another line.

@tparam number token The token id.
@tparam number pos The position right after this name.
@return The resulting parse error.
]]
function errors.standalone_name_call(token, pos)
    expect(1, token, "number")
    expect(2, pos, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. " \239\238\241\235\229 \232\236\229\237\232.",
        annotate(pos + 1, "\207\229\240\229\228 \234\238\237\246\238\236 \241\242\240\238\234\232 \238\230\232\228\224\235\238\241\252 \226\251\240\224\230\229\237\232\229."),
        "\207\238\228\241\234\224\231\234\224: \232\241\239\238\235\252\231\243\233\242\229 " .. code("()") .. " \228\235\255 \226\251\231\238\226\224 \225\229\231 \224\240\227\243\236\229\237\242\238\226.",
    }
end

--[[- `then` was expected

@tparam number if_start The start position of the `if`/`elseif` keyword.
@tparam number if_end The end position of the `if`/`elseif` keyword.
@tparam number token_pos The current token position.
@return The resulting parse error.
]]
function errors.expected_then(if_start, if_end, token_pos)
    expect(1, if_start, "number")
    expect(2, if_end, "number")
    expect(3, token_pos, "number")

    return {
        "\206\230\232\228\224\235\241\255 \242\238\234\229\237 " .. code("then") .. " \239\238\241\235\229 \243\241\235\238\226\232\255 if.",
        annotate(if_start, if_end, "\211\241\235\238\226\232\229 if \237\224\247\232\237\224\229\242\241\255 \231\228\229\241\252."),
        annotate(token_pos, "\206\230\232\228\224\235\241\255 \242\238\234\229\237 " .. code("then") .. " \239\229\240\229\228 \253\242\232\236 \236\229\241\242\238\236."),
    }

end

--[[- `end` was expected

@tparam number block_start The start position of the block.
@tparam number block_end The end position of the block.
@tparam number token The current token position.
@tparam number token_start The current token position.
@tparam number token_end The current token position.
@return The resulting parse error.
]]
function errors.expected_end(block_start, block_end, token, token_start, token_end)
    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ". \206\230\232\228\224\235\241\255 \242\238\234\229\237 " .. code("end") .. " \232\235\232 \228\240\243\227\224\255 \232\237\241\242\240\243\234\246\232\255.",
        annotate(block_start, block_end, "\193\235\238\234 \237\224\247\232\237\224\229\242\241\255 \231\228\229\241\252."),
        annotate(token_start, token_end, "\199\228\229\241\252 \238\230\232\228\224\235\241\255 \234\238\237\229\246 \225\235\238\234\224."),
    }
end

--[[- An unexpected `end` in a statement.

@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.unexpected_end(start_pos, end_pos)
    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. code("end") .. ".",
        annotate(start_pos, end_pos),
        "\194 \239\240\238\227\240\224\236\236\229 \225\238\235\252\248\229 " .. code("end") .. ", \247\229\236 \237\243\230\237\238. \207\240\238\226\229\240\252\242\229, \247\242\238 " ..
        "\234\224\230\228\251\233 \225\235\238\234 (" .. code("if") .. ", " .. code("for") .. ", " ..
        code("function") .. ", ...) \231\224\234\240\251\242 \240\238\226\237\238 \238\228\237\232\236 " .. code("end") .. ".",
    }
end

--[[- A label statement was opened but not closed.

@tparam number open_start The start position of the opening label.
@tparam number open_end The end position of the opening label.
@tparam number tok_start The start position of the current token.
@return The resulting parse error.
]]
function errors.unclosed_label(open_start, open_end, token, start_pos, end_pos)
    expect(1, open_start, "number")
    expect(2, open_end, "number")
    expect(3, token, "number")
    expect(4, start_pos, "number")
    expect(5, end_pos, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ".",
        annotate(open_start, open_end, "\204\229\242\234\224 \237\224\247\232\237\224\229\242\241\255 \231\228\229\241\252."),
        annotate(start_pos, end_pos, "\207\238\228\241\234\224\231\234\224: \239\238\239\240\238\225\243\233\242\229 \228\238\225\224\226\232\242\252 " .. code("::") .. " \231\228\229\241\252."),

    }
end

--------------------------------------------------------------------------------
-- Generic parsing errors
--------------------------------------------------------------------------------

--[[- A fallback error when we can't produce anything more useful.

@tparam number token The token id.
@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.unexpected_token(token, start_pos, end_pos)
    expect(1, token, "number")
    expect(2, start_pos, "number")
    expect(3, end_pos, "number")

    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ".",
        annotate(start_pos, end_pos),
    }
end

--[[- A parenthesised expression was started but not closed.

@tparam number open_start The start position of the opening bracket.
@tparam number open_end The end position of the opening bracket.
@tparam number tok_start The start position of the opening bracket.
@return The resulting parse error.
]]
function errors.unclosed_brackets(open_start, open_end, token, start_pos, end_pos)
    expect(1, open_start, "number")
    expect(2, open_end, "number")
    expect(3, token, "number")
    expect(4, start_pos, "number")
    expect(5, end_pos, "number")

    -- TODO: Do we want to be smarter here with where we report the error?
    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ". \194\238\231\236\238\230\237\238, \239\240\238\239\243\249\229\237\224 \231\224\234\240\251\226\224\254\249\224\255 \241\234\238\225\234\224?",
        annotate(open_start, open_end, "\209\234\238\225\234\232 \238\242\234\240\251\242\251 \231\228\229\241\252."),
        annotate(start_pos, end_pos, "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. " \231\228\229\241\252."),

    }
end

--[[- Expected `(` to open our function arguments.

@tparam number token The token id.
@tparam number start_pos The start position of the token.
@tparam number end_pos The end position of the token.
@return The resulting parse error.
]]
function errors.expected_function_args(token, start_pos, end_pos)
    return {
        "\205\229\238\230\232\228\224\237\237\251\233 \242\238\234\229\237 " .. token_names[token] .. ". \206\230\232\228\224\235\241\255 \242\238\234\229\237 " .. code("(") .. " \239\229\240\229\228 \224\240\227\243\236\229\237\242\224\236\232 \244\243\237\234\246\232\232.",
        annotate(start_pos, end_pos),
    }
end

return errors
