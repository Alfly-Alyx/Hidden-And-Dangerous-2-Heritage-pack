# Suivi des cartes multijoueur vers le solo

Date de travail : 14 septembre 2026.

## Règle de classement

Une carte n’est comptée comme mission solo que si elle possède un point de départ utilisable, un contrôleur de mission, au moins un objectif ou une fin de mission vérifiable, les acteurs nécessaires et un lancement confirmé depuis le menu solo. Une simple entrée de catalogue, une carte libre ou une partie locale multijoueur n’est pas présentée comme une mission solo.

La version multijoueur commerciale reste toujours intacte. Toute conversion est installée sous un autre dossier et porte le préfixe `Prototype`, `Reconstruction` ou `Alternative` selon son niveau de fidélité.

## État actuel

- 47 dossiers sont déclarés dans le catalogue multijoueur commercial.
- 33 missions solo commerciales sont présentes.
- Aucune conversion d’une carte exclusivement multijoueur en mission solo n’est encore validée en jeu.
- `Normandy3_MP_ZONE` et `AFRIKA5_MP` sont actuellement traitées comme prototypes multijoueur ; elles ne doivent plus être annoncées comme missions solo tant qu’un script solo réellement lançable n’a pas été construit et testé.
- Les missions du Community Map Package restent coopératives tant qu’une conversion solo distincte n’a pas franchi les mêmes contrôles.

## Contrôle reproductible

`tools/multiplayer_solo_readiness_audit.py` applique désormais le même garde-fou à chaque carte. Il vérifie séparément : l'entrée de catalogue solo, les quatre fichiers de carte, les données d'acteurs et de navigation, le registre de scripts, les scripts réellement reliés et une logique d'objectif active. Il ne valide ensuite une conversion que si `validation/multiplayer-solo-runtime.json` atteste quatre essais en jeu : ouverture depuis le menu solo, apparition du joueur, fonctionnement des objectifs et fin de mission.

Ce registre contient maintenant explicitement les 21 candidates officielles,
toutes initialisées à `pending` avec leurs quatre preuves à `false`. Une carte
ne peut donc plus disparaître du suivi ni être validée par omission.

Le contrôle est étalonné sur les 33 missions solo commerciales : **33/33 franchissent le contrôle statique**. Sur l'installation de travail actuelle, il distingue 47 dossiers multijoueur commerciaux et 195 dossiers déclarés après ajout du Community Map Package. Parmi eux, 21 cartes officielles et 69 cartes communautaires possèdent assez de composants statiques pour mériter une étude d'adaptation ; ce ne sont pas encore 90 conversions. **Aucune conversion multijoueur vers solo n'a reçu les quatre validations en jeu.**

Les 21 candidats officiels sont les douze variantes Objectifs `AFRICA1_OBJ`, `AFRICA3_OBJ`, `AFRICA4_OBJ`, `ALPS3_OBJ`, `ARCTIC1_OBJ`, `ARCTIC3_OBJ`, `ARDENS1_OBJ`, `BURMA1_OBJ`, `BURMA2_OBJ`, `CZECH1_OBJ`, `CZECH2_OBJ` et `CZECH3_OBJ`, ainsi que les neuf missions coopératives `CO_BREST`, `CO_BURGUNDY1`, `CO_BURGUNDY2`, `CO_BURGUNDY3`, `CO_LIBYE1`, `CO_LIBYE2`, `CO_LIBYE3`, `CO_SICILY1` et `CO_SICILY2`. Leur contrôleur multijoueur et leurs objectifs constituent une base de reconstruction, mais ne prouvent ni une équipe solo correcte, ni une IA compatible, ni une sortie de mission solo.

Les 26 autres cartes officielles exigent davantage de reconstruction : treize variantes libres n'ont aucun registre propre, et les autres registres ne pilotent aucune logique d'objectif solo complète. Les dépendances commerciales orphelines sont conservées comme avertissements ; elles ne font pas échouer à tort le référentiel, car plusieurs missions solo publiées en contiennent elles aussi.

Commande de vérification :

```powershell
python tools/multiplayer_solo_readiness_audit.py "D:\Games\Hidden and Dangerous 2" --runtime-results validation/multiplayer-solo-runtime.json --require-baseline
```

## Lieux commerciaux sans mission solo homonyme

| Lieu | Dossiers multijoueur | Mode officiel | Données conservées | Travail solo |
|---|---|---|---|---|
| Poland / vestige London | `london_mp` | Deathmatch | carte publiée sous le nom Poland, sans registre de mission ; ne pas confondre avec la campagne London coupée | confié à la reconstruction |
| Alps3 | `alps3_mp_zone`, `alps3_obj` | Teamplay, Objectifs | deux cartes complètes ; la variante Objectifs Sabre est active, le prototype Base à trois véhicules est incomplet | wrapper solo et variante Legacy confiés |
| Ardennes1 | `ardens1_obj` | Objectifs | carte Sabre complète ; scène Base inachevée avec un Sherman et un Tiger supplémentaires | wrapper solo et roster Legacy confiés |
| Ardennes2 | `ardens2_mp_zone` | Teamplay | géométrie et acteurs multijoueur, aucun registre de mission | reconstruction solo confiée |
| Normandy2B | `normandy2b_mp_zone` | Teamplay | variante complète sans registre de mission | reconstruction solo confiée |
| Normandy3 | `normandy3_mp`, vestige `normandy3_mp_zone` | Deathmatch ; variante Zone non publiée | carte Deathmatch complète sans registre ; seconde variante de carte non publiée | reconstruction solo confiée ; prototypes conservés en multijoueur |
| Normandy4 | `normandy4_mp_zone` | Teamplay | géométrie et acteurs multijoueur, aucun registre de mission | reconstruction solo confiée |

## Variantes multijoueur d’un lieu déjà présent en solo

Les 39 autres dossiers du catalogue reprennent une famille Africa, Arctic, Alps1, Burma, Burgundy, Czech, Libya, Normandy, Brest ou Sicily déjà représentée en solo. Cela ne signifie pas que leur variante Deathmatch, Teamplay, Objectifs ou Coopération possède un script solo : chaque transplantation doit encore comparer la géométrie, les acteurs, les chemins, les objectifs et la fin de mission à son parent solo.

Ces variantes seront classées séparément comme : réutilisation fidèle du contrôleur solo, adaptation officielle coop vers solo, reconstruction partielle ou exploration seulement.

## Bilan à joindre à l’exécutable final

Le bilan final donnera, pour chaque carte : son mode d’origine, le nom de sa nouvelle entrée solo éventuelle, le script utilisé, les objectifs disponibles, le niveau de création moderne, le résultat du test de lancement et la conservation de l’entrée multijoueur originale.
