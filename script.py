import tomllib
from tinyhtml import html, h, frag, raw

ICON_CDN = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons"

def icon_src(name: str) -> str:
    if name.startswith("http://") or name.startswith("https://"):
        return name

    lower = name.lower()

    if lower.endswith(".svg"):
        return f"{ICON_CDN}/svg/{name}"
    if lower.endswith(".png"):
        return f"{ICON_CDN}/png/{name}"
    if lower.endswith(".webp"):
        return f"{ICON_CDN}/webp/{name}"

    return f"{ICON_CDN}/svg/{name}.svg"

def icon_img(name, size=18):
    if not name:
        return frag()
    return h("img",
        src=icon_src(name),
        alt=name,
        width=str(size), height=str(size),
        loading="lazy",
        klass="service-icon",
        onerror="this.style.display='none'",
    )

def render_item(item):
    has_ext = bool(item.get("url_ext"))
    has_int = bool(item.get("url_int"))
    has_both = has_ext and has_int
    int_only  = has_int and not has_ext

    if item.get("stream"):
        return h("button", klass="item stream-btn",
                 **{"data-stream": item["stream"], "data-title": item["title"]})(
            h("span", klass="item-title")(item["title"]),
        )

    # Klasse: ext (hat url_ext), int-only (nur url_int)
    if int_only:
        css_class = "item int-only"
        url = item["url_int"]
    else:
        css_class = "item ext"
        url = item.get("url_ext") or item.get("url_int") or "#"

    link = h("a", klass=css_class, href=url)(
        icon_img(item.get("icon")),
        h("span", klass="item-title")(item["title"]),
    )

    # Badge: grüner Punkt für Dual-URL – öffnet die interne URL
    badge = h("a",
        klass="int-badge",
        href=item.get("url_int", ""),
        title="Intern öffnen",
    )("●") if has_both else frag()

    return h("div", klass="item-wrap")(link, badge)

def render_cluster(cluster):
    is_radio = cluster.get("radio", False)
    items_html = list(render_item(item) for item in cluster.get("items", []))

    stop_btn = h("button", klass="item stream-btn stop-btn", **{"data-stop": "true"})(
        h("span")("⏹ Stop"),
    ) if is_radio else frag()

    now_playing = h("span", klass="now-playing", id="now-playing")() if is_radio else frag()

    return h("div", klass="cluster")(
        h("div", klass="cluster-header")(
            h("h3", klass="cluster-name")(cluster.get("name", "")),
        ),
        h("div", klass="cluster-items")(
            *items_html,
            stop_btn,
            now_playing,
        ),
    )

with open("data.toml", "rb") as f:
    data = tomllib.load(f)

meta    = data.get("meta", {})
gtag    = meta.get("gtag_id", "")
title   = meta.get("title", "Dashboard")

gtag_block = raw(f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={gtag}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{gtag}');</script>
""") if gtag else frag()

# Favicons aus dist/img/
favicons = raw("""
  <link rel="icon" type="image/x-icon"    href="img/favicon.ico">
  <link rel="icon" type="image/svg+xml"   href="img/logo.svg">
  <link rel="apple-touch-icon"            href="img/apple-touch-icon.png">
  <link rel="manifest" href="img/manifest.json">
""")

radio_js = r"""
<script>
(() => {
  const player    = document.getElementById("radio-player");
  const nowPlay   = document.getElementById("now-playing");
  const DEF_TITLE = document.title;
  let active = null, vol = 0.65, idleTimer = null;
  const IDLE_MS = 12000;

  const resetIdle = () => {
    clearTimeout(idleTimer);
    document.body.classList.remove("is-dimmed");
    if (!active) return;
    idleTimer = setTimeout(() => document.body.classList.add("is-dimmed"), IDLE_MS);
  };
  ["mousemove","mousedown","keydown","scroll","touchstart"]
    .forEach(e => document.addEventListener(e, resetIdle, {passive:true}));

  const stop = () => {
    try { player.pause(); } catch(e) {}
    player.removeAttribute("src"); player.load();
    if (active) { active.classList.remove("radio-active"); active = null; }
    document.title = DEF_TITLE;
    if (nowPlay) nowPlay.textContent = "";
    clearTimeout(idleTimer);
    document.body.classList.remove("is-dimmed");
  };

  document.addEventListener("click", async ev => {
    const btn = ev.target.closest(".stream-btn");
    if (!btn) return;
    if (btn.dataset.stop === "true") { stop(); return; }
    stop();
    active = btn;
    btn.classList.add("radio-active");
    player.volume = vol;
    player.src = btn.dataset.stream;
    const name = btn.dataset.title || "Radio";
    document.title = name + " — " + DEF_TITLE;
    if (nowPlay) nowPlay.textContent = "▶ " + name;
    try { await player.play(); } catch(e) { stop(); }
    resetIdle();
  });
})();
</script>
"""

page = html(lang="de")(
    h("head")(
        h("meta", charset="utf-8"),
        h("meta", name="viewport", content="width=device-width, initial-scale=1"),
        h("title")(title),
        favicons,
        h("link", rel="stylesheet", href="css/style.css"),
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
        raw(radio_js),
    ),
)

import os
os.makedirs("dist", exist_ok=True)
with open("dist/index.html", "w") as f:
    f.write(page.render())

print("done")
