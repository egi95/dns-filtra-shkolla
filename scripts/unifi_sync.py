#!/usr/bin/env python3
"""Keep the UniFi (BGT 2) blocking in sync with the lists of this repository.

- Games, only during lessons: Domain Lists "BGT Lojera UT1 #1..#N" (lists/bgt-lojera.txt = UT1 games + CasCas2
  school-gaming, plus EXTRA_GAMES, educational sites removed) and one BLOCK policy per list and lesson block: "BGT Lojera UT1 #k - Ora n".
- Security, always: Domain List "BGT Siguria UT1" (UT1 ddos, dangerous_material, warez, tricheur) and
  the BLOCK policy "BGT Siguria UT1 - gjithmone". The other security categories come from the UniFi Content Filter.
- AI chatbots, only on request (exams): Domain List "BGT AI UT1" and the BLOCK policy "BGT AI UT1 - provime",
  created switched off. The script never changes whether an existing policy is on or off.

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
LISTS = os.path.join(os.path.dirname(__file__), "..", "lists")

NETWORK_DEFAULT = "6a9eb8681371273baf74e21f"
ZONE_INTERNAL = "6a9f756351a32245e36b216b"
ZONE_EXTERNAL = "6a9f756351a32245e36b216c"
MAX_PER_LIST = 9000          # a single list of 10,000 was accepted, 33,652 was refused
MAX_GAME_LISTS = 5
MIN_GAME_DOMAINS = 1000      # a smaller games list means the download failed: change nothing
DAYS = ["mon", "tue", "wed", "thu", "fri"]
BLOCKS = [("Ora 1", "08:10", "09:20"), ("Ora 2", "09:29", "10:39"), ("Ora 3", "11:07", "12:17"),
          ("Ora 4", "12:26", "13:36"), ("Ora 5", "13:45", "14:55")]
ALWAYS = {"mode": "ALWAYS"}
# educational sites that stay reachable (the same exceptions as the AdGuard of BGT 1)
ALLOW = ["kahoot.com", "kahoot.it", "wordwall.net", "quizizz.com", "blooket.com", "scratch.mit.edu", "code.org",
         "chess.com", "lichess.org", "khanacademy.org", "typing.com", "geogebra.org", "duolingo.com",
         "learningapps.org", "liveworksheets.com", "play.google.com", "apps.apple.com"]
# browser-game sites blocked in BGT 1 that are missing from UT1
EXTRA_GAMES = ["poki-gdn.com"]
SECURITY_CATS = ["ddos", "dangerous_material", "warez", "tricheur"]


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"X-API-Key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path}: HTTP {e.code} {e.read()[:300]!r}")


def read_list(category):
    path = os.path.join(LISTS, f"ut1-{category}.txt")
    doms = set()
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("||") and line.endswith("^"):
            d = line[2:-1]
            if not any(d == a or d.endswith("." + a) for a in ALLOW):
                doms.add(d)
    return doms


def policy_body(name, group_id, schedule, enabled):
    return {
        "name": name, "enabled": enabled, "action": "BLOCK", "protocol": "all", "ip_version": "BOTH",
        "connection_state_type": "ALL", "connection_states": [], "create_allow_respond": False, "logging": False,
        "match_ip_sec": False, "match_opposite_protocol": False, "icmp_typename": "ANY", "icmp_v6_typename": "ANY",
        "source": {"matching_target": "NETWORK", "network_ids": [NETWORK_DEFAULT], "zone_id": ZONE_INTERNAL,
                   "port_matching_type": "ANY", "match_opposite_networks": False, "match_opposite_ports": False,
                   "match_mac": False},
        "destination": {"matching_target": "WEB", "matching_target_type": "OBJECT", "web_group_id": group_id,
                        "zone_id": ZONE_EXTERNAL, "port_matching_type": "ANY", "match_opposite_ports": False},
        "schedule": schedule,
    }


def lesson(start, end):
    return {"mode": "EVERY_WEEK", "repeat_on_days": DAYS, "time_all_day": False,
            "time_range_start": start, "time_range_end": end}


class Sync:
    def __init__(self):
        self.groups = {g["name"]: g for g in api("GET", "/api/s/default/rest/firewallgroup")["data"]}
        self.policies = {p["name"]: p for p in api("GET", "/v2/api/site/default/firewall-policies")}
        self.created = 0

    def group(self, name, members):
        body = {"name": name, "group_type": "domain-group", "group_members": members}
        g = self.groups.get(name)
        if g is None:
            gid = api("POST", "/api/s/default/rest/firewallgroup", body)["data"][0]["_id"]
            print(f"{name}: krijuar me {len(members)} domene")
            return gid
        if sorted(g.get("group_members", [])) != members:
            api("PUT", f"/api/s/default/rest/firewallgroup/{g['_id']}", body)
            print(f"{name}: perditesuar, {len(members)} domene")
        else:
            print(f"{name}: pa ndryshim ({len(members)} domene)")
        return g["_id"]

    def policy(self, name, gid, schedule, enabled_when_new=True):
        p = self.policies.get(name)
        if p is None:
            api("POST", "/v2/api/site/default/firewall-policies", policy_body(name, gid, schedule, enabled_when_new))
            self.created += 1
        elif p.get("destination", {}).get("web_group_id") != gid:
            body = dict(policy_body(name, gid, schedule, p.get("enabled", enabled_when_new)), _id=p["_id"])
            api("PUT", f"/v2/api/site/default/firewall-policies/{p['_id']}", body)
            print(f"{name}: lista u lidh perseri")


def read_merged(name):
    """A merged list built by build_lists.py (UT1 + other collections), minus the educational exceptions."""
    path = os.path.join(LISTS, f"{name}.txt")
    if not os.path.exists(path):
        return None
    doms = set()
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("||") and line.endswith("^"):
            d = line[2:-1]
            if not any(d == a or d.endswith("." + a) for a in ALLOW):
                doms.add(d)
    return doms


def main():
    merged = read_merged("bgt-lojera")   # UT1 games + CasCas2 school-gaming (has poki.io, unblocked-games mirrors)
    games = sorted((merged if merged else read_list("games")) | set(EXTRA_GAMES))
    if len(games) < MIN_GAME_DOMAINS:
        sys.exit(f"vetem {len(games)} domene lojerash, asgje nuk ndryshohet")
    n = -(-len(games) // MAX_PER_LIST)
    if n > MAX_GAME_LISTS:
        sys.exit(f"{len(games)} domene kerkojne {n} lista (maksimumi {MAX_GAME_LISTS}), asgje nuk ndryshohet")
    size = -(-len(games) // n)
    chunks = [games[i:i + size] for i in range(0, len(games), size)]

    s = Sync()
    for k, members in enumerate(chunks, 1):
        gid = s.group(f"BGT Lojera UT1 #{k}", members)
        for ora, start, end in BLOCKS:
            s.policy(f"BGT Lojera UT1 #{k} - {ora}", gid, lesson(start, end))

    security = sorted(set().union(*(read_list(c) for c in SECURITY_CATS)))
    if security:
        s.policy("BGT Siguria UT1 - gjithmone", s.group("BGT Siguria UT1", security), ALWAYS)

    ai = sorted(read_list("ai"))
    if ai:
        s.policy("BGT AI UT1 - provime", s.group("BGT AI UT1", ai), ALWAYS, enabled_when_new=False)

    print(f"lojera: {len(games)} domene ne {len(chunks)} lista; siguria: {len(security)}; AI: {len(ai)}; "
          f"rregulla te reja: {s.created}")


if __name__ == "__main__":
    main()
