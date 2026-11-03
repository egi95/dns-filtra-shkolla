# dns-filtra-shkolla

DNS block lists in AdGuard Home syntax (`||domain^`), used by the school networks to block games during lessons.

| List | Content | URL for AdGuard Home |
|---|---|---|
| `lists/ut1-games.txt` | game sites, including browser games | `https://raw.githubusercontent.com/egi95/dns-filtra-shkolla/main/lists/ut1-games.txt` |
| `lists/ut1-social_networks.txt` | social networks (not in use yet) | `https://raw.githubusercontent.com/egi95/dns-filtra-shkolla/main/lists/ut1-social_networks.txt` |

The workflow `.github/workflows/perditeso.yml` refreshes the lists every night from the UT1 categories. If a download is almost empty, the previous list is kept.

- **BGT 1 (MikroTik + AdGuard Home):** AdGuard downloads `lists/ut1-games.txt` itself every 24 h. A router script turns the list on only during lessons.
- **BGT 2 (UniFi):** UniFi cannot read a list URL. After the lists are refreshed, `scripts/unifi_sync.py` updates 4 Domain Lists ("BGT Lojera UT1 #1..#4", educational sites removed) and keeps 20 BLOCK policies, one per list and lesson block, Mon–Fri. It needs the repository secrets `UNIFI_API_KEY` and `UNIFI_CONSOLE`.

## Source and license
The domains come from the UT1 blacklists of Université Toulouse Capitole (https://dsi.ut-capitole.fr/blacklists/), through the mirror https://github.com/olbat/ut1-blacklists. They are published under **CC BY-SA 4.0**, and this conversion is shared under the same license.
