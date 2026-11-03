#!/usr/bin/env python3
"""Keep the UniFi (BGT 2) game blocking in sync with lists/ut1-games.txt.

- Domain Lists "BGT Lojera UT1 #1..#N" (domain-group, at most MAX_PER_LIST domains each, educational sites removed)
- for every lesson block one BLOCK policy per list: "BGT Lojera UT1 #k - Ora n" (network Default -> Internet)

Creates what is missing and updates list members; objects with other names are never touched.
Needs UNIFI_API_KEY and UNIFI_CONSOLE (the console id used in the api.ui.com connector URL).
"""
import json
import os
import sys
import urllib.error
import urllib.request

KEY = os.environ["UNIFI_API_KEY"].strip()
CONSOLE = os.environ["UNIFI_CONSOLE"].strip()
BASE = f"https://api.ui.com/v1/connector/consoles/{CONSOLE}/proxy/network"
LIST_FILE = os.path.join(os.path.dirname(__file__), "..", "lists", "ut1-games.txt")

NETWORK_DEFAULT = "6a9eb8681371273baf74e21f"
ZONE_INTERNAL = "6a9f756351a32245e36b216b"
ZONE_EXTERNAL = "6a9f756351a32245e36b216c"
MAX_PER_LIST = 9000          # a single list of 10,000 was accepted, 33,652 was refused
MAX_LISTS = 5
MIN_DOMAINS = 1000           # a smaller list means the download failed: change nothing
DAYS = ["mon", "tue", "wed", "thu", "fri"]
BLOCKS = [("Ora 1", "08:10", "09:20"), ("Ora 2", "09:29", "10:39"), ("Ora 3", "11:07", "12:17"),
          ("Ora 4", "12:26", "13:36"), ("Ora 5", "13:45", "14:55")]
# educational sites that stay reachable (the same exceptions as the AdGuard of BGT 1)
ALLOW = ["kahoot.com", "kahoot.it", "wordwall.net", "quizizz.com", "blooket.com", "scratch.mit.edu", "code.org",
         "chess.com", "lichess.org", "khanacademy.org", "typing.com", "geogebra.org", "duolingo.com",
         "learningapps.org", "liveworksheets.com", "play.google.com", "apps.apple.com"]


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"X-API-Key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path}: HTTP {e.code} {e.read()[:300]!r}")


def load_domains():
    doms = []
    for line in open(LIST_FILE, encoding="utf-8"):
        line = line.strip()
        if line.startswith("||") and line.endswith("^"):
            d = line[2:-1]
            if not any(d == a or d.endswith("." + a) for a in ALLOW):
                doms.append(d)
    return sorted(set(doms))


def policy_body(name, group_id, start, end):
    return {
        "name": name, "enabled": True, "action": "BLOCK", "protocol": "all", "ip_version": "BOTH",
        "connection_state_type": "ALL", "connection_states": [], "create_allow_respond": False, "logging": False,
        "match_ip_sec": False, "match_opposite_protocol": False, "icmp_typename": "ANY", "icmp_v6_typename": "ANY",
        "source": {"matching_target": "NETWORK", "network_ids": [NETWORK_DEFAULT], "zone_id": ZONE_INTERNAL,
                   "port_matching_type": "ANY", "match_opposite_networks": False, "match_opposite_ports": False,
                   "match_mac": False},
        "destination": {"matching_target": "WEB", "matching_target_type": "OBJECT", "web_group_id": group_id,
                        "zone_id": ZONE_EXTERNAL, "port_matching_type": "ANY", "match_opposite_ports": False},
        "schedule": {"mode": "EVERY_WEEK", "repeat_on_days": DAYS, "time_all_day": False,
                     "time_range_start": start, "time_range_end": end},
    }


def main():
    doms = load_domains()
    if len(doms) < MIN_DOMAINS:
        sys.exit(f"vetem {len(doms)} domene ne liste, asgje nuk ndryshohet")
    n = -(-len(doms) // MAX_PER_LIST)
    if n > MAX_LISTS:
        sys.exit(f"{len(doms)} domene kerkojne {n} lista (maksimumi {MAX_LISTS}), asgje nuk ndryshohet")
    size = -(-len(doms) // n)
    chunks = [doms[i:i + size] for i in range(0, len(doms), size)]

    groups = {g["name"]: g for g in api("GET", "/api/s/default/rest/firewallgroup")["data"]}
    gid = {}
    for k, members in enumerate(chunks, 1):
        name = f"BGT Lojera UT1 #{k}"
        body = {"name": name, "group_type": "domain-group", "group_members": members}
        g = groups.get(name)
        if g is None:
            gid[k] = api("POST", "/api/s/default/rest/firewallgroup", body)["data"][0]["_id"]
            print(f"{name}: krijuar me {len(members)} domene")
        else:
            gid[k] = g["_id"]
            if sorted(g.get("group_members", [])) != members:
                api("PUT", f"/api/s/default/rest/firewallgroup/{g['_id']}", body)
                print(f"{name}: perditesuar, {len(members)} domene")
            else:
                print(f"{name}: pa ndryshim ({len(members)} domene)")

    policies = {p["name"]: p for p in api("GET", "/v2/api/site/default/firewall-policies")}
    created = 0
    for k in gid:
        for ora, start, end in BLOCKS:
            name = f"BGT Lojera UT1 #{k} - {ora}"
            p = policies.get(name)
            if p is None:
                api("POST", "/v2/api/site/default/firewall-policies", policy_body(name, gid[k], start, end))
                created += 1
            elif p.get("destination", {}).get("web_group_id") != gid[k]:
                api("PUT", f"/v2/api/site/default/firewall-policies/{p['_id']}",
                    dict(policy_body(name, gid[k], start, end), _id=p["_id"]))
                print(f"{name}: lista u lidh perseri")
    print(f"{len(doms)} domene ne {len(chunks)} lista; rregulla te reja: {created}; "
          f"rregulla gjithsej: {len(gid) * len(BLOCKS)}")


if __name__ == "__main__":
    main()
