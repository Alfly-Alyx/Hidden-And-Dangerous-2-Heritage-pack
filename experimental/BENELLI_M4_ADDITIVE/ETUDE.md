# Benelli M4 — reconstruction additive expérimentale

État : **priorité haute, banc visuel/sonore d'abord**, 15 septembre 2026.
Aucune entrée Weapon n'est créée, aucun asset commercial n'est recopié et rien
n'est compilé.

## Décision

La Benelli est le vestige d'arme le plus complet du corpus : neuf couples
d'états FPV, leur bloc dans `Tables/FpvAnims.sav`, trois bitmaps, deux sons et
la munition 179 subsistent. Cette richesse autorise un banc fidèle aux ressources
présentes, puis une reconstruction jouable moderne.

L'ancien emplacement Weapon 9 est aujourd'hui la boussole. Il est intangible :
la Benelli ne doit jamais remplacer, masquer, renuméroter ou détourner cet objet.
Toute arme jouable future doit employer un emplacement réellement libre après
audit de toutes les tables Base/Patch/Sabre et des sauvegardes. Aucun numéro
libre n'est inventé dans cette étude.

## Phases

1. **B0 — banc FPV/sonore.** Charger manuellement les neuf couples depuis
   l'installation possédée, sans Item, projectile ni dégâts. Jouer séparément
   `f_bene_a.wav` et `bene_r.wav`, sans prétendre connaître leur timing.
2. **B1 — enveloppe moderne.** Créer un modèle monde/posé/third-person et un
   modèle FPV statique séparé, sous noms `TEST_` ou `PROTOTYPE_`.
3. **B2 — entrée additive.** Réserver un slot libre audité, ajouter une entrée
   Weapon de laboratoire et relier provisoirement la munition 179. Le slot 9 et
   la boussole restent bit-à-bit inchangés.
4. **B3 — mécanique.** Mesurer puis choisir chargeur, cadence, dégâts,
   dispersion, recul, portée, enrayement et chronologie de rechargement. Toutes
   ces valeurs sont marquées modernes.
5. **B4 — intégration expérimentale.** Dépôt/reprise, troisième personne, IA,
   sauvegarde et réseau. Aucun passage au paquet principal sans validation
   indépendante.

Le banc B0 reste le livrable par défaut tant que B1/B2 ne sont pas sûrs.

## Tests essentiels

- vérifier les 18 fichiers FPV et le mapping complet sans substitution ;
- inspecter matériaux, pivots, `fpv_weapon`, culasse, chargeur et points
  d'éjection ;
- auditionner les deux sons séparément et mesurer durée/niveau, sans les lier
  automatiquement aux suffixes d'animation ;
- prouver la liberté du futur slot dans toutes les couches et sur sauvegarde ;
- comparer avant/après la boussole : inventaire, sélection, HUD et sauvegarde ;
- pour B3/B4, couvrir visée, tir, rechargement, enrayement, dépôt, mort, IA,
  hôte/client et reprise.

Critères d'arrêt : collision de slot, boussole modifiée, modèle extérieur
absent, état FPV manquant, son mal synchronisé ou paramètre présenté comme
historique sans source.

## Fichiers du cas

- [`MANIFEST.md`](MANIFEST.md) : frontière officiel/dérivé/créé ;
- [`ROADMAP.plan.disabled`](ROADMAP.plan.disabled) : portes additives ;
- l'ancien banc détaillé reste dans
  `experimental/BENELLI_M4_PARTIAL_WEAPON/` et sert de référence B0.
