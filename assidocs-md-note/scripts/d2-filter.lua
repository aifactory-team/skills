-- d2-filter.lua
-- Pandoc Lua filter: ```d2 코드블록을 자동으로 PNG 렌더링 후 이미지로 삽입
--
-- 사용법 (마크다운):
--   ```{.d2 caption="시스템 구성도" width=80%}
--   direction: down
--   a -> b -> c
--   ```
--
-- 또는 간단히:
--   ```d2
--   a -> b -> c
--   ```

local counter = 0
local img_dir = "d2_rendered"

-- Ensure output directory exists
os.execute("mkdir -p " .. img_dir)

function CodeBlock(block)
  if not block.classes:includes("d2") then
    return nil
  end

  counter = counter + 1
  local caption = block.attributes["caption"] or ("Figure " .. counter)
  local width = block.attributes["width"] or "80%"
  local theme = block.attributes["theme"] or "4"
  local pad = block.attributes["pad"] or "40"

  local basename = string.format("%s/d2_%03d", img_dir, counter)
  local d2_file = basename .. ".d2"
  local png_file = basename .. ".png"

  -- Write D2 source to temp file
  local f = io.open(d2_file, "w")
  f:write(block.text)
  f:close()

  -- Render with d2
  local cmd = string.format("d2 --theme %s --pad %s %s %s 2>&1", theme, pad, d2_file, png_file)
  local handle = io.popen(cmd)
  local result = handle:read("*a")
  local success = handle:close()

  if not success then
    io.stderr:write("d2 render failed: " .. result .. "\n")
    return nil
  end

  -- Create image element with caption
  local img = pandoc.Image(pandoc.Str(caption), png_file)
  img.attributes["width"] = width

  -- Return as a figure paragraph
  return pandoc.Para({img})
end
