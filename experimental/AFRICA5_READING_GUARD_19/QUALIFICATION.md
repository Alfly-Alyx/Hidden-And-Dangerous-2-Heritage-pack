# AF4_19 — lecture : profil natif reproductible

26 septembre 2026. **MODERNE, laboratoire uniquement, API historique non validée.**

`africa5-guard19-reading-interruptible` reconstruit le script Patch effectif de
1590 octets en une variante de 2607 octets, SHA-256
`ddb51b1354109c28b8a45c4c746b1f553c777018a595e4a7fd87deb82c2cf42c`.
Aucun script commercial complet, modèle ou son n'est distribué avec la recette.

## Géométrie retrouvée

Le propriétaire humain reste `AF4_19`, lié à `AF4_19.scr` dans le registre solo.
Les deux accessoires sont vérifiés séparément comme instances de modèle de type 9
avec une référence exacte, un nœud visuel `Box01` racine et aucun enfant rattaché.

| Accessoire | Instance | Modèle dans models.dta | Taille / SHA-256 |
| --- | --- | --- | --- |
| Livre manipulé | `m_AF5_slozky01a7` | `models/m_af5_slozky01a.4ds` | 1309 / `fe9d05b9d48b1a12d0f3790a6c6f452ea61601b564541408545785e338ee7ad4` |
| Archive inspectée | `m_AF5_slozky01b14` | `models/m_af5_slozky01b.4ds` | 1309 / `47357a054d21b5712febe2e114a353e879881e626d016d80e825827a44bb393e` |

Chacun possède 24 sommets, 12 triangles, trois matériaux et un dummy indépendant.
Positions monde des instances : livre (35.421612, 0.037319, 97.459435), archive
(35.554207, 0.584466, 97.497627). Les étendues locales sont respectivement
environ (0.087473, 0.351471, 0.270000) et (0.169642, 0.351471, 0.270000).
Ni le maillage, ni le dummy, ni le nom ne prouvent une saisissabilité, une collision
ou un point d'attache à la main. Les quaternions sérialisés ne sont pas convertis
sans validation de leurs conventions.

## Machine d'état moderne limitée

La variante réactive prise, lecture, arrêt puis dépôt aux emplacements dormants.
L'inspection de l'archive, les délais 1000/2000, modes IA, postures et chaîne
commerciale d'alarme sont conservés. Aucun objectif, voix, acteur ni binding ajouté.

- Le signal 1 démarre seulement si aucun cycle n'est déjà en cours, avec verrou
  avant le saut. Les répétitions ne reprennent pas une prise en cours.
- Le drapeau d'objet est posé avant `HUMAN_PickObject`, celui de lecture avant
  `HUMAN_ACTIVITY_Read(1, book)` : une interruption pendant un appel voit le
  nettoyage nécessaire, même si l'opération n'est pas encore revenue.
- Alarme : déverrouillage du cycle, arrêt conditionnel de lecture, remise à zéro
  du drapeau d'objet, puis **dépôt commercial inconditionnel**, reste du handler
  et `EndScript()` inchangés.
- Décès : arrêt conditionnel, dépôt conditionnel, puis message et fin d'origine.
  Aucune posture forcée sur le corps.
- Fin d'alarme : nettoyage conditionnel avant les réglages commerciaux et
  `ACTIVATE`, avec cycle réarmé. Ce handler commercial peut rester inaccessible
  après `EndScript`; sa priorité réelle n'est pas prétendue validée.
- Fin normale : drapeaux remis à zéro avant arrêt et dépôt, puis boucle d'origine.

Les nouveaux verrous limitent les réentrées ; ils ne rendent pas une API
ininterruptible miraculeusement sûre. Aucune désactivation d'alarme n'est ajoutée.

## Critères de qualification

Comme les autres profils Africa 5, cette variante exige d'abord une preuve du
témoin avec son ancien détecteur de piste manquant, conservé sans contournement.
La recette reste refusée en laboratoire renommé.

Le commentaire d'origine attendait explicitement que `Read` fonctionne ; aucun
précédent actif n'a été établi. Une erreur de symbole, de signature ou de
chargement impose le retour au témoin, pas une substitution silencieuse.

Tester cinq cycles, signal 1 répété, alarme et décès avant/pendant prise,
pendant lecture, après arrêt et après dépôt. Vérifier livre unique, main libre,
absence d'objet invisible/orphelin, délai d'alarme, reprise, sauvegarde/chargement,
optimisation/LOD et objectifs. Le retour arrière remet intégralement le script
Patch sans activité de lecture ni nouvel objet.

Le registre `validation/reconstruction-runtime.json` garde tous les résultats
en attente. Les anciens prototypes textuels illustrent une première proposition ;
la recette actuelle ajoute les verrous et les preuves de modèles ci-dessus.
