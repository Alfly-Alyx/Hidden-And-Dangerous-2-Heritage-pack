# Attachement natif des animations aux cibles

**27 septembre 2026.** Le nouveau banc exécute l'appel `SetAnimation` et ses
liaisons internes dans un modèle synthétique. Il dépasse les anciens contrôles
séparés de [recherche et descripteurs](LIAISON_ANIMATION_NATIVE.md), sans
prétendre charger une scène ni construire un personnage jouable.

## Ce qui est exécuté et ce qui est fourni

LS3DF est épinglé : 864 256 octets, SHA-256
`12c61eed2aec0c45700ad0a5ddfd7cbb3cbf0ea15ec67de155790bb24e7756ee`.
L'appel `0x100342f0`, le contrôleur `0x10020260`, la recherche et création
des propriétaires `0x10020740`, leur nettoyage `0x100206b0` et les accesseurs
de clip sont exécutés uniquement dans leurs blocs examinés.

Le modèle et son contrôleur sont **préalloués par le banc**. Les noms de
cibles proviennent du lecteur 4DS ; les blocs 5DS sont strictement relus,
puis leurs pointeurs relocalisés en mémoire par le banc, **pas par le chargeur
natif**. Les ressources commerciales et leurs clés ne sont pas exportées.

Les allocations de structures de cible de 244 octets et leurs libérations
sont des doubles Python bornés : 128 structures maximum, sites appelants et
tailles exacts exigés. Leur initialisation, réutilisation, insertion dans la
table et retrait sont natifs. Ni allocation du contrôleur, agrandissement de
table, destruction du clip de base, API Windows, entrée de bibliothèque,
événement, pose ou rendu ne sont autorisés.

Le domaine comprend neuf clips maximum, 128 cibles, huit emplacements et
32 opérations par séquence. Deux dispositions de conteneur sont vérifiées.
La tête SEH utilisée par l'appel est une page isolée, restaurée après chaque
opération, pas un environnement Windows. Code et écritures sont filtrés ;
limite de six millions d'instructions et vingt secondes par opération,
nécessaire au témoin de 128 noms longs presque identiques.

## Contrats établis

- Une animation non nulle active l'emplacement, remet son temps à zéro et
  son repère précédent à **−40** ; le dernier pas demeure inchangé.
- Un mode d'appel nul conserve le **mode par défaut du clip**. Un mode
  non nul le remplace. Le mode 2 fourni aux banques réelles est une condition
  synthétique explicite, pas une preuve de leur valeur après chargement.
- Le poids initial est copié sans plafonnement dans le domaine examiné
  [0,2]. C'est différent du réglage de poids séparé, qui borne à [0,1].
- Réaffecter le même clip au même emplacement redémarre ses temps et remet
  ses paramètres sans incrémenter à nouveau sa référence ni dupliquer les cibles.
- Partager un clip entre plusieurs emplacements ajoute une référence par
  emplacement. Le dernier retrait retrouve la référence de base détenue par
  le banc ; aucune destruction réelle du clip n'est nécessaire.
- Changer de clip efface les drapeaux des anciennes liaisons de cet
  emplacement. Les canaux du nouveau sont attachés par nom **exact, sensible
  à la casse** ; un doublon cible prend la première correspondance.
- Un nom absent n'empêche pas l'activation du clip, mais ne crée pas de cible.
- Une structure sans canal peut subsister tant qu'une piste quelconque du
  contrôleur reste active. Une fois toutes les pistes détachées, les structures
  devenues inutiles sont retirées et rendues au double d'allocation.
- Détacher un emplacement déjà vide ne réinitialise pas arbitrairement ses
  anciens temps, son poids ou le drapeau de recalcul.

Les pointeurs et comptes des canaux position/rotation/échelle, leurs drapeaux,
les références, les états des huit pistes et les tables de propriétaires sont
comparés après **chaque opération**, y compris lorsque plusieurs clips se
chevauchent. Les données d'entrée et champs hors périmètre restent inchangés.

## Résultats privés

`native-animation-attachment-20260927.json` :

| Corpus | Séquences | Opérations | Créations / libérations de cibles |
|---|---:|---:|---:|
| Données inventées | 44 | 304 | 308 / 308 |
| Mains Benelli normales + arme | 146 | 466 | 3 674 / 3 674 |
| Seconde variante de mains + arme | 146 | 466 | 3 674 / 3 674 |
| FG42 moderne | 146 | 466 | 438 / 438 |
| MG34 moderne | 146 | 466 | 584 / 584 |

Chaque banque comprend neuf clips, les huit emplacements dans deux types
de conteneurs, les redémarrages et une séquence de chevauchement/remplacement.
Les 1 864 opérations des banques concordent. Quinze tests nouveaux utilisent
uniquement des états et animations inventés.

```powershell
.\.venv\Scripts\python.exe tools/animation_attach_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/attachement-nouveau.json'
```

Rapport neuf obligatoire. **Chargement effectif, pose appliquée après cette
liaison, héritage en situation réelle, événements, caméra, scène et jouabilité
restent à qualifier.** Les bancs de pose/peau antérieurs restent des preuves
distinctes, pas un appel complet au moteur chargé.
