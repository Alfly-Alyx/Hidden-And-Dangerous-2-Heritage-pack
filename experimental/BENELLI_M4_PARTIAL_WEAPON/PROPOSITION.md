# Benelli M4 Super 90 — vestige d’arme partiel

État : **meilleur candidat à une reconstruction fidèle, toujours expérimentale**,
14 septembre 2026. Le prototype visuel est désactivé, ne contient aucun asset
commercial et n’entre pas dans le système Weapon.

**Actualisation du 26 septembre :** un [banc privé réalisé](../BENELLI_M4_ADDITIVE/BANC_FPV.md)
remplace désormais la seule proposition de visualiseur. Le modèle extérieur
moderne et le FPV statique dérivé sont fabriqués hors moteur. L'étude ci-dessous
reste historique ; les étapes jouables demeurent non validées.

## Verdict

Les archives conservent une chaîne première personne exceptionnellement riche :
neuf états FPV avec compagnons 5DS, textures/icône, munition et sons de tir et de
rechargement. Elle permet un démonstrateur visuel fidèle et fournit les meilleurs
matériaux du corpus pour recréer l’arme. Elle ne fournit toutefois ni objet
ramassable ni entrée Weapon fonctionnelle. Contrairement au premier inventaire,
un record original `item_shoot` de 135 octets existe : ses champs nécessitent
encore une qualification, ce n'est pas une configuration de tir prête à activer.

Classement : **vestige partiel**. Un banc visuel utilisant les fichiers de
l’installation du testeur est borné et fidèle aux ressources présentes. Une
Benelli jouable demanderait des créations modernes essentielles et ne pourrait
pas être présentée comme une simple restauration.

## Ressources commerciales attestées

models.dta contient neuf couples 4DS/5DS, avec l’orthographe historique
« Beneli » :

| État FPV | Couple attesté |
| --- | --- |
| visée | #FPVBeneliAim.4ds / .5ds |
| tir en visée | #FPVBeneliAimShot.4ds / .5ds |
| armement | #FPVBeneliArm.4ds / .5ds |
| sortie de visée | #FPVBeneliDaim.4ds / .5ds |
| désarmement | #FPVBeneliDisarm.4ds / .5ds |
| repos | #FPVBeneliIdle1.4ds / .5ds |
| enrayement | #FPVBeneliJammed.4ds / .5ds |
| état Rel | #FPVBeneliRel.4ds / .5ds |
| tir | #FPVBeneliShot.4ds / .5ds |

#FPVBeneliAim.4ds pèse 63 906 octets et contient 45 nœuds. L’inventaire du
modèle relève notamment les bras/mains, fpv_weapon, blsdum, cardum, cock,
gunlock, shdum, shell01 et magazine. Ces nœuds attestent une préparation FPV
avec pièces mobiles et ancrages d’effets ; leur nom seul ne définit ni cadence,
ni éjection, ni dégâts.

Maps.dta conserve trois bitmaps associés :

- wi_it-benelli.bmp ;
- d_benellim4.bmp ;
- d_benellim4paz.bmp.

TEXTY.txt nomme « Ammunition - Benelli m4 super 90 » à l’identifiant texte 1179,
et Items.md répertorie la munition Benelli M4 Super 90 à l’ID d’objet 179. Il
s’agit d’une munition de catalogue, pas d’une preuve qu’une arme la consomme.

## Sons commerciaux attestés

LangEnglish.dta::Tables/IngameSounds.def conserve les liaisons « I Benelli M4 »
vers f_bene_a.wav et « I Benelli M4 Reload » vers bene_r.wav. Sounds.dta contient
les deux fichiers : f_bene_a.wav (70 236 octets) et bene_r.wav (265 818 octets).

Le tir et le rechargement disposent donc de sources sonores commerciales
attestées. Leur déclenchement exact reste à reconstruire avec la future entrée
Weapon ; le prototype visuel demeure volontairement silencieux afin de ne pas
inventer cette synchronisation.

## Éléments essentiels manquants

- entrée Weapon Benelli dans la table fonctionnelle ;
- modèle monde/posé ou troisième personne w_benelli* ;
- modèle FPV statique séparé attendu par une entrée Weapon ;
- liaison prouvée vers la munition 179 ;
- interprétation qualifiée des paramètres conservés et des champs manquants ;
- capacité du magasin et règle exacte de rechargement ;
- liaison événementielle de ces deux sons à la future entrée Weapon ;
- icônes/états d’inventaire complets pour prise, dépôt et échange ;
- usage par l’IA, sauvegarde et réplication réseau.

Au stade de l'étude initiale, l'absence du modèle monde interdisait une
intégration propre : une
arme équipée ne disposerait pas d’apparence fiable dans les mains d’un tiers,
au sol ou lors d’un échange.

## Démonstrateur visuel borné

PROTOTYPE_VISUAL_FPV.plan.disabled décrit un visualiseur manuel des neuf couples.
Il résout les fichiers depuis une installation possédée, affiche un seul état à
la fois et ne crée aucun Item. Il ne joue aucun son, ne tire aucun projectile et
ne consomme pas la munition 179.

Le sélecteur reste manuel : les suffixes Arm, Rel ou Jammed n’autorisent pas à
inventer une machine d’états ou leur chronologie historique. Le banc sert à
mesurer matériaux, échelle, pivots, continuité et visibilité des sous-objets.

## Chemin vers une arme fonctionnelle

Une phase ultérieure devrait d’abord créer sous un nom explicitement moderne un
modèle monde/posé et le modèle FPV statique manquants, puis une entrée Weapon de
laboratoire séparée. Capacité, cadence, dégâts, dispersion et recul seraient des
choix modernes testés indépendamment. Les sons attestés et l’ID 179 peuvent être
référencés depuis l’installation du testeur, mais leur timing/liaison doivent
être instrumentés avec une sauvegarde jetable.

Une arme fonctionnelle ne devient candidate à diffusion qu’après tests de visée,
tir, rechargement, enrayement, changement d’arme, dépôt/reprise, mort, IA,
sauvegarde et coop. Même réussie, elle reste une **reconstruction expérimentale**.

## Test du banc visuel

1. Vérifier les hashes et la présence des 18 fichiers dans l’installation.
2. Charger chaque couple isolément ; aucune ressource ne doit être extraite dans
   ce dossier.
3. Comparer origine, échelle, bras, mains et fpv_weapon entre les neuf états.
4. Relever pivots/visibilité de cock, gunlock, shell01 et magazine sans les
   animer artificiellement.
5. Vérifier les trois textures, transparence, mipmaps et variantes de rendu.
6. Tester fermeture/rechargement du visualiseur et absence de fichier résiduel.

Acceptation : les neuf états sont inspectables de façon reproductible et le
banc n’affiche jamais « arme jouable ». Un échec de texture ou de couple reste
un résultat d’inventaire, pas une autorisation de substituer un autre fusil.

## Réversibilité et limites

La désactivation consiste à ne jamais transformer le plan disabled en banc
actif. Un futur visualiseur doit seulement référencer l’installation locale et
se désinstaller sans modifier models.dta, Maps.dta ou les tables d’objets.

Audit statique uniquement : aucune compilation, aucun test en jeu, aucune
modification de l’installeur, des outils ou du README.
