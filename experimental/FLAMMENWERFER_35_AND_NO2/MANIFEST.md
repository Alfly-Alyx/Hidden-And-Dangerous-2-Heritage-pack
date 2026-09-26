# Manifeste — FLAMMENWERFER_35_AND_NO2

## OFFICIEL

| Ressource | Preuve | Portée réelle |
| --- | --- | --- |
| `wi_ge-flmwr35*` | `Maps.dta` | icône Flammenwerfer 35 |
| `wi_br-flmthr2*` | `Maps.dta` | icône Portable No. 2 |
| objet 207, `AMMO Flammewer` | `items.sav` | identité de munition allemande |
| objet 208, `AMMO Flamethrow` | `items.sav` | identité de munition britannique |
| effet 25 `plamenomet` | `TABLES/effects.def` | particule visuelle avec `d_fire.tga` |
| `flame1.4ds`, 471 octets | `models.dta` | un nœud `fire01`, effet seulement |
| voix « They've Got Flamethrowers » / « Aaaa » | `IngameSounds.def` | dialogue/réaction, pas son d'arme |

## DÉRIVÉ / INFÉRÉ

- deux armes distinctes étaient prévues ;
- l'effet 25 et les munitions étaient probablement destinés à leur chaîne ;
- aucun paramètre de portée, débit, dégâts ou réservoir ne peut être déduit de
  ces seules ressources.

## CRÉATION MODERNE REQUISE POUR CHAQUE ARME

- [Ensembles monde/sol et volumes dorsaux réalisés](MODELES_MODERNES.md) :
  recettes originales distinctes, deux LOD, cinq matériaux ; statiques et
  désactivés, sans origine commerciale ni validation moteur ;
- modèles FPV et rattachements third-person à réaliser ;
- animations joueur et IA ;
- allumage, son continu, extinction et sécurité ;
- jauge/consommation, recharge, jet, collision, occultation et dégâts ;
- réactions IA, inventaire, sauvegarde et réseau ;
- paramètres d'équilibrage documentés comme modernes.

## ABSENT / NON PROUVÉ

- entrée Weapon exploitable ; modèle animé/tenu complet ; sons mécaniques ;
- comportement du carburant ; primitives de dégâts continues historiques.
