#!/usr/bin/env python3
"""IP lists for the routers, rebuilt every 6 hours (Tor changes often).

  lists/bgt-tor-ip.txt         every Tor relay that is running now (Tor Project Onionoo), one IPv4 per line
  lists/bgt-spamhaus-drop.txt  Spamhaus DROP: hijacked / criminal networks, one CIDR per line

Used by the BGT 1 server (router address-lists BGT-TOR, BGT-DROP) and, through the shared threat layer,
by BGT 2 (UniFi IP groups). Same safety as the domain lists: if a download looks wrong (too few/many
entries, or less than half of the previous list) the previous file is kept unchanged.
"""
import ipaddress
import json
import os
import time
import urllib.request

LISTS = os.path.join(os.path.dirname(__file__), "..", "lists")
UA = {"User-Agent": "dns-filtra-shkolla/1.0"}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read().decode("utf-8", "replace")


def previous(name):
    p = os.path.join(LISTS, name)
    if not os.path.exists(p):
        return 0
    return sum(1 for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#"))


def write(name, title, source, items, lo, hi):
    old = previous(name)
    if not lo <= len(items) <= hi or len(items) < old // 2:
        print(f"{name}: {len(items)} (dje {old}, pritet {lo}-{hi}), lista nuk ndryshohet")
        return
    with open(os.path.join(LISTS, name), "w", encoding="utf-8") as f:
        f.write(f"# Title: {title}\n# Source: {source}\n# Entries: {len(items)}\n")
        f.write(f"# Updated: {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC\n")
        f.writelines(f"{x}\n" for x in items)
    print(f"{name}: {len(items)} (dje {old})")


def tor():
    data = json.loads(fetch("https://onionoo.torproject.org/summary?type=relay&running=true"))
    ips = set()
    for relay in data.get("relays", []):
        for a in relay.get("a", []):
            try:
                ip = ipaddress.ip_address(a.strip("[]"))
            except ValueError:
                continue
            if ip.version == 4 and ip.is_global:
                ips.add(ip)
    return [str(i) for i in sorted(ips)]


def spamhaus():
    nets = set()
    for line in fetch("https://www.spamhaus.org/drop/drop_v4.json").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if "cidr" in d:
            n = ipaddress.ip_network(d["cidr"], strict=False)
            if n.version == 4 and not n.is_private:
                nets.add(n)
    return [str(n) for n in sorted(nets)]


if __name__ == "__main__":
    for name, title, src, fn, lo, hi in [
        ("bgt-tor-ip.txt", "Tor relays (running)", "Tor Project Onionoo", tor, 3000, 20000),
        ("bgt-spamhaus-drop.txt", "Spamhaus DROP (IPv4)", "https://www.spamhaus.org/drop/", spamhaus, 500, 5000),
    ]:
        try:
            write(name, title, src, fn(), lo, hi)
        except Exception as e:  # one failing source must not break the other
            print(f"{name}: burimi deshtoi ({e}), lista nuk ndryshohet")
