#!/usr/bin/env python3
"""Brand one HTML mailer for every brand (plus GRAPE versions).

Usage:
  python3 -I scripts/brand.py MAILER.html --campaign "Woollam Consult - Bradford SSH" \
      [--grape-url URL] [--landing-url URL] [--brands "Prop Invest,PIG"] [--no-grape]

Writes mailers/<campaign-slug>/<brand-slug>.html (and <brand-slug>-grape.html for
the GRAPE brands) inside this repository, runs every check, and prints the public
GitHub Pages address of each file. Edits the HTML as a string so Outlook's
conditional comments survive. Re-running on an already-branded file swaps the
branding instead of stacking it.
"""
import argparse, collections, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = "https://mailermaker.github.io/email-assets/"
BRANDS = ["Prop Invest", "PIG", "Property Wealth Group", "Ression", "Rock Harbour Invest",
          "Global Investment Property", "Global Property Invest", "Global Invest Real Estate",
          "Asset Invest Group", "Investor Nation 2022"]
GRAPE_BRANDS = ["Prop Invest", "Asset Invest Group"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


WRAP = re.compile(r'<tbody class="brand-wrap">.*?</tbody>', re.S)
BLK = re.compile(r'<!-- BRAND-(HEADER|FOOTER):.*?<!-- /BRAND-\1 -->', re.S)


def strip_branding(html):
    return BLK.sub("", WRAP.sub("", html))


def block(kind, brand, url, w):
    return (f'<!-- BRAND-{kind}:{brand} --><!--[if (gte mso 9)|(IE)]><table align="center" border="0" '
            f'cellspacing="0" cellpadding="0" width="{w}" style="width:{w}px;"><tr><td><![endif]-->'
            f'<table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" '
            f'style="max-width:{w}px;" role="presentation"><tr><td valign="top" '
            f'style="padding:0;line-height:0;font-size:0;"><img src="{url}" width="{w}" alt="{brand}" '
            f'border="0" style="display:block;width:100%;max-width:{w}px;height:auto;border:0;'
            f'outline:none;text-decoration:none;"/></td></tr></table><!--[if (gte mso 9)|(IE)]>'
            f'</td></tr></table><![endif]--><!-- /BRAND-{kind} -->')


def matching_close(html, start):
    """Index of the </table> that closes the <table> opening at `start`."""
    depth, i = 0, start
    for m in re.finditer(r"<table\b|</table>", html[start:]):
        depth += 1 if m.group(0).startswith("<table") else -1
        if depth == 0:
            return start + m.start()
    raise SystemExit("Could not find the end of the root table.")


def brand_html(base, brand):
    body = base.index("<body")
    m = re.search(r"max-width:\s*(\d+)px", base[body:])
    w = m.group(1) if m else "600"
    s = slug(brand)
    head = block("HEADER", brand, f"{PAGES}images/{s}-header.png", w)
    foot = block("FOOTER", brand, f"{PAGES}images/{s}-footer.png", w)
    root = re.search(r'<table[^>]*id="root"[^>]*>', base)
    if root:  # Mailchimp-style export
        wrap = lambda x: f'<tbody class="brand-wrap"><tr><td align="center" valign="top">{x}</td></tr></tbody>'
        hpos = root.end()
        fs = base.find('class="mceFooterSection"', body)
        wrappers = [x.start() for x in re.finditer(r'<tbody[^>]*class="mceWrapper"[^>]*>', base)
                    if fs != -1 and x.start() < fs]
        fpos = wrappers[-1] if wrappers else matching_close(base, root.start())
        return base[:hpos] + wrap(head) + base[hpos:fpos] + wrap(foot) + base[fpos:], w
    # Any other HTML: after <body> (and any hidden preheader), and before </body>
    hpos = base.index(">", body) + 1
    pre = re.match(r'\s*<div[^>]*display:\s*none[^>]*>.*?</div>', base[hpos:], re.S)
    if pre:
        hpos += pre.end()
    fpos = base.rindex("</body>")
    return base[:hpos] + head + base[hpos:fpos] + foot + base[fpos:], w


def landing_url(html):
    hrefs = [h for h in re.findall(r'href="(https?://[^"]+)"', html)
             if "unsubscribe" not in h.lower() and "*|" not in h]
    counts = collections.Counter(hrefs).most_common()
    if not counts:
        raise SystemExit("No links found in the mailer, so there is nothing to swap for GRAPE.")
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        raise SystemExit("More than one candidate landing page; pass --landing-url. Links: "
                         + "; ".join(f"{u} x{n}" for u, n in counts))
    return counts[0][0], counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mailer")
    ap.add_argument("--campaign", required=True, help='e.g. "Woollam Consult - Bradford SSH"')
    ap.add_argument("--brands", help="comma-separated subset; default all 10")
    ap.add_argument("--grape-url", help="GRAPE landing page URL (never guess it)")
    ap.add_argument("--landing-url", help="landing page to replace in GRAPE versions (auto-detected if omitted)")
    ap.add_argument("--no-grape", action="store_true")
    a = ap.parse_args()

    brands = [b.strip() for b in a.brands.split(",")] if a.brands else BRANDS
    for b in brands:
        if b not in BRANDS:
            raise SystemExit(f"Unknown brand {b!r}. Known: {', '.join(BRANDS)}")
    base = strip_branding(open(a.mailer, encoding="utf-8").read())
    outdir = os.path.join(REPO, "mailers", slug(a.campaign))
    os.makedirs(outdir, exist_ok=True)
    made = []
    for b in brands:
        out, w = brand_html(base, b)
        s = slug(b)
        assert out.count("BRAND-HEADER:") == 1 and out.count("BRAND-FOOTER:") == 1, b
        assert out.count("<table") == out.count("</table>"), b
        assert strip_branding(out) == base, b
        for kind in ("header", "footer"):
            assert os.path.exists(os.path.join(REPO, "images", f"{s}-{kind}.png")), f"missing {s}-{kind}.png"
        open(os.path.join(outdir, f"{s}.html"), "w", encoding="utf-8").write(out)
        made.append((b, f"{s}.html"))
        if b in GRAPE_BRANDS and a.grape_url and not a.no_grape:
            land, counts = (a.landing_url, None) if a.landing_url else landing_url(out)
            old, new = f'href="{land}"', f'href="{a.grape_url}"'
            n = out.count(old)
            g = out.replace(old, new)
            assert n > 0 and old not in g and g.count(new) == n and g.replace(new, old) == out, b
            open(os.path.join(outdir, f"{s}-grape.html"), "w", encoding="utf-8").write(g)
            made.append((f"{b} GRAPE", f"{s}-grape.html"))
            print(f"GRAPE {b}: replaced {n} links to {land}")
    print(f"width {w}px | {len(made)} files in mailers/{slug(a.campaign)}/")
    for b, f in made:
        print(f"{b}\t{PAGES}mailers/{slug(a.campaign)}/{f}")
    if a.grape_url is None and not a.no_grape and any(b in GRAPE_BRANDS for b in brands):
        print("NOTE: no --grape-url given, so no GRAPE versions were made.")


if __name__ == "__main__":
    main()
