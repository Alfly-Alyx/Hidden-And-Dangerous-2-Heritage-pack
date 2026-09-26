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
| record `Benelli` / `item_shoot.tbl` | `others.DTA`, offsets 1547–1682 | 135 octets attestés, sémantique numérique non qualifiée |
| Weapon 9 actuel | table commerciale | boussole livrée, réservée et non modifiable |
| Liaison des identifiants Item/FPV | client 1.12 possédé, analyse et émulation ciblées | `groupe = slot + 100` confirmé ; pas une validation d'animation en jeu. [Contrat](CONTRAT_NATIF.md). |
| Liaison arme/munition et état d'objet | même client 1.12, routines isolées | 208 associations commerciales contrôlées ; munition 179 : quantité 7,0 ; deux tags communs non relus. Pas une validation de sauvegarde complète. [Limites](ETAT_ET_MUNITION.md). |

## DÉRIVÉ / INFÉRÉ

Le [banc FPV](BANC_FPV.md) distingue désormais données et interprétation :
neuf paires décodées sans piste manquante, modèle statique privé à huit nœuds,
inspecteur de poses et de clés, deux sons décodés mais non écoutés. Le modèle
statique est **DÉRIVÉ DU JEU**, son extraction/recalage est une opération moderne.
Le modèle extérieur est une **CRÉATION MODERNE ORIGINALE**. Aucune animation
jouée hors moteur ne serait une preuve d'équivalence au moteur.

- les neuf couples forment une chaîne FPV avancée et les noms de nœuds
  suggèrent culasse, chargeur et éjection ;
- la munition 179 et les deux sons étaient vraisemblablement destinés à cette
  arme ; le consommateur de munition est prouvé, mais aucune fiche Weapon
  Benelli commerciale ni synchronisation sonore n'est restaurée ;
- la position historique du bloc d'animations n'autorise pas à reprendre le
  slot 9 désormais occupé.

## CRÉATION MODERNE REQUISE

- slot Weapon additif, choisi seulement après audit (`FREE_SLOT_TO_AUDIT`) ;
- entrée Item/Weapon Benelli et migration/sauvegarde correspondante ;
- modèle monde, au sol et third-person : [fabriqué](MODELE_MODERNE.md), essais requis ;
- modèle FPV statique séparé : [dérivé localement](BANC_FPV.md), compatibilité requise ;
- chargeur, cadence, dégâts, dispersion, portée, recul et enrayement ;
- événements et timings des sons, projectile, douille et flash ;
- prise/dépôt, animation tierce, IA et réplication réseau.

## INTERDIT

- Weapon 9 ; remplacement de la boussole ; copie d'un slot occupé ;
- présentation comme simple réactivation ;
- redistribution des ressources commerciales dans ce dossier.
