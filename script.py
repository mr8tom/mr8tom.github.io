import tomllib
from tinyhtml import html, h, frag, raw

ICON_CDN = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/{}.svg"

def icon_img(name, size=18):
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
            title="Intern öffnen",
        )("●") if has_both else frag(),
    )

def render_cluster(cluster):
    is_radio = cluster.get("radio", False)
    items_html = list(render_item(item) for item in cluster.get("items", []))

    stop_btn = h("button", klass="item stream-btn stop-btn", **{"data-stop": "true"})(
        h("span", klass="item-title")("⏹ Stop"),
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

meta = data.get("meta", {})
gtag = meta.get("gtag_id", "")
primary_dark = meta.get("primary_color_dark", "#d81b60")
primary_light = meta.get("primary_color_light", "#85d457")
title = meta.get("title", "Dashboard")

gtag_block = raw(f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={gtag}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{gtag}');</script>
""") if gtag else frag()

radio_js = r"""
<script>
(() => {
  const player = document.getElementById("radio-player");
  const nowPlaying = document.getElementById("now-playing");
  const DEFAULT_TITLE = document.title;
  let active = null, vol = 0.65, idleTimer = null;
  const IDLE_MS = 12000;

  // ── Idle/dim logic ────────────────────────────────────────────────────────
  const resetIdle = () => {
    clearTimeout(idleTimer);
    document.body.classList.remove("is-dimmed");
    if (!active) return;
    idleTimer = setTimeout(() => document.body.classList.add("is-dimmed"), IDLE_MS);
  };
  ["mousemove","mousedown","keydown","scroll","touchstart"]
    .forEach(e => document.addEventListener(e, resetIdle, {passive:true}));

  // ── Stop ──────────────────────────────────────────────────────────────────
  const stop = () => {
    try { player.pause(); } catch(e) {}
    player.removeAttribute("src"); player.load();
    if (active) { active.classList.remove("radio-active"); active = null; }
    document.title = DEFAULT_TITLE;
    if (nowPlaying) nowPlaying.textContent = "";
    clearTimeout(idleTimer);
    document.body.classList.remove("is-dimmed");
  };

  // ── Click delegation ──────────────────────────────────────────────────────
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
    document.title = name + " — " + DEFAULT_TITLE;
    if (nowPlaying) nowPlaying.textContent = "▶ " + name;
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
        raw(radio_js),
    ),
)

import os
os.makedirs("dist", exist_ok=True)
with open("dist/index.html", "w") as f:
    f.write(page.render())

print("done – dist/index.html written")
