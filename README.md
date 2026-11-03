# dns-filtra-shkolla

DNS block lists in AdGuard Home syntax (`||domain^`), used by the school networks to block games during lessons.

Every UT1 category is available as `lists/ut1-<category>.txt`. The full table with sizes and AdGuard URLs is in [`lists/README.md`](lists/README.md). "adult" is left out: its 4.6M domains are too big for GitHub and for the routers.

In use today: `lists/ut1-games.txt` (games, during lessons, in both schools).

The workflow `.github/workflows/perditeso.yml` refreshes all lists every night. If a download is empty or suddenly drops below half of yesterday's size, the previous list is kept.

- **BGT 1 (MikroTik + AdGuard Home):** AdGuard downloads `lists/ut1-games.txt` itself every 24 h. A router script turns the list on only during lessons.
- **BGT 2 (UniFi):** UniFi cannot read a list URL. After the lists are refreshed, `scripts/unifi_sync.py` updates 4 Domain Lists ("BGT Lojera UT1 #1..#4", educational sites removed) and keeps 20 BLOCK policies, one per list and lesson block, Mon–Fri. It needs the repository secrets `UNIFI_API_KEY` and `UNIFI_CONSOLE`.

## Source and license
The domains come from the UT1 blacklists of Université Toulouse Capitole (https://dsi.ut-capitole.fr/blacklists/), through the mirror https://github.com/olbat/ut1-blacklists. They are published under **CC BY-SA 4.0**, and this conversion is shared under the same license.
