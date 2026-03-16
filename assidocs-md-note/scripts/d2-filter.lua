-- d2-filter.lua
-- Pandoc Lua filter: ```d2 코드블록을 자동으로 PNG 렌더링 후 이미지로 삽입
--
-- 사용법 (마크다운):
--   ```{.d2 caption="시스템 구성도" width=65% scale=0.7}
--   direction: down
--   a -> b -> c
--   ```
--
-- 또는 간단히:
--   ```d2
--   a -> b -> c
--   ```
--
-- 속성:
--   caption: 이미지 캡션 (기본: "Figure N")
--   width:   DOCX 내 이미지 너비 (기본: 65%)
--   scale:   D2 렌더링 스케일 (기본: 0.8, 작을수록 이미지 작아짐)
--   theme:   D2 테마 번호 (기본: 1)
--   pad:     D2 패딩 (기본: 10)
--   layout:  D2 레이아웃 엔진 (기본: elk)

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
  local width = block.attributes["width"] or "65%"
  local scale = block.attributes["scale"] or "0.8"
  local theme = block.attributes["theme"] or "1"
  local pad = block.attributes["pad"] or "10"
  local layout = block.attributes["layout"] or "elk"

  local basename = string.format("%s/d2_%03d", img_dir, counter)
  local d2_file = basename .. ".d2"
  local png_file = basename .. ".png"

  -- Write D2 source to temp file
  local f = io.open(d2_file, "w")
  f:write(block.text)
  f:close()

  -- Render with d2 (elk layout for tighter spacing, scale for size control)
  local cmd = string.format(
    "d2 --layout %s --theme %s --pad %s --scale %s %s %s 2>&1",
    layout, theme, pad, scale, d2_file, png_file
  )
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
