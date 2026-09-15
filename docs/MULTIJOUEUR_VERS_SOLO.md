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