import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = {
    "BBC News": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
}
SITE_NAME = "Breaking News"
ACCENT = "#C8102E"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NewsBuilder"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()


def parse(source, xml_bytes):
    items = []
    for it in ET.fromstring(xml_bytes).iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        try:
            when = parsedate_to_datetime(it.findtext("pubDate"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if title and link.startswith(("http://", "https://")):
            items.append({"title": title, "link": link, "source": source, "when": when})
    return items


def collect(fetcher=fetch):
    items = []
    for name, url in FEEDS.items():
        try:
            items += parse(name, fetcher(url))
        except Exception as e:
            print(f"skip {name}: {e}")
    seen, out = set(), []
    for i in sorted(items, key=lambda x: x["when"], reverse=True):
        key = i["title"].lower()
        if key not in seen:
            seen.add(key)
            out.append(i)
    return out


def ago(when):
    m = int((datetime.now(timezone.utc) - when).total_seconds() // 60)
    if m < 1:
        return "just now"
    if m < 60:
        return f"{m} min ago"
    return f"{m // 60} h ago" if m < 1440 else f"{m // 1440} d ago"


def link(i, style):
    return (f'<a href="{html.escape(i["link"])}" target="_blank" rel="noopener" style="{style}">'
            f'{html.escape(i["title"])}</a>')


def render(items):
    if not items:
        return "<p>No stories available right now.</p>"
    top, live, more = items[0], items[1:7], items[7:15]
    meta = lambda i: f'<div class="meta">{html.escape(i["source"])} · {ago(i["when"])}</div>'
    live_html = "".join(
        f'<div class="row"><span class="src">{html.escape(i["source"])}</span>'
        f'<div>{link(i, "font-weight:600")}<div class="meta">{ago(i["when"])}</div></div></div>' for i in live)
    more_html = "".join(f'<div class="card">{link(i, "font:700 20px/1.3 Georgia,serif")}{meta(i)}</div>' for i in more)
    return f"""
<div class="bar"><b>BREAKING</b> {link(top, "color:#fff")}</div>
<header><h1>{html.escape(SITE_NAME)}</h1><span class="meta">Updated {datetime.now(timezone.utc):%H:%M} UTC</span></header>
<main><section class="lead"><span class="tag">TOP STORY</span>
<h2>{link(top, "color:#0B0F14")}</h2>{meta(top)}</section>
<aside><h3>Live updates</h3>{live_html}</aside></main>
<h3 class="more">More stories</h3><div class="grid">{more_html}</div>
<footer>Headlines and links belong to their publishers: {html.escape(", ".join(FEEDS))}.</footer>"""


CSS = f"""body{{margin:0;font-family:Inter,Arial,sans-serif;color:#0B0F14;max-width:1200px;margin:auto}}
a{{text-decoration:none;color:inherit}}a:hover{{color:{ACCENT}}}
.bar{{background:{ACCENT};color:#fff;padding:10px 24px}}.bar b{{background:#fff;color:{ACCENT};padding:3px 8px;margin-inline-end:12px}}
header{{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid #D9DDE2}}
h1{{margin:0;font:700 32px Georgia,serif}}main{{display:flex;gap:40px;padding:32px 24px;flex-wrap:wrap}}
.lead{{flex:2 1 520px}}.lead h2{{font:700 38px/1.2 Georgia,serif;margin:8px 0}}.tag{{color:{ACCENT};font-weight:800;font-size:13px}}
aside{{flex:1 1 300px}}.row{{display:flex;gap:12px;padding:12px 0;border-top:1px solid #D9DDE2}}
.src{{flex:0 0 90px;color:{ACCENT};font-weight:700;font-size:13px}}.meta{{color:#4A5360;font-size:14px}}
.more{{padding:0 24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px;padding:0 24px 40px}}
footer{{background:#0B0F14;color:#fff;padding:24px;font-size:14px}}"""


if __name__ == "__main__":
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="300">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(SITE_NAME)}</title>'
            f'<style>{CSS}</style></head><body>{render(collect())}</body></html>')
    open("index.html", "w", encoding="utf-8").write(page)
    print("index.html written")
