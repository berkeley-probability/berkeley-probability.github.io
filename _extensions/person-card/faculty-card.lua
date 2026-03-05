return {
  ['faculty-card'] = function(args, kwargs)
    local name = pandoc.utils.stringify(kwargs["name"] or "")
    local url = pandoc.utils.stringify(kwargs["url"] or "")
    local image = pandoc.utils.stringify(kwargs["image"] or "")
    local affil = pandoc.utils.stringify(kwargs["affil"] or "")
    local research = pandoc.utils.stringify(kwargs["research"] or "")
    local html = string.format([[
<div class="g-col-12 g-col-sm-6" style="margin-bottom: 8px;">
<div style="display: flex; gap: 16px; align-items: center;">
<div style="flex-shrink: 0; width: 110px;">
<img src="%s" alt="Headshot" style="width: 100%%; aspect-ratio: 1/1; object-fit: cover; object-position: center; border-radius: 8%%;">
</div>
<div style="flex: 1; line-height: 1.3;">
<a href="%s" target='_blank' class="faculty-name-link">
<span style="font-size: 1.1em; font-weight: 600;">%s</span>
</a>
<br><span style="font-size: 1em; font-weight: 400;">%s</span>
<br><span style="font-size: 0.8em; font-weight: 300; color: #444;">%s</span>
</div>
</div>
</div>
]], image, url, name, affil, research)
    return pandoc.RawBlock('html', html)
  end
}
