import tomllib
from tinyhtml import html, h, frag, raw

ICON_CDN = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/{}.svg"

def icon_img(name, size=20):
    if not name:
        return frag()
    return h("img",
        src=ICON_CDN.format(name),
        alt=name,
        width=str(size), height=str(size),
        loading="lazy",
        klass="service-icon",
        onerror="this.style.display='none'",
    )

def render_item(item):
    has_both = item.get("url_ext") and item.get("url_int")
    url = item.get("url_ext") or item.get("url_int") or "#"

    if item.get("stream"):
        return h("button", klass="item stream-btn",
                 **{"data-stream": item["stream"], "data-title": item["title"]})(
            icon_img(item.get("icon")),
            h("span", klass="item-title")(item["title"]),
        )

    return h("div", klass="item-wrap")(
        h("a", klass="item", href=url, target="_blank")(
            icon_img(item.get("icon")),
            h("span", klass="item-title")(item["title"]),
        ),
        h("a",
            klass="int-badge",
            href=item.get("url_int", ""),
            target="_blank",
            title="Interner Zugriff",
        )("●") if has_both else frag(),
    )

def render_cluster(cluster):
    return h("div", klass="cluster")(
        h("div", klass="cluster-header")(
            icon_img(cluster.get("icon"), size=18),
            h("h3", klass="cluster-name")(cluster.get("name", "")),
        ),
        h("div", klass="cluster-items")(
            render_item(item) for item in cluster.get("items", [])
        ),
    )

with open("data.toml", "rb") as f:
    data = tomllib.load(f)

meta = data.get("meta", {})
gtag = meta.get("gtag_id", "")
primary_dark = meta.get("primary_color_dark", "#d81b60")
primary_light = meta.get("primary_color_light", "#85d457")
title = meta.get("title", "Dashboard")

gtag_block = raw(f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={gtag}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{gtag}');</script>
""") if gtag else frag()

page = html(lang="de")(
    h("head")(
        h("meta", charset="utf-8"),
        h("meta", name="viewport", content="width=device-width, initial-scale=1"),
        h("title")(title),
        h("link", rel="stylesheet", href="css/pico.min.css"),
        h("link", rel="stylesheet", href="css/style.css"),
        h("style")(raw(f"""
            :root {{ --primary: {primary_dark}; }}
            @media (prefers-color-scheme: light) {{ :root {{ --primary: {primary_light}; }} }}
        """)),
        gtag_block,
    ),
    h("body")(
        h("div", id="dim-overlay")(),
        h("main", klass="container")(
            h("div", klass="clusters-grid")(
                render_cluster(c) for c in data.get("clusters", [])
            ),
            h("audio", id="radio-player", preload="none")(),
        ),
        raw("""<script>
(() => {
  const player = document.getElementById("radio-player");
  const DEFAULT_TITLE = document.title;
  let active = null, vol = 0.65, idleTimer = null;

  const IDLE = 10000;
  const resetIdle = () => {
    clearTimeout(idleTimer);
    document.body.classList.remove("is-dimmed");
    if (!active) return;
    idleTimer = setTimeout(() => document.body.classList.add("is-dimmed"), IDLE);
  };
  ["mousemove","mousedown","keydown","scroll","touchstart"]
    .forEach(e => document.addEventListener(e, resetIdle, {passive:true}));

  const stop = () => {
    try { player.pause(); } catch(e) {}
    player.removeAttribute("src"); player.load();
    if (active) { active.classList.remove("radio-active"); active = null; }
    document.title = DEFAULT_TITLE;
    resetIdle();
  };

  document.addEventListener("click", async ev => {
    const btn = ev.target.closest(".stream-btn");
    if (!btn) return;
    stop();
    active = btn;
    btn.classList.add("radio-active");
    player.volume = vol;
    player.src = btn.dataset.stream;
    document.title = (btn.dataset.title || "Radio") + " — " + DEFAULT_TITLE;
    try { await player.play(); } catch(e) { stop(); }
    resetIdle();
  });

  window.jakeRadio = { stop, volUp: () => { vol = Math.min(1, vol+0.1); player.volume=vol; }, volDown: () => { vol = Math.max(0, vol-0.1); player.volume=vol; } };
})();
</script>"""),
    ),
)

import os
os.makedirs("dist", exist_ok=True)
with open("dist/index.html", "w") as f:
    f.write(page.render())

print("done")
