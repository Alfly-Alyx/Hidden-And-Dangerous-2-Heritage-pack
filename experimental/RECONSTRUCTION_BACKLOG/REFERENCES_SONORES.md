# Références sonores des actions de tir

**27 septembre 2026.** Les colonnes 8 et 10 de `item_shoot.tbl` sont maintenant
reliées à des indices de banques sonores, au-delà de leur seule correspondance
binaire avec le descripteur. Les outils originaux `sound_definition.py`,
`item_sound_oracle.py` et `item_sound_audit.py` conservent trois preuves séparées :
structure de fichier, passage des arguments natifs et recherche d'indices sur
des banques synthétiques. **Aucune restitution audio ni opération de jeu complète.**

## Lecteur strict des définitions

La source effective contrôlée est `Patch.dta::Tables/IngameSounds.def`,
104700 octets, SHA-256
`ab374c805b6bc663593bfd788f9e437b6998ffe8a3d02e83a393aa201dfd94f3`.

Elle contient **14 banques, 539 entrées et 672 variantes**. Les **148 entrées
sans variante** restent présentes dans l'index ; les supprimer décalerait les
références suivantes. Les banques vides restent également en place.

La racine 1000 contient les banques 1100. Leur libellé 1110 précède les entrées
1200, elles-mêmes composées d'un libellé 1210, d'un drapeau 1310 sur un octet et
de zéro ou plusieurs variantes 1300. Chaque variante conserve le nom 1400 et
six paramètres 32 bits **bruts**, sans inventer leurs unités ou leur rôle.

La dernière section 1050, 3581 paires de mots, est conservée comme **table de
recherche opaque** ; elle n'est ni une quinzième banque ni une preuve de
résolution des symboles FG42. Les noms et les tailles sont strictement bornés.

## Contrat natif borné

Les blocs lus puis exécutés dans l'émulateur verrouillé montrent :

- Tir : `0x7d610b…0x7d6132`, getter `0x7e06f0`. Le membre d'action 0x14
  (payload +16, colonne 8) devient l'indice passé avec la **banque 2**.
- Rechargement : `0x7d50d5…0x7d5103`, getter `0x7e07f0`. Le membre 0x2c
  (payload +40, colonne 10) devient l'indice associé à la **banque 3**.
- L'insertion des banques à `0x4392d5` et des entrées à `0x43226e` conserve
  l'ordre du fichier. Douze cas synthétiques vérifient l'ajout et l'incrément.
- La table virtuelle finale du gestionnaire est `0x80f7b8`, sa méthode +0x8c
  est `0x4326d0`. La recherche indexe d'abord les banques, puis les entrées,
  avec contrôles des bornes. Neuf cas synthétiques couvrent références valides,
  banques/entrées vides, débordement d'indice et sentinelles `0xffffffff`.

Le banc vérifie **168 fiches commerciales** : 40 Base, 40 Patch, 44 Sabre,
44 PatchX01. Il compare leurs indices à **une seule définition sonore effective
verrouillée**, pas à une reconstruction de toutes les versions linguistiques.
Le descripteur moderne Benelli est contrôlé en supplément, avec l'argument
synthétique 359. Le chargeur de fichier complet, les variantes aléatoires,
les appels audio et les opérations complètes de tir/rechargement ne sont pas
exécutés. Les quelques mots globaux écrits dans la mémoire émulée sont restaurés.

## Associations obtenues

| Arme / action | Banque | Indice | Définition | Fichier référencé |
|---|---:|---:|---|---|
| Benelli / tir | 2 | 36 | I Benelli M4 | f_bene_a.wav |
| Benelli / rechargement | 3 | 54 | I Benelli M4 Reload | bene_r.wav |
| MG34 / tir | 2 | 34 | G MG34 | f_mg34_a.wav |
| MG34 / rechargement | 3 | 38 | G MG34 Reload | mg34_r.wav |

Les deux WAV Benelli sont déjà verrouillés et mesurés par le banc FPV privé.
Pour MG34, ce lot établit la **référence de fichier**, pas encore l'audit PCM
de ces WAV. FG42 conserve les deux symboles **FG42_F / FG42_R**, explicitement
non résolus. Ils ne sont ni remplacés par zéro ni affectés au son d'une autre arme.

Compléments ultérieurs distincts : le [laboratoire MG34 portable](../MG34_PORTABLE/DESCRIPTEUR_ET_TABLES.md)
contrôle désormais ses WAV PCM et leur liaison au descripteur ; les
[sons FG42/ZK-383 modernes](SONS_MODERNES.md) sont entièrement synthétisés sous
de nouveaux alias. Leur ajout numérique réversible ne résout toujours pas
les deux anciens symboles FG42 et n'emprunte aucun échantillon d'une autre arme.

## Raccordement et limites

`BenelliDescriptor_v2` reconstruit le laboratoire avec ces associations dans son
manifeste. Les quatre fichiers binaires restent **identiques octet par octet**
à v1. La construction refuse désormais une définition sonore différente ou
une ressource Benelli manquante. L'audit des arguments natifs reste un contrôle
séparé, explicitement annoncé comme tel dans le manifeste du constructeur.

Il reste à qualifier les autres paramètres de tir, la synchronisation et les
événements audio/FPV, puis les effets réellement observés en jeu. Une référence
valide ne prouve pas qu'un son est joué au bon moment, ni même joué dans toutes
les branches de comportement. Aucun nouveau son n'est créé ou exporté ici.

```powershell
.\.venv\Scripts\python.exe tools/item_sound_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output .analysis/references-sonores-nouveau.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_sound_definition.py
```

Rapport privé final : `.analysis/item-sound-references-v2-20260927.json`.
Neuf tests synthétiques couvrent le format, ses refus, les ordres, les bornes,
les sentinelles et les symboles. Un dixième contrôle supplémentaire protège
le constructeur Benelli contre un raccordement sonore modifié.
