# Manifeste — BENELLI_M4_ADDITIVE

## OFFICIEL

| Ressource | Provenance | Statut |
| --- | --- | --- |
| 9 couples `#FPVBeneli*.4ds/.5ds` | `models.dta` | présents : Aim, AimShot, Arm, Daim, Disarm, Idle1, Jammed, Rel, Shot |
| mapping des neuf états | `Tables/FpvAnims.sav` | bloc complet conservé entre Mosin et Garand |
| `wi_it-benelli.bmp` | `Maps.dta` | icône inventaire |
| `d_benellim4.bmp`, `d_benellim4paz.bmp` | `Maps.dta` | textures conservées |
| munition objet 179 / texte 1179 | `items.sav`, `TEXTY.txt` | « Ammunition - Benelli m4 super 90 » |
| `f_bene_a.wav` | `Sounds.dta` / `IngameSounds.def` | tir, 70 236 octets |
| `bene_r.wav` | `Sounds.dta` / `IngameSounds.def` | rechargement, 265 818 octets |
| Weapon 9 actuel | table commerciale | boussole livrée, réservée et non modifiable |

## DÉRIVÉ / INFÉRÉ

- les neuf couples forment une chaîne FPV avancée et les noms de nœuds
  suggèrent culasse, chargeur et éjection ;
- la munition 179 et les deux sons étaient vraisemblablement destinés à cette
  arme, mais leur binding fonctionnel n'est pas conservé ;
- la position historique du bloc d'animations n'autorise pas à reprendre le
  slot 9 désormais occupé.

## CRÉATION MODERNE REQUISE

- slot Weapon additif, choisi seulement après audit (`FREE_SLOT_TO_AUDIT`) ;
- entrée Item/Weapon Benelli et migration/sauvegarde correspondante ;
- modèle monde, au sol et third-person ;
- modèle FPV statique séparé ;
- chargeur, cadence, dégâts, dispersion, portée, recul et enrayement ;
- événements et timings des sons, projectile, douille et flash ;
- prise/dépôt, animation tierce, IA et réplication réseau.

## INTERDIT

- Weapon 9 ; remplacement de la boussole ; copie d'un slot occupé ;
- présentation comme simple réactivation ;
- redistribution des ressources commerciales dans ce dossier.
