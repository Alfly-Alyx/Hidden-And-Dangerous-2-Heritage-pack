# Li-2 — banc décoratif sans liaison aux ambiances

État : **modèle présent, aucune instance commerciale exacte**, 15 septembre
2026. Aucun script `Li2_SND_*` n'est rattaché au modèle.

`la_Li2.4ds` et son LOD sont conservés ; le principal contient 89 nœuds avec
deux moteurs/hélices, roues, gouvernes, cinq sièges et une caméra FPV. Ces nœuds
ne prouvent aucun siège utilisable ni modèle de vol.

Les quatre scripts Libye2/Co_Libye2 nommés `Li2_SND_bum`, `sup`, `sutr1` et
`sutr2` activent aléatoirement des frames sonores `S_bum*`, `S_sup*` et
`S_sutr*`. Ils ne recherchent ni `la_Li2` ni un acteur avion et ne le pilotent
pas. Le banc reste silencieux jusqu'à preuve d'une liaison distincte.

`TEST_LOCAL_LI2_DECOR` vérifie modèle, LOD, textures, échelle, collision et
sauvegarde. Le profil MP suit seulement après succès local. Tout pilotage,
équipage, son moteur, dégâts et réseau est moderne.
