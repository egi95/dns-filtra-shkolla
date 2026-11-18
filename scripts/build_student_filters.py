"""Build the three independently switchable AdGuard subscriptions for BGT1 Students."""
from pathlib import Path
import json
from urllib.request import urlopen

from ai_hosts import AI_SERVICE_HOSTS
from build_lists import ALLOW_SOCIAL, parse

LISTS = Path(__file__).resolve().parents[1] / "lists"
SERVICES_URL = "https://raw.githubusercontent.com/AdguardTeam/HostlistsRegistry/main/assets/services.json"
GAME_SERVICES = set("""roblox epic_games steam minecraft leagueoflegends valorant riot_games playstation xboxlive
battle_net electronic_arts ubisoft shell_shockers activision_blizzard blizzard_entertainment gog nintendo origin
rockstar_games wargaming warnerbrosgames""".split())
SOCIAL = set("""facebook.com fb.com fb.me fbcdn.net fbsbx.com messenger.com instagram.com cdninstagram.com ig.me
threads.net tiktok.com tiktokv.com tiktokcdn.com tiktokcdn-us.com tiktokv.us byteoversea.com ibytedtos.com
ibyteimg.com muscdn.com snapchat.com sc-cdn.net snap-dev.net twitter.com x.com twimg.com t.co reddit.com redd.it
redditmedia.com redditstatic.com pinterest.com pinimg.com tumblr.com 9gag.com bsky.app likee.video kwai.com""".split())


def domains(stem):
    return parse((LISTS / (stem + ".txt")).read_text(encoding="utf-8").splitlines())


def write(category, rules, important=False):
    suffix = "$client=10.10.0.0/16" + (",important" if important else "")
    if any("$" in rule or not rule.startswith("|") for rule in rules):
        raise ValueError("Unexpected upstream rule syntax")
    folder = LISTS / "students"
    folder.mkdir(exist_ok=True)
    body = ["! BGT Students - " + category, "! Sources and licenses: see parent list and scripts/build_student_filters.py."]
    (folder / (category + ".txt")).write_text("\n".join(body + [r + suffix for r in sorted(rules)]) + "\n", encoding="utf-8")


def main():
    games = domains("bgt-lojera") | {"poki-gdn.com", "roblox.com"}
    ai = domains("bgt-ai") | AI_SERVICE_HOSTS
    social = SOCIAL | domains("bgt-mesuar-sociale")
    social = {d for d in social if not any(d == a or d.endswith("." + a) for a in ALLOW_SOCIAL)}
    if len(games) < 1000 or not {"copilot.microsoft.com", "gemini.google.com", "chatgpt.com"} <= ai:
        raise ValueError("Incomplete source lists")
    with urlopen(SERVICES_URL, timeout=30) as response:
        services = {s["id"]: s["rules"] for s in json.load(response)["blocked_services"]}
    game_rules = {"||" + d + "^" for d in games}
    for service in GAME_SERVICES:
        game_rules.update(services[service])
    write("lojera", game_rules)
    write("sociale", {"||" + d + "^" for d in social})
    write("ai", {"||" + d + "^" for d in ai}, important=True)


if __name__ == "__main__":
    main()

