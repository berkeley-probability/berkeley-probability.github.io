return {
  ['student-card'] = function(args, kwargs)
    local name = pandoc.utils.stringify(kwargs["name"] or "")
    local url = pandoc.utils.stringify(kwargs["url"] or "")
    local image = pandoc.utils.stringify(kwargs["image"] or "")
    local affil = pandoc.utils.stringify(kwargs["affil"] or "")
    local advisors = pandoc.utils.stringify(kwargs["advisors"] or "")
    local html = string.format([[
<div class="g-col-12 g-col-sm-6 g-col-lg-3">
<div style="display: flex; gap: 15px; align-items: start;">
<div style="flex-shrink: 1; width: 90px; min-width: 50px;">
<a href="%s" target='_blank'>
<img src="%s" alt="Headshot" style="width: 100%%; aspect-ratio: 1/1; object-fit: cover; object-position: center; border-radius: 10%%;">
</a>
</div>
<div style="flex: 1;line-height: 1.1;">
<a href="%s" target='_blank' style="color: inherit; text-decoration: none;">
<span style="font-size: 1.1em; font-weight: 600; display: inline-block; height: 2.1em; line-height: 0.88em; vertical-align: top;">%s</span>
</a>
<br><span style="font-size: 0.7em; font-weight: 300;">
%s
<br>
%s
</span>
</div>
</div>
</div>
]], url, image, url, name, affil, advisors)
    return pandoc.RawBlock('html', html)
  end
}
