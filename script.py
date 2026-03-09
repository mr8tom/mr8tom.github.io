import tomllib

from tinyhtml import html, h, frag, raw


def render_item(item, outline: bool):
    klass = "outline" if outline else ""

    if item.get("stream"):
        return h(
            "button",
            role="button",
            klass=klass,
            **{
                "data-stream": item.get("stream"),
                "data-title": item.get("title") or "",
            },
        )(
            h("hgroup")(
                h("h4")(item.get("title")),
                h("h5")(item.get("description")),
            ),
        )

    if item.get("data-stop"):
        return h(
            "button",
            role="button",
            klass=klass,
            onclick="window.jakeRadio.stop(); return false;",
        )(
            h("hgroup")(
                h("h4")(item.get("title")),
            ),
        )

    return h(
        "a",
        role="button",
        klass=klass,
        href=item.get("url"),
        # target="_blank",
    )(
        h("hgroup")(
            h("h4")(item.get("title")),
            h("h5")(item.get("description")),
        ),
    )

with open("data.toml", "rb") as f:
    data = tomllib.load(f)
    sections = frag(
        h("div", klass="section")(
            h("hgroup")(
                h("h3")(section.get("title")),
                h("p")(section.get("description")),
            ),
            h(
                "div",
                klass="items",
                style=f"flex-direction: {section.get('direction', 'column')}",
            )(
                h(
                    "div",
                    klass="item",
                    style=f"width: {'100%' if section.get('direction', 'column') == 'column' else 'unset'}",
                )(
                    render_item(
                        item,
                        section.get("item_style", "outline") == "outline",
                    )
                )
                for item in section["items"]
            ),
        )
        for section in data["sections"]
    )

    meta_tags = frag(
        h("title")("8tom"),
        h("meta", name="description", content=data.get("description")),
        h("meta", name="keywords", content=data.get("keywords")),
        h("meta", name="viewport", content="width=device-width, initial-scale=1"),
        h("meta", charset="utf-8"),
        h(
            "link",
            rel="icon",
            href=f"./img/{data.get('favicon', 'favicon.png')}?v=3",
            type="image/png",
        )
    )

    head = frag(
        h("head")(
            meta_tags,
            h("link", rel="stylesheet", href="css/pico.min.css"),
            h("link", rel="stylesheet", href="css/style.css"),
            h("style", rel="stylesheet")(
                f"""
                    [data-theme="dark"], [data-theme="light"] {{
                        --primary: {data.get("primary_color", "#546e7a")} !important;
                    }}
                    * {{
                        text-align: {data.get("text_align", "center")};
                    }}
                    /* Dim-Overlay Styles für Dark Mode (Standard) */
                    #dim-overlay {{
                        position: fixed;
                        top: 0; left: 0; width: 100vw; height: 100vh;
                        background: rgba(0, 0, 0, 0.85); /* Dunkler Schleier */
                        opacity: 0;
                        pointer-events: none;
                        transition: opacity 2s ease-in-out;
                        z-index: 9999;
                    }}
                    body.is-dimmed #dim-overlay {{
                        opacity: 1;
                    }}
                    
                    /* Dim-Overlay Styles für Light Mode */
                    @media (prefers-color-scheme: light) {{
                        #dim-overlay {{
                            background: rgba(255, 255, 255, 0.75); /* Heller Schleier statt schwarz */
                        }}
                    }}
                """
            ),
            raw(
                f"""
                    <script async src="https://www.googletagmanager.com/gtag/js?id={data.get("gtag_id")}"></script>
                    <script>
                    window.dataLayer = window.dataLayer || [];
                    function gtag(){{dataLayer.push(arguments);}}
                    gtag('js', new Date());
                    gtag('config', '{data.get("gtag_id")}');
                    </script>
                """
            )
            if data.get("gtag_id")
            else None,
        ),
    )

    header = frag(
        # h("header", klass="container")(
        #     h("hgroup")(
        #         h(
        #             "img",
        #             klass="avatar",
        #             src=f"img/{data.get('image')}",
        #             alt="avatar",
        #         ),
        #         h("h1")(data.get("name")),
        #         h("p")(data.get("description")) if data.get("description") else None,
        #     ),
        # )
    )

    footer = frag(
        # h("footer", klass="container")(
        #     h("small")("Generated with "),
        #     h(
        #         "a",
        #         klass="",
        #         href="https://github.com/thevahidal/jake/",
        #         target="_blank",
        #     )("Jake"),
        # ),
    )

    # HIER GEÄNDERT: data_theme entfernt, damit der Browser selbst (Hell/Dunkel) entscheidet
    output = html(lang="en")(
        head,
        h("body")(
            h("div", id="dim-overlay")(), # Das Overlay-Element für die Abdunklung
            header,
            h("main", klass="container")(
                sections,
                h("audio", id="radio-player", preload="none")(),
                raw(
                    """
<script>
(() => {
  const player = document.getElementById("radio-player");
  if (!player) return;

  const DEFAULT_TITLE = "8tom";
  let vol = 0.6;
  let active = null;
  
  // -- Dimming Logik --
  let idleTimer = null;
  const IDLE_TIME = 10000; // 10 Sekunden

  const resetIdleTimer = () => {
    if (!active) {
      document.body.classList.remove("is-dimmed");
      clearTimeout(idleTimer);
      return;
    }
    document.body.classList.remove("is-dimmed");
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
      document.body.classList.add("is-dimmed");
    }, IDLE_TIME);
  };

  ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'].forEach(evt => 
    document.addEventListener(evt, resetIdleTimer, { passive: true })
  );

  // Diese Funktion holt die Icecast-Header (Name und Description) direkt vom Stream
  async function fetchIcecastHeaders(streamUrl) {
    try {
      const response = await fetch(streamUrl, { method: 'HEAD' });
      const icyName = response.headers.get('icy-name');
      const icyDesc = response.headers.get('icy-description');
      
      if (icyName && icyDesc) {
        return `${icyName} - ${icyDesc}`;
      } else if (icyName) {
        return icyName;
      }
    } catch (e) {
      console.warn("Konnte Stream-Header nicht lesen", e);
    }
    return null;
  }

  const setActive = async (el) => {
    if (active) active.classList.remove("radio-active");
    active = el;
    
    if (active) {
      active.classList.add("radio-active");
      
      const fallbackTitle = active.dataset.title || "Radio";
      document.title = `${fallbackTitle} — ${DEFAULT_TITLE}`;

      const streamUrl = active.dataset.stream;
      const icyTitle = await fetchIcecastHeaders(streamUrl);
      
      if (icyTitle && active === el) { 
        document.title = `${icyTitle} — ${DEFAULT_TITLE}`;
      }
      
      resetIdleTimer();
      
    } else {
      document.title = DEFAULT_TITLE;
      resetIdleTimer(); 
    }
  };

  const stop = () => {
    try { player.pause(); } catch (e) {}
    player.removeAttribute("src");
    player.load();
    setActive(null);
  };

  document.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("button[data-stream]");
    if (!btn) return;

    setActive(btn);
    player.volume = vol;
    player.src = btn.dataset.stream;

    try {
      await player.play();
    } catch (e) {
      stop();
      console.warn("play() failed", e);
    }
  });

  window.jakeRadio = {
    volDown: () => { vol = Math.max(0, Math.round((vol - 0.1) * 10) / 10); player.volume = vol; },
    volUp:   () => { vol = Math.min(1, Math.round((vol + 0.1) * 10) / 10); player.volume = vol; },
    stop
  };
})();
</script>
"""
                ),
            ),
            footer,
        ),
    ).render()

    with open("dist/index.html", "w") as f:
        f.write(output)
