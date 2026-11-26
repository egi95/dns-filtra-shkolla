"""Classify cross-school observations with independent domain evidence."""
from pathlib import Path
import json
import re
from ai_hosts import AI_SERVICE_HOSTS

LISTS = Path(__file__).resolve().parents[1] / "lists"
FEEDS = {"ai": ("ut1-ai", "bgt-ai"), "vpn": ("ut1-vpn", "ut1-doh", "ut1-residential-proxies", "bgt-hagezi-vpn-proxy", "bgt-proxy-confirmed"),
         "siguria": ("ut1-malware", "ut1-phishing", "ut1-cryptojacking", "ut1-stalkerware", "ut1-ddos")}
PROTECTED = ("google.com", "googleapis.com", "gstatic.com", "googleusercontent.com", "googlezip.net", "apple.com", "icloud.com", "icloud-content.com", "aapljs.com", "safebrowsing.apple", "norton.com", "microsoft.com", "office.com", "live.com", "github.com", "githubusercontent.com", "github.io", "amazonaws.com", "cloudfront.net", "azure.com", "azurefd.net", "azurewebsites.net", "akamai.net", "akamaized.net", "cloudflare.com", "cloudflare.net", "workers.dev", "pages.dev", "whatsapp.com", "whatsapp.net", "wa.me", "viber.com", "viber.co", "edupage.org", "bgt.school", "kahoot.com", "quizizz.com")
# Frozen pre-migration group; ambiguity never creates a new permanent block.
LEGACY = frozenset(Path(__file__).with_name("exchange-legacy.txt").read_text().splitlines())
HOST = re.compile(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\Z")


def protected(host):
    return any(host == suffix or host.endswith("." + suffix) for suffix in PROTECTED)


class Catalog:
    def __init__(self, folder):
        self.entries = {}
        for category, feeds in FEEDS.items():
            for feed in feeds:
                with (folder / (feed + ".txt")).open(encoding="utf-8") as stream:
                    for line in stream:
                        rule = line.strip()
                        if rule.startswith("||") and rule.endswith("^"):
                            self.entries.setdefault(rule[2:-1], {})[category] = feed
        for host in AI_SERVICE_HOSTS:
            self.entries.setdefault(host, {})["ai"] = "ai_hosts"

    def match(self, host):
        if not HOST.fullmatch(host) or (protected(host) and host not in AI_SERVICE_HOSTS):
            return None
        labels = host.split(".")
        matches = {}
        for i in range(len(labels) - 1):
            parent = ".".join(labels[i:])
            for category, feed in self.entries.get(parent, {}).items():
                matches.setdefault(category, (category, parent, feed))
        if len(matches) == 1:
            return next(iter(matches.values()))
        return None


def read_exchange(folder):
    catalog = Catalog(folder)
    result = {name: set() for name in (*FEEDS, "legacy")}
    records = json.loads((folder / "bgt-mesuar.json").read_text(encoding="utf-8"))
    for entry in records.values():
        host = entry["domain"]
        if entry["kind"] != "gjithmone":
            continue
        match = catalog.match(host)
        if match:
            result[match[0]].add(host)
        elif host in LEGACY:
            # Existing enforcement is retained until the ambiguous legacy entry is reviewed.
            result["legacy"].add(host)
    path = folder / "bgt-shkembim.json"
    if path.exists():
        for entry in json.loads(path.read_text(encoding="utf-8")):
            host = entry["domain"]
            match = catalog.match(host)
            if entry["category"] not in FEEDS or not HOST.fullmatch(host):
                raise ValueError("Invalid exchange record")
            if protected(host) and host not in AI_SERVICE_HOSTS:
                continue
            reviewed = entry.get("basis") == "reviewed" and not match
            if reviewed or (match and match[0] == entry["category"] and match[1] == host):
                result[entry["category"]].add(host)
    return result
