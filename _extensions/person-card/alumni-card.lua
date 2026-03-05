return {
  ['alumni-card'] = function(args, kwargs)
    local name = pandoc.utils.stringify(kwargs["name"] or "")
    local url = pandoc.utils.stringify(kwargs["url"] or "")
    local image = pandoc.utils.stringify(kwargs["image"] or "")
    local position = pandoc.utils.stringify(kwargs["position"] or "")
    local year = pandoc.utils.stringify(kwargs["year"] or "")

    local html = string.format([[
<div class="g-col-12 g-col-sm-6 g-col-lg-3">
<div style="display: flex; gap: 15px; align-items: start;">
<div style="flex-shrink: 1; width: 90px; min-width: 50px;">
<a href="%s" target='_blank'>
<img src="%s" alt="Headshot" style="width: 100%%; aspect-ratio: 1/1; object-fit: cover; object-position: center; border-radius: 10%%;">
</a>
</div>
<div style="flex: 1;line-height: 1.1;">
<a href="%s" target='_blank' style="color: inherit; text-decoration: underline; text-decoration-color: rgba(0,0,0,0.3);">
<span style="font-size: 1.1em; font-weight: 600;">%s</span>
</a>
<br><span style="font-size: 0.7em; font-weight: 300;">
%s
<br>
%s
</span>
</div>
</div>
</div>
]], url, image, url, name, year, position)
    return pandoc.RawBlock('html', html)
  end
}
