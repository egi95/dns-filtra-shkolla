#!/usr/bin/env python3
"""Merged category lists for both schools, rebuilt every night after the UT1 download.

Each list = UT1 (University of Toulouse) + the big public collections that track new domains, so new
sites (e.g. poki.io) are covered without anyone adding domains by hand.

  bgt-lojera.txt   games, only during lessons  = UT1 games + CasCas2 school-gaming list
  bgt-torrent.txt  torrent / piracy, always    = UT1 warez + HaGeZi anti-piracy + Block List Project piracy, torrent
  bgt-sociale.txt  social networks (PREPARED, not switched on anywhere yet)
                                               = UT1 social_networks + HaGeZi social + Block List Project facebook,
                                                 tiktok, twitter

Safety: a source that fails to download is skipped; if a list would shrink below half of yesterday's size,
yesterday's file is kept unchanged.
"""
import os
import re
import sys
import urllib.request

LISTS = os.path.join(os.path.dirname(__file__), "..", "lists")
HAGEZI = "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock"
BLP = "https://blocklistproject.github.io/Lists/adguard"

# educational sites that stay reachable (same exceptions as AdGuard of BGT 1 and unifi_sync.py)
ALLOW_GAMES = ["kahoot.com", "kahoot.it", "wordwall.net", "quizizz.com", "blooket.com", "scratch.mit.edu",
               "code.org", "chess.com", "lichess.org", "khanacademy.org", "typing.com", "geogebra.org",
               "duolingo.com", "learningapps.org", "liveworksheets.com", "play.google.com", "apps.apple.com"]
# WhatsApp and Viber must stay allowed in both schools, even when social networks get blocked
ALLOW_SOCIAL = ["whatsapp.com", "whatsapp.net", "wa.me", "viber.com", "viber.co"]

LISTS_DEF = {
    "bgt-lojera": {
        "title": "Lojera (UT1 games + CasCas2 school-gaming)",
        "local": ["games"],
        "remote": ["https://raw.githubusercontent.com/CasCas2/school-gaming-dns-blocklist/main/mega-gaming-blocklist.txt"],
        "allow": ALLOW_GAMES, "min": 20000,
    },
    "bgt-torrent": {
        "title": "Torrent / pirateri (UT1 warez + HaGeZi anti-piracy + Block List Project piracy, torrent)",
        "local": ["warez"],
        "remote": [f"{HAGEZI}/anti.piracy.txt", f"{BLP}/piracy-ags.txt", f"{BLP}/torrent-ags.txt"],
        "allow": [], "min": 20000,
    },
    "bgt-sociale": {
        "title": "Rrjete sociale (UT1 social_networks + HaGeZi social + Block List Project facebook, tiktok, twitter)",
        "local": ["social_networks"],
        "remote": [f"{HAGEZI}/social.txt", f"{BLP}/facebook-ags.txt", f"{BLP}/tiktok-ags.txt",
                   f"{BLP}/twitter-ags.txt"],
        "allow": ALLOW_SOCIAL, "min": 5000,
    },
}

DOMAIN = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")


def parse(lines):
    """Plain domains from AdGuard (||d^), hosts (0.0.0.0 d) or plain-domain lists; skips exceptions, regex, wildcards."""
    out = set()
    for line in lines:
        line = line.strip().lower()
        if not line or line[0] in "!#@/[":
            continue
        line = re.sub(r"^(0\.0\.0\.0|127\.0\.0\.1)\s+", "", line)
        if line.startswith("||"):
            line = line[2:]
        line = line.split("^")[0].split("$")[0].strip()
        if "*" in line:
            continue
        if DOMAIN.match(line) and not re.fullmatch(r"[0-9.]+", line):
            out.add(line)
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dns-filtra-shkolla/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace").splitlines()


def old_count(path):
    if not os.path.exists(path):
        return 0
    return sum(1 for l in open(path, encoding="utf-8") if l.startswith("||"))


def build(name, d):
    doms, used = set(), []
    for cat in d["local"]:
        p = os.path.join(LISTS, f"ut1-{cat}.txt")
        if os.path.exists(p):
            got = parse(open(p, encoding="utf-8"))
            doms |= got
            used.append(f"UT1 {cat} ({len(got)})")
    for url in d["remote"]:
        try:
            got = parse(fetch(url))
            doms |= got
            used.append(f"{url} ({len(got)})")
        except Exception as e:  # one failing source must not break the night
            print(f"{name}: burimi deshtoi {url}: {e}", file=sys.stderr)
    allow = d["allow"]
    doms = {x for x in doms if not any(x == a or x.endswith("." + a) for a in allow)}
    path = os.path.join(LISTS, f"{name}.txt")
    old = old_count(path)
    if len(doms) < d["min"] or len(doms) < old // 2:
        print(f"{name}: {len(doms)} domene (dje {old}), lista nuk ndryshohet")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"! Title: {d['title']}\n")
        for u in used:
            f.write(f"! Source: {u}\n")
        f.write("! Licenses: UT1 CC BY-SA 4.0; HaGeZi GPL-3.0; Block List Project Unlicense; CasCas2 see repo\n")
        f.write(f"! Domains: {len(doms)}\n")
        f.writelines(f"||{x}^\n" for x in sorted(doms))
    print(f"{name}: {len(doms)} domene (dje {old})")


if __name__ == "__main__":
    for n, d in LISTS_DEF.items():
        build(n, d)
