-- full-width-tables.lua
-- Pandoc Lua filter: 모든 테이블을 페이지 전체 너비로 설정
function Table(tbl)
  tbl.colspecs = tbl.colspecs:map(function(colspec)
    -- Set each column width proportionally (nil = auto/equal distribution)
    local align = colspec[1]
    return {align, nil}
  end)
  -- Set table width to 1.0 (100%)
  if PANDOC_VERSION >= {2,10} then
    tbl.attributes["width"] = "1.0"
  end
  return tbl
end
