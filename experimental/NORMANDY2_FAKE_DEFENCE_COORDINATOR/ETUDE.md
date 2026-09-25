# Normandy 2 — coordinateur de défense retiré

État : chaîne incompatible, audit reproductible, 26 septembre 2026. Aucun
propriétaire, binding ou signal ajouté; version commerciale inchangée.

## Le fichier ne forme pas une chaîne complète

`R_N2_fake_defence_sender.scr` existe dans Scripts.dta (5998 octets,
SHA-256 `d552ff5a5c657bc1cd15a6f673e8f85ab0191a3b282a5b589abef7b9438d66cd`).
Il n'est ni lié ni atteint par les dépendances littérales des scripts actifs.
Le graphe commercial compte 159 liaisons, 135 scripts racines, 142 accessibles
et 175 disponibles, sans fichier manquant dans cette fermeture statique.

Le coordinateur conserve 21 tests de proximité `<4` : quinze Blue et six Wave.
Six autres tests correspondent à Blue12/16 et Wave1_2/4, Wave2_4/5 retirés et
restent commentés. Les tests sont initialement désactivés, puis armés par
`OnSignal(1)`. Le commentaire évoque Waves, mais le contrôleur commercial
`R_N2_Waves` ne recherche ni ne contacte ce coordinateur. Le centre des rayons
dépendrait de son propriétaire : un dummy arbitraire ne serait pas neutre.

La cible est placée dans `kdo`, écrite en valeur de jeu 25, puis un allié 1..5
est choisi aléatoirement et reçoit **signal 25**. Ce protocole n'est pas celui
des récepteurs conservés :

| Script de fin accessible | Réponse littérale au signal 25 |
|---|---|
| `R_N2_Ally1_End`, `Ally2_End`, `Ally3_End` | cible fixe `Wave1_5` |
| `R_N2_Ally4_End` | cible fixe `Blue_17` |
| `R_N2_Ally5_End` | aucun gestionnaire 25 |

Aucun de ces cinq scripts ne lit la valeur de jeu 25. Ils sont atteints par
affectation dynamique, pas directement liés dans le registre initial. Leur
accessibilité ne garantit pas qu'ils soient affectés au moment d'un signal.
`R_N2_OnFire_B17` contient déjà une émission 25 vers Ally4 : ce numéro ne doit
pas être redéfini globalement pour le nouveau coordinateur.

## Décision de reconstruction

La description initiale « script complet sans propriétaire » était insuffisante.
Il manque aussi le contrat de réception, le raccord d'activation et le placement.
Un verrou anti-répétition seul ne répare pas cette incompatibilité. Aucun delta
exécutable n'est produit pour cette chaîne.

Une variante MODERNE devra définir un propriétaire spatial justifié, une liste
de couples allié/cible vivants, une seule transaction en cours, une cadence
bornée et une annulation sur mort/fin/alarme. Le choix de cible doit rester
cohérent jusqu'à réception; une valeur globale partagée sans acquittement ne
garantit pas cela. Les scripts de fin et leurs signaux actuels restent le témoin.
Ne pas mélanger cette reconstruction avec le réseau de déplacement
[Go](../NORMANDY2_LEGACY_GO_NETWORK/ETUDE.md) ou l'ajout des
[quinze acteurs](../NORMANDY2_REMOVED_DEFENDERS/ETUDE.md).

## Vérification relançable

```powershell
.\.venv\Scripts\python.exe tools\audit_normandy2_vestiges.py --game "D:\Games\Hidden and Dangerous 2" --archives-only
```

L'[audit](../../tools/audit_normandy2_vestiges.py) lit et empreinte 179 sources,
sans en écrire aucune. Il distingue gestionnaire absent, cible fixe et corps
imbriqué non interprété. Huit tests synthétiques couvrent ce contrat, les
dépendances et les mouvements. Le mode strict refuse les surcharges installées;
le mode archives les exclut explicitement et consigne leurs empreintes : quinze
Blue, objectifs et Red26, soit 17 fichiers, laissés intacts.

Récepteurs 1/2/3/4 : SHA-256 respectifs
`d2bd58c3a84902ac40f35d556c2daeaf307431490effc3c7cdf8225d72e9e3ea`,
`1f27778dbd23eeb0d6dcd87ac13711d9878e67ea58d9490833cb893a1c17d8d4`,
`633d9b8ac35cff0f6db76eba7364549378453f23f7808fabb5f1e78189a70b87`,
`96e928ed06e3a20c0b7e216ef71aacd81987a58e287159dec0d2fb14bf713558`.
Le rapport complet donne les autres empreintes. État moteur : **pending**.
