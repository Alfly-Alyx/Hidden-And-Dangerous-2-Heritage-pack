# Associations modernes et lecture native des animations

**27 septembre 2026.** Les 36 clips du [montage FPV aplati](MONTAGE_FPV_MODERNE.md)
sont maintenant associés à treize états par variante et relus par la routine
d'origine, dans un émulateur mémoire borné. Aucun jeu ni installateur lancé.

## Quatre laboratoires exclusifs

`build_equipment_fpv_resource_lab.py` construit séparément F35 et No. 2 pour
chacune des deux variantes commerciales de mains H/R. Chaque dossier contient
un modèle moderne, neuf clips privés dérivés, un fragment de groupe FPV et son
manifeste, soit **12 fichiers**, tous les binaires étant `.disabled`.

Le choix moderne des états suit les neuf noms de présentation déjà employés :
Idle1 pour 2000/2001, Shot pour 2002/2003, AimShot pour 2004/2005, Rel pour 2006,
Jammed pour 2007, Arm pour 2008, Disarm pour 2009/2010, Aim pour 2011 et Daim
pour 2012. Un seuil 100 sur le premier canal rend la sélection déterministe ;
les trois autres canaux restent vides. Aucun événement sonore ou de dégâts
n'est créé par cette table.

Les arguments de laboratoire **360/361**, groupes **460/461**, sont des choix
synthétiques, pas des numéros historiques ni des réservations globales. Le
constructeur vérifie les slots vides dans Sabre/PatchX01 et les groupes absents
dans la table FPV Sabre verrouillée. Il ne fusionne ni surcharges, ni tables
centrales, ni sauvegardes. Les variantes H/R partagent le même groupe : elles
doivent rester exclusives et correspondre aux mains effectivement chargées.

Le parcours natif du fragment et **156 demandes** (13 états × 3 tirages ×
4 variantes) sont vérifiés. Les noms demandés correspondent exactement aux
alias des fichiers émis, sans récupération silencieuse d'une animation officielle.

## Lecture réelle de la routine d'animation, sans accès système

`ls3d_animation_load_oracle.py` exécute `I3D_animation_set::Open` à
`0x10004ce0`, la résolution de chemin `0x1005d5b0` et le lecteur `0x1005e580`.
La DLL n'est jamais chargée par Windows ; son empreinte est verrouillée.

- Le suffixe `.I3D` est remplacé par `.5ds` par les instructions natives.
  Aucun modèle compagnon `.4ds` n'est nécessaire à ce chemin d'animation.
- Signature, version 122, métadonnées et taille sont lus dans leur ordre natif,
  en cinq lectures, puis le fichier mémoire est fermé.
- Les pointeurs de noms et de pistes sont relocalisés par le lecteur natif,
  et non préparés par Python. Chaque octet obtenu est comparé au résultat attendu.
- Le nom de base mémorisé, l'intégrité des autres champs et le retour de succès
  sont contrôlés ; les **36 animations** passent cette lecture complète bornée.

L'ouverture/lecture/fermeture du fichier, les allocations et un callback de
service du pilote sont des **doubles mémoire explicitement limités**. Aucun
pilote, accès disque natif, API Windows ou fonction de rendu n'est appelé.
Seuls des objets frais et des clips de transformations prévalidés sont acceptés ;
les notes/événements, vieux buffers et chemins arbitraires sont refusés.

Six tests synthétiques supplémentaires couvrent chemins, refus de fichiers,
treize états, ordre des canaux, tirages 0–100 et exclusivité des variantes.

## Reproduction privée

```powershell
.\.venv\Scripts\python.exe tools/build_equipment_fpv_resource_lab.py --case F35 --hand H --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name F35H_FPVResources_nouveau
```

Les quatre dossiers actuels sont `F35H_FPVResources_v1`, `F35R_FPVResources_v1`,
`F2H_FPVResources_v1` et `F2R_FPVResources_v1`, sous `.analysis/modern-assets/`.
Leurs manifestes conservent empreintes, demandes et lectures individuelles.

## Ce que ce raccordement ne termine pas

La lecture de l'animation n'est pas le chargement/copie de la scène FPV.
Le contrôleur de poses dense utilise encore sa propre mémoire de clips ; cette
étape ne prétend pas exécuter chargement, attachement et rendu dans une seule
instance. Les [remplacements pendant la lecture](../RECONSTRUCTION_BACKLOG/ENCHAINEMENT_ANIMATIONS_NATIF.md)
sont contrôlés séparément, sans encore qualifier leur continuité visuelle.
Descripteur d'arme, choix réel des mains, transitions visuelles, caméra, sons,
carburant, jet, dégâts, IA, sauvegarde et réseau restent à réaliser ou qualifier.
Les ressources sont prêtes pour la suite de l'intégration, pas pour installation.
