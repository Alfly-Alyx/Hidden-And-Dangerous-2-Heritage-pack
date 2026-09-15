# Matrice — cartes multijoueur vers variantes solo

État : **dix fiches et dix wrappers de conception**, 14 septembre 2026. Aucun
wrapper n'est déclaré jouable, aucun catalogue n'est modifié et aucun fichier
commercial n'est copié dans le dépôt.

## Règle

Chaque sous-dossier nomme une future entrée solo distincte et sépare :

1. **ORIGINE** — données commerciales réemployées sans changement ;
2. **DÉDUCTION** — raccord logique reconstruit à partir de la carte ou d'une
   mission apparentée ;
3. **CRÉATION** — objectif, acteur, placement, texte ou fin inventé faute de
   donnée.

Un dossier et une fiche constituent ici la préparation du wrapper. La mention
`BLOQUÉ` signifie qu'aucun registre solo exécutable n'est encore fourni.
Le contrat commun est détaillé dans `METHODE_WRAPPER_SOLO.md`.

## Priorités

| Source MP | Future entrée solo | Données | Spéculation | Fiche |
| --- | --- | --- | --- | --- |
| `london_mp` | Prototype — reconstruction — Poland/London MP | carte publiée, 32 spawns | très haute | [fiche](LONDON_MP/FICHE.md) |
| `alps3_mp_zone` | Prototype — reconstruction — Alps3 Frontline | carte/5 zones | haute | [fiche](ALPS3_MP_ZONE/FICHE.md) |
| `alps3_obj` | Reconstruction — Alps3 Objectifs solo | carte, 4 bindings, 3 objectifs MP | moyenne | [fiche](ALPS3_OBJ/FICHE.md) |
| `ardens1_obj` | Reconstruction — Ardennes1 Objectifs solo | carte, 4 bindings, 3 objectifs MP | moyenne | [fiche](ARDENS1_OBJ/FICHE.md) |
| `ardens2_mp_zone` | Prototype — reconstruction — Ardennes2 Frontline | carte/4 zones | haute | [fiche](ARDENS2_MP_ZONE/FICHE.md) |
| `normandy2b_mp_zone` | Prototype — reconstruction — Normandy2B | carte/5 zones, registre vide | haute | [fiche](NORMANDY2B_MP_ZONE/FICHE.md) |
| `normandy3_mp` | Prototype — reconstruction — Normandy3 | carte/5 zones, véhicules | haute | [fiche](NORMANDY3_MP/FICHE.md) |
| `normandy3_mp_zone` | Test — reconstruction — Normandy3 Zone | variante non publiée et incomplète | très haute | [fiche](NORMANDY3_MP_ZONE/FICHE.md) |
| `normandy4_mp_zone` | Prototype — reconstruction — Normandy4 Frontline | carte/5 zones, véhicules | haute | [fiche](NORMANDY4_MP_ZONE/FICHE.md) |
| `afrika5_mp` | Test — reconstruction — Africa5 Prototype solo | 7 fichiers propres, famille Africa5 | très haute | [fiche](AFRIKA5_MP/FICHE.md) |

Les fragments sans carte complète — England, Castle1/2, Gary Bristol,
Allemagne, Dunkerque et décors urbains/entrepôt/pont-train — sont classés dans
`REGISTRE_CONCEPTS_INCOMPLETS.md`.

## Critère de promotion

Une fiche ne passe de `BLOQUÉ` à `LANÇABLE` qu'après : point d'apparition solo
confirmé, équipe créée, contrôleur chargé, objectif visible, victoire et échec
reproductibles, fin sans commande multijoueur, sauvegarde/reprise et retour
intact à la carte MP source.

