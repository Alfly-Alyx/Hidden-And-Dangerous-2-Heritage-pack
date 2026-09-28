# MG34 portative — descripteur moderne et tables privées désactivées

**27 septembre 2026.** `tools/build_mg34_descriptor_lab.py` construit maintenant
une fiche Weapon complète de 508 octets et, sur demande explicite, une paire
de tables complètes réversibles. **Ce n'est pas une arme jouable ni un installateur.**

## Provenance séparée

La ligne historique **32, « MG 34 »**, du catalogue de tir est projetée dans
l'action primaire. Son SHA-256 est
`d577c7866fa84d9deb9f69765657d87f51278852e3d4fbfb9c09f0f9869abbb2`.
Le slot natif 32, réutilisé par un casque, reste intact. La munition portative
**201, « AMMO MG 34 »**, est reliée explicitement ; ni la munition 211 ni
l'objet TANK MG34 ne sont utilisés comme donneurs ou remplacés.

La fiche générale manquante n'est pas annoncée comme retrouvée. Le poids
`11.57699966430664`, les membres de catégorie et l'action secondaire proviennent
d'un **choix de conception moderne** : attributs individuels de la MG42 Sabre,
slot 33, empreinte `f3f34fd2d68efb6caa515fb65007a2c9e84ec1837056a67c68bef6627c66e1fe`.
L'action secondaire conserve les constantes `(0, 4, 5)` et le scalaire
`1.0471975803375244`. Cela ne qualifie ni le poids historique de la MG34, ni
son équilibrage, ni la signification complète de ces membres. Aucun record
donneur entier n'est copié ; les octets non documentés sont remis à zéro selon
une politique moderne explicite. Le nom interne est `MODERN_MG34`.

Le modèle extérieur moderne original reste inchangé (260 160 octets,
SHA-256 `d45597f0c720991a468fe8064c5ee972efeb884dc1be6acef45bb06dfc924dac`).
Le modèle FPV moderne reçoit l'alias **`PROTOTYPE_MG3FPV`** : l'ancien nom
descriptif du laboratoire dépassait la limite Item de 19 caractères. Seul le
nom de fichier est raccourci ; géométrie et noms des cibles d'animation ne
changent pas. Les animations de mains dérivées restent privées.

## Ressources historiques contrôlées en mémoire

| Référence | Source effective | Taille | SHA-256 |
|---|---|---:|---|
| Icône `wi_ge-mg34.bmp` | Maps.dta | 3128 | `9d101281f23e575eabd0a903812dced69bf20ed1cc46a1575bb1b38bef7276ef` |
| Tir `f_mg34_a.wav` | Sounds.dta | 48238 | `ca56fb3a2aac19aa5c0fa07d6f8cd3a7a05b51658990f686a4b6ddd048675500` |
| Recharge `mg34_r.wav` | Sounds.dta | 152876 | `121188b694db91d829a84fd57ad0290b6a3ad812912c99a49362555bc71a7c25` |

La définition sonore effective Patch est épinglée à
`ab374c805b6bc663593bfd788f9e437b6998ffe8a3d02e83a393aa201dfd94f3`.
Les indices **banque 2/entrée 34** et **banque 3/entrée 38** sont résolus puis
vérifiés dans les blocs natifs d'arguments. Les deux WAV sont lus intégralement
en mémoire : PCM mono 16 bits, 22 050 Hz, respectivement 24 097 et 76 416
échantillons (1,092834467 s et 3,465578231 s). Pas d'écoute, d'export audio,
de lecture moteur ni de synchronisation validée.

Le catalogue moderne ajoute **21501 : MG 34 [MODERNE]**, décliné dans les huit
langues avec le même marqueur localisé que le Benelli. Quinze tables de textes,
les quatre couches d'objets et la table personnelle sont examinées contre les
collisions. Les anciens octets sont conservés ; les ajouts restent désactivés.

## Descripteurs et associations construits

Les dossiers privés `MG34H_Descriptor_v1` et `MG34R_Descriptor_v1`, dans
`.analysis/item-descriptor-labs`, comportent **22 fichiers chacun** :
descripteur, modèle extérieur, modèle FPV, neuf animations, fragment FPV,
huit textes et manifeste. Sons, icône et modèles commerciaux de mains ne
sont pas exportés. Les variantes H/R sont mutuellement exclusives.

Le descripteur commun avec texte a pour SHA-256
`d911d4235e698d0dac8b0f14325bba73a62fb11ce3783fdea47101d1b3d90a41`.
Le lecteur natif isolé le relit ; la munition 201 initialise **75** unités dans
chacune des couches Sabre/PatchX01. Les **13 liaisons slot 363 → groupe 463**,
**39 demandes de ressources et 9 chargements de clips par variante** concordent.
Les positions 363/463 ne sont que des candidats de laboratoire, pas des
réservations globales. Cette première construction utilise les mains **v4**,
dont les défauts entre clés sont documentés dans [l'audit des mains](../RECONSTRUCTION_BACKLOG/MAINS_ARMES_RIGIDES.md).

## Tables complètes et surcharges préservées

Quatre dossiers privés `MG34{H|R}_Tables_{SabreSquadron|PatchX01}_v1`, sous
`.analysis/item-table-labs`, contiennent **25 fichiers chacun**. Un cinquième,
`MG34H_Tables_Current_v1`, compose l'ajout sur les deux tables personnelles
lues comme instantané, sans jamais les réécrire.

Chaque construction conserve **272 objets et 277 groupes existants**, ajoute
l'objet 363 et son groupe 463, puis vérifie le retrait exact. Les tables finales
ont 273 objets présents et 278 groupes. Le parcours natif visite les **500
emplacements** ; les 273 descripteurs, le parcours FPV et 39 demandes de ressources
sont vérifiés dans chaque laboratoire. La réserve d'objets diminue de 504 octets,
mais la taille totale reste 252 000 octets.

| Table désactivée | SHA-256 |
|---|---|
| Objets Sabre, H/R | `ad4e6a76c8a527f50cae4a907b5ca56a44cd320aed39db7175e8d96774e85166` |
| Objets PatchX01, H/R | `c6b96bad4064a0a67ab54866aa581a4fc3077104f853a09ea53040a80a24261a` |
| FPV H, 127 992 octets | `40a20e097db4cd134831aa07389751d66b8e410fe356be987480ad20231a7f8b` |
| FPV R, 127 992 octets | `7b661f8c99a047a87377621b8c893ae2301cf63f31ec1d6a3717bad586b25ccc` |
| Objets sur instantané personnel | `89f9c39153d36d59b9aa1f085ae2264c46a440f2e241d71e4f8ec4d69b2f2b68` |
| FPV H sur instantané personnel, 128 559 octets | `c5f753ad8966bcc3d3c33747a66c411dbf513e8c5fd30307536b91a24a5a4cdb` |

L'instantané personnel comporte dix objets et six groupes différents des
archives choisies : **toutes ces différences sont préservées**, sans changer
l'ordre des groupes. Une modification de la munition référencée, un emplacement
occupé, un libellé déjà utilisé ou une source modifiée sont refusés. Le retrait
refuse une paire altérée ultérieurement. Ce contrôle n'est pas un déploiement
atomique sur disque, une migration de sauvegarde ou une permission d'installation.

## Reproduction et réalisations restantes

**Actualisation du 28 septembre 2026 :** le profil par défaut de ce constructeur
est désormais `modern-rigid-hand-grips-mg34-linear.json`, utilisé avec la banque
privée **MG34_HandFPV_v10**. La correction Arm/Disarm supprime les 36 dépassements
bruts entre clés de v7 ; 1 010 poses de surface, zéro traversée et aucune pièce
omise. Les mélanges de clips gardent des écarts distincts, documentés dans
[l'audit des mains](../RECONSTRUCTION_BACKLOG/MAINS_ARMES_RIGIDES.md).

Trois nouveaux laboratoires, `MG34_Tables_PatchX_H_v2`, `MG34_Tables_Sabre_R_v2`
et `MG34_Tables_Current_H_v2`, ont été construits et contrôlés : **25 fichiers,
273 descripteurs, 39 demandes de ressources et 9 lectures d'animations chacun**.
Le retrait exact est vérifié ; les anciennes données et les surcharges personnelles
sont conservées. Le catalogue de textes commun contient maintenant les cinq
libellés 21500–21504 ; cela n'ajoute pas les autres armes aux tables MG34.
Les laboratoires v1 ne sont pas écrasés ni présentés comme corrigés.

```powershell
.\.venv\Scripts\python.exe tools/build_mg34_descriptor_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --hand H --bank .analysis/modern-assets/MG34_HandFPV_v10 --inventory-texts --item-layer PatchX01.dta --preserve-central-overrides --output-name MG34_Tables_Neuves
```

Les archives, mains et dépendances d'émulation sont locales et privées. Le
dossier de sortie doit être neuf. Enlever les options de couche et de surcharges
limite la sortie au descripteur et à ses ressources désactivées.

Seize tests synthétiques couvrent descripteur, provenance, ressources, longueur
des noms, textes, quatre variantes de tables, collisions, surcharges, parcours
et retrait. Restent notamment : contacts/gestes des mains, raccordement du
correcteur au client, chargement/copie des modèles en scène, caméra, événements
de tir/recharge, choix et équilibrage des paramètres non qualifiés, animations
de personnage, IA, sauvegardes complètes, réseau, compatibilité des autres
surcharges et déploiement isolé. **Ne pas copier ces fichiers dans le jeu.**
