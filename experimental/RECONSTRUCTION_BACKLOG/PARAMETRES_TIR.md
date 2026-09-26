# Correspondance des paramètres de tir d'éditeur

Établie le **27 septembre 2026**, en lecture seule. L'outil original
`tools/item_shoot_projection.py` rapproche 18 colonnes de
`item_shoot.tbl` des octets du premier descripteur d'action, sélecteur 4.
Ce n'est ni une entrée Weapon, ni une allocation de slot, ni une preuve de
signification complète des paramètres de gameplay.

## Correspondances contrôlées

Offsets relatifs au payload de 128 octets, dont le lecteur natif déjà qualifié
copie les 88 premiers octets. Les colonnes sont les identifiants du schéma TBL,
pas leur rang dans le fichier.

| Colonne | Offset | Transformation observée |
|---:|---:|---|
| 2 | 76 | nom cp1252 terminé, dans huit octets |
| 3 | 36 | entier 32 bits |
| 4 | 8 | float32 |
| 6 | 12 | float32 |
| 8 | 16 | chaîne décimale → entier 32 bits |
| 10 | 40 | chaîne décimale → entier 32 bits |
| 12 | 24 | entier 32 bits |
| 24 | 44 | float32 × 1000, résultat float32 |
| 26 | 48 | float32 |
| 28 | 52 | float32 |
| 30 | 56 | float32 |
| 38 | 20 | float32 × 1000, résultat float32 |
| 40 | 60 | float32 |
| 42 | 64 | float32 × constante float32 0,01 |
| 46 | 84 | float32 |
| 58 | 28 | booléen sur un octet |
| 77 | 68 | entier 32 bits |
| 79 | 72 | entier 32 bits |

Les mots aux offsets 0, 4 et 32 valent respectivement 0, 3 et 0 dans les
40 témoins Base. Ils sont contrôlés comme **constantes observées**, pas reliés
arbitrairement à une colonne qui aurait la même valeur. Les colonnes
1, 81, 84, 86, 88, 92, 94 et 98 restent non reliées.

Les trois octets suivant le booléen, les octets après le premier zéro du nom
et les quarante octets finaux ne sont pas comparés comme données vivantes.
L'outil produit une projection **partielle** et ses empreintes, pas un record
complet rempli à partir de suppositions.

L'arrondi est significatif : pour la valeur float32 0,38, multiplier par la
constante float32 0,01 retrouve exactement les octets natifs. Utiliser le
nombre double 0,01 produit un écart d'un ULP. Un test synthétique verrouille
cette différence. Une conversion ×1000 ne suffit pas à qualifier son unité
physique, pas plus que ×0,01 ne prouve à elle seule une probabilité.

## Quatre couches, différences conservées

Les sources complètes sont verrouillées par taille et SHA-256 avant lecture.
Quarante armes du sélecteur 4 sont comparées dans chaque couche :
**160 contrôles, 154 concordances complètes et six fiches portant onze
différences de colonnes connues**.

| Couche | Concordances | Différences par slot |
|---|---:|---|
| Base | 40/40 | aucune |
| Patch | 40/40 | aucune |
| Sabre | 38/40 | 5 : colonne 24 ; 23 : colonne 28 |
| PatchX01 | 36/40 | mêmes écarts de 5/23 ; 26 : colonnes 6/26/28 ; 28 : colonnes 6/28/30/40 |

Ces écarts ne sont pas « corrigés ». Ils prouvent qu'on ne doit pas exporter
les valeurs d'éditeur Base par-dessus une table Sabre/PatchX01. Un écart
supplémentaire, un changement de type ou de sélecteur fait refuser l'audit.

## Armes orphelines

- **Benelli**, ligne 9 : 21 plages, 85 octets comparables sur 88.
  Projection SHA-256 `5126189a3af8c541b9a77f3dc0c4f65f53ab5570d890e30db5b65fa6e953017d`.
- **FG 42**, ligne 27 : 19 plages, 75 octets. Les colonnes 8 et 10 contiennent
  les symboles `FG42_F` et `FG42_R`, pas des chaînes décimales.
  Ils sont conservés comme **références non résolues**, jamais convertis en
  zéro, remplacés ou affectés à un numéro inventé.
- **MG 34**, ligne 32 : 21 plages, 83 octets.
  Projection SHA-256 `abbd1c7e753f9392292d98e0dbc993c2ff2e7faf35c9b18578b8637f7606bd6b`.

L'absence de symbole non résolu ne signifie pas que les références numériques
restantes sont toutes reliées à une ressource ou à une fonction sonore vérifiée.
Les noms de sons ne sont pas déduits de la seule position de ces champs.

Aucune fiche commerciale d'arme exploitable n'est créée pour ces trois lignes ;
les objets actuellement présents aux slots 9/27/32 restent intacts. Il manque
encore les autres données du descripteur, les consommateurs de paramètres,
la liaison complète des ressources et la voie additive sûre.

## Reproduction

```powershell
.\.venv\Scripts\python.exe tools/item_shoot_projection.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output .analysis/projection-tir-nouveau.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_item_shoot_projection.py
```

Le rapport privé contrôlé est `.analysis/item-shoot-projection-20260927.json`.
Les surcharges libres sont exclues et empreintées ; sans cette option elles
font refuser l'audit. Huit tests inventés, sans archive commerciale, couvrent
conversions, arrondis, masques, symboles, champs manquants et refus.
Ni jeu ni sauvegarde de partie ouverts.

