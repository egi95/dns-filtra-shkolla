#!/usr/bin/env python3
"""Merged category lists for both schools, rebuilt every night after the UT1 download.

Each list = UT1 (University of Toulouse) + the big public collections that track new domains, so new
sites (e.g. poki.io) are covered without anyone adding domains by hand.

  bgt-lojera.txt   games, only during lessons  = UT1 games + CasCas2 school-gaming list
  bgt-torrent.txt  torrent / piracy, always    = UT1 warez + HaGeZi anti-piracy + Block List Project piracy, torrent
  Stored for later (NOT switched on anywhere until the school decides):
  bgt-ai.txt         AI chatbots (exams) = UT1 ai. Before enabling, allow the admin laptop (Claude/Codex use these).
  bgt-mashtrim.txt   scams / fake shops = HaGeZi fake + Block List Project scam
  bgt-kercenime.txt  malware, ransomware, crypto-mining = HaGeZi TIF mini + BLP ransomware, crypto + UT1 cryptojacking
  bgt-droga.txt      drugs and vaping = UT1 drogue + BLP drugs, vaping
  bgt-video.txt      video/streaming for lessons = UT1 audio-video + BLP youtube
  bgt-safesearch.txt search engines without SafeSearch = HaGeZi nosafesearch
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

FIREWALLA = "https://raw.githubusercontent.com/firewalla/fw-public-lists/main/"
SHADOW = "https://raw.githubusercontent.com/ShadowWhisperer/BlockLists/master/Lists/"
F5_AI = "https://raw.githubusercontent.com/f5devcentral/sslo-script-tools/main/sslo-generative-ai-categories/"
# Firewalla publishes these feeds as pointers to the same HaGeZi project.
MIRRORS = {
    HAGEZI + "/anti.piracy.txt": ("Hagezi-Anti-Piracy.txt", "anti.piracy", 10000),
    HAGEZI + "/doh-vpn-proxy-bypass.txt": ("Hagezi-DoH-VPN-Proxy-Bypass.txt", "doh-vpn-proxy-bypass", 8000),
}

LISTS_DEF = {
    "bgt-proxy-confirmed": {
        "title": "Dedicated student proxy domains confirmed by UT1 and ShadowWhisperer",
        "local": ["redirector"], "remote": [], "allow": ALLOW_GAMES + ALLOW_SOCIAL,
        "min": 40, "license": "UT1 CC BY-SA 4.0; ShadowWhisperer Unlicense",
    },
    "bgt-nsfw-ai": {
        "title": "Adult AI services (Firewalla)", "local": [],
        "remote": [FIREWALLA + "nsfw-ai.txt"], "allow": [], "min": 40,
        "license": "Firewalla fw-public-lists GPL-2.0",
    },
    "bgt-hagezi-vpn-proxy": {
        "title": "HaGeZi encrypted DNS, VPN, Tor and proxies",
        "local": [], "remote": [f"{HAGEZI}/doh-vpn-proxy-bypass.txt"], "allow": [], "min": 8000,
    },
    "bgt-blp-redirect": {
        "title": "Block List Project redirects and URL shorteners",
        "local": [], "remote": [f"{BLP}/redirect-ags.txt"], "allow": [], "min": 50000,
        "license": "See the upstream source header and repository license",
    },
    "bgt-lojera": {
        "title": "Lojera (UT1 games + CasCas2 school-gaming)",
        "local": ["games"],
        "learned": ["bgt-mesuar-lojera.txt"],
        "remote": ["https://raw.githubusercontent.com/CasCas2/school-gaming-dns-blocklist/main/mega-gaming-blocklist.txt"],
        "allow": ALLOW_GAMES, "min": 20000,
    },
    "bgt-torrent": {
        "title": "Torrent / pirateri (UT1 warez + HaGeZi anti-piracy + Block List Project piracy, torrent)",
        "local": ["warez"],
        "remote": [f"{HAGEZI}/anti.piracy.txt", f"{BLP}/piracy-ags.txt", f"{BLP}/torrent-ags.txt"],
        "allow": [], "min": 20000,
    },
    "bgt-ai": {
        "title": "AI services (UT1, Nullgen, Firewalla and F5 DevCentral)",
        "local": ["ai"],
        "remote": ["https://raw.githubusercontent.com/nullgen-inc/ai-blocklist/main/lists/ai.domains.txt"],
        "allow": ["google.com", "microsoft.com", "github.com", "amazon.com", "adobe.com",
                  "apple.com", "office.com", "m365.cloud.microsoft", "factory.com", "playground.com",
                  "sourcegraph.com", "assistant.googleapis.com", "aiplatform.googleapis.com"],
        "min": 30,
        "license": "UT1 CC BY-SA 4.0; Nullgen CC0-1.0; additional domains from Firewalla and F5 DevCentral, see source URLs; ShadowWhisperer Unlicense",
    },
    "bgt-mashtrim": {
        "title": "Mashtrime / scam / fake shops (HaGeZi fake + Block List Project scam)",
        "local": [], "remote": [f"{HAGEZI}/fake.txt", f"{BLP}/scam-ags.txt"], "allow": [], "min": 10000,
    },
    "bgt-kercenime": {
        "title": "Kercenime: malware, ransomware, crypto-mining (HaGeZi TIF mini + BLP ransomware, crypto + UT1 cryptojacking)",
        "local": ["cryptojacking"],
        "remote": [f"{HAGEZI}/tif.mini.txt", f"{BLP}/ransomware-ags.txt", f"{BLP}/crypto-ags.txt"],
        "allow": [], "min": 10000,
    },
    "bgt-droga": {
        "title": "Droga dhe vape (UT1 drogue + Block List Project drugs, vaping)",
        "local": ["drogue"], "remote": [f"{BLP}/drugs-ags.txt", f"{BLP}/vaping-ags.txt"], "allow": [], "min": 10000,
    },
    "bgt-video": {
        "title": "Video / streaming per ore mesimore (UT1 audio-video + Block List Project youtube)",
        "local": ["audio-video"], "remote": [f"{BLP}/youtube-ags.txt"], "allow": [], "min": 10000,
    },
    "bgt-safesearch": {
        "title": "Motore kerkimi pa SafeSearch (HaGeZi nosafesearch)",
        "local": [], "remote": [f"{HAGEZI}/nosafesearch.txt"], "allow": [], "min": 50,
    },
    "bgt-sociale": {
        "title": "Rrjete sociale (UT1 social_networks + HaGeZi social + Block List Project facebook, tiktok, twitter)",
        "local": ["social_networks"],
        "learned": ["bgt-mesuar-sociale.txt"],
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


def wildcard_domains(url, minimum):
    rows = fetch(url)
    domains = parse(line.strip().removeprefix("*.") for line in rows)
    if len(domains) < minimum:
        raise ValueError(f"Incomplete domain feed: {url}")
    return domains


def remote_domains(url):
    if url == FIREWALLA + "nsfw-ai.txt":
        return wildcard_domains(url, 40), url
    if url not in MIRRORS:
        return parse(fetch(url)), url
    filename, category, minimum = MIRRORS[url]
    manifest = FIREWALLA + filename
    target = "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/" + category + ".txt"
    try:
        if [s.strip() for s in fetch(manifest) if s.startswith("@")] != ["@" + target]:
            raise ValueError(f"Unexpected feed pointer: {manifest}")
        return wildcard_domains(target, minimum), manifest + " -> " + target
    except (OSError, ValueError) as error:
        print(f"{manifest}: {error}; using HaGeZi directly", file=sys.stderr)
        domains = parse(fetch(url))
        if len(domains) < minimum:
            raise ValueError(f"Incomplete fallback feed: {url}")
        return domains, url


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
    for fname in d.get("learned", []):   # learned by the schools from each other (bgt-learn.py)
        p = os.path.join(LISTS, fname)
        if os.path.exists(p):
            got = parse(open(p, encoding="utf-8"))
            doms |= got
            used.append(f"{fname} ({len(got)})")
    for url in d["remote"]:
        try:
            got, source = remote_domains(url)
            if name == "bgt-ai" and len(got) < 100:
                raise ValueError("Incomplete AI source")
            doms |= got
            used.append(f"{source} ({len(got)})")
        except Exception as e:  # one failing source must not break the night
            print(f"{name}: burimi deshtoi {url}: {e}", file=sys.stderr)
            if name in {"bgt-ai", "bgt-nsfw-ai"} or url in MIRRORS:
                raise
    if name == "bgt-proxy-confirmed":
        url = SHADOW + "Tunnels"
        doms &= wildcard_domains(url, 500)
        # Limit the extra group to explicitly named proxy services. Dual-use
        # vendor homepages also appear in both upstream catalogs.
        doms = {h for h in doms if "proxy" in h or "unblock" in h}
        if len(doms) < d["min"] or len(doms) < old_count(os.path.join(LISTS, name + ".txt")) // 2:
            raise ValueError("Incomplete confirmed proxy list")
        used.append(f"{url} (intersection with UT1, dedicated proxy names)")
    allow = d["allow"]
    if name == "bgt-ai":
        from ai_hosts import AI_SERVICE_HOSTS
        fw = FIREWALLA + "ai-provider.txt"
        broad = F5_AI + "ai-tools-urls"
        chat = F5_AI + "ai-category-chat"
        firewalla_domains = wildcard_domains(fw, 700)
        f5_domains = wildcard_domains(broad, 1200)
        shadow_url = SHADOW + "AI"
        shadow_domains = wildcard_domains(shadow_url, 80)
        confirmed = (firewalla_domains & f5_domains) | (shadow_domains & (firewalla_domains | f5_domains))
        if len(confirmed) < 100:
            raise ValueError("AI catalogs have too few matching domains")
        chats = wildcard_domains(chat, 70)
        shared = ALLOW_GAMES + ALLOW_SOCIAL + ["notion.so", "canva.com", "grammarly.com",
            "xata.io", "tidio.com", "crisp.chat", "commandbar.com", "deepl.com"]
        additions = {host for host in confirmed | chats
                     if not any(host == base or host.endswith("." + base) for base in shared)}
        doms |= additions
        used += [f"{fw}, {broad}, {shadow_url} (at least two sources: {len(confirmed)})", f"{chat} ({len(chats)})"]
        doms = (doms - set(allow)) | AI_SERVICE_HOSTS
    else:
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
        license_note = d.get("license", "UT1 CC BY-SA 4.0; HaGeZi GPL-3.0; Block List Project see upstream; CasCas2 see repo")
        f.write(f"! Licenses: {license_note}\n")
        f.write(f"! Domains: {len(doms)}\n")
        f.writelines(f"||{x}^\n" for x in sorted(doms))
    print(f"{name}: {len(doms)} domene (dje {old})")


if __name__ == "__main__":
    for n, d in LISTS_DEF.items():
        build(n, d)
