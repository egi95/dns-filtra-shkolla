# Orari i ndryshimeve në UniFi

Listat mund të ndërtohen dhe publikohen në GitHub gjatë gjithë ditës. Sinkronizimi automatik që ndryshon konfigurimin e UniFi fillon vetëm nga ora 00:00 deri para orës 07:00, sipas zonës `Europe/Belgrade`, përfshirë ndryshimin verë/dimër. Nëse GitHub e nis punën me vonesë, skripti shënon `SKIP UniFi` dhe i ruan listat e publikuara për sinkronizimin e radhës.

Për një ndërhyrje manuale të miratuar, te **Actions → Perditeso listat → Run workflow** mund të zgjidhet `allow_daytime_sync`. Nga terminali përdoret `python3 scripts/unifi_sync.py --allow-daytime`, me kredencialet ekzistuese në mjedis. Ky përjashtim zbatohet vetëm për atë ekzekutim. Komandat e zakonshme `bgt-modi` për lejim dhe bllokim sipas orarit nuk ndryshojnë.

Listat e mëdha u dyshuan më herët për vonesën e rregullave. Auditimi i 14 nëntorit dalloi kohën e ngjarjes nga koha e regjistrimit të saj, dhe prova e veçuar e një politike u zbatua brenda pak sekondash. Prandaj madhësia e listës nuk trajtohet si shkak i provuar i vonesës. Lista e lojërave në UniFi mbetet e vogël; kapaciteti real duhet matur gjatë mësimit.
