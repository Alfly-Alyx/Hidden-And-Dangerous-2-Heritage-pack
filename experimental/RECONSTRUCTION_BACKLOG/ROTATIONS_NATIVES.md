# Rotations 4DS/5DS : correction et preuves indépendantes

**27 septembre 2026.** Une erreur de convention dans nos outils hors moteur
est corrigée. Les quaternions natifs XYZW doivent être conjugués pour entrer
dans notre calcul mathématique actif à vecteurs colonnes : `(-x,-y,-z,w)`.
L'opération inverse est identique. Ce résultat ne qualifie ni les rotations
de `scene2.bin`, ni l'interpolation native, ni le skin animé.

## Preuves qui ne dépendent pas d'un aller-retour de notre encodeur

Les matrices inverses de repos stockées dans les deux modèles de mains sont
comparées aux transformations hiérarchiques de leurs joints. Les identifiants
de joints, différents de leur ordre dans le fichier, et les octets de parents
sont vérifiés séparément. Pour chaque os, la composition doit donner l'identité.

| Modèle privé | Os | Sommets / paires de poids | Triangles | Erreur maximale |
|---|---:|---:|---:|---:|
| fpv_hands | 36 | 991 | 1526 | 4,625 × 10⁻⁷ |
| fpv_hands_r | 36 | 1076 | 1654 | 4,708 × 10⁻⁷ |

L'ancienne convention produit une erreur allant presque jusqu'à **2**, et non
un simple écart d'arrondi. Le nouveau contrôle refuse un résidu supérieur à
10⁻⁵. Il n'exporte ni sommets, ni matrices commerciales.

Les **224 premières rotations** des neuf couples Benelli concordent aussi
avec leurs modèles 4DS appariés ; écart maximal 1,770 × 10⁻⁶. Les deux formats
utilisent donc la même convention sur ce corpus. Les pistes absentes ou sans
clé initiale ne sont pas complétées : leur héritage demeure à établir.

`tools/four_ds_skin.py` est borné au domaine effectivement examiné : racine
identité, un LOD non instancié sans données supplémentaires, enfants joints,
une paire `(identifiant d'os, octet)` par sommet. **La signification de cet
octet n'est pas encore qualifiée** ; aucun mélange de poids n'est inventé.

La disposition binaire est recoupée avec la référence primaire
[4ds.bt épinglée](https://github.com/RoadTrain/mafia-formats/blob/13d2ff8b4d58a098438a0b300129d9e7c574e783/4ds.bt).
Le [lecteur Noesis examiné](https://github.com/RoadTrain/noesis-plugins/blob/dc4d3dcfc26a177f14ce3687e2498a176914d240/pluginsource/mafia4ds/mafia4ds/mafia4ds_import.cpp)
lit les données HD2 mais ne démontre pas leur déformation ; il n'est pas pris
comme preuve de sémantique des poids. Aucun code tiers n'est recopié.

## Correction des livrables

- Le calcul mathématique générique reste inchangé. `native_affine` et
  `decompose_native` rendent explicite la frontière de sérialisation.
- Benelli : six octets de rotations du chargeur recalé changent, sur 61 351.
  Les sommets, matériaux, noms et autres ressources restent intacts. Nouveau
  SHA-256 : `c445e8ff1c96da33317e7eeafe14f18277b9650e8c796e1078396eab6e3ef85b`.
  L'ancien `0c54e499…` est historique et refusé pour une nouvelle application.
- Nouveaux bancs privés : `BenelliFPV_v6`, `BenelliDescriptor_v4`, et
  `BenelliTables_Personal_v4` sur la même couche PatchX01 que le précédent.
  La construction intermédiaire personnelle v3 utilise Sabre comme référence ;
  ses quatorze contenus sont identiques à v4, mais pas les comparaisons de couche.
  Face au personnel v2, **seul le modèle FPV change** : tables, descripteur,
  fragment FPV, modèle extérieur et huit textes restent identiques.
- FG42/MG34 : `FG42_Motion_v3` et `MG34_Motion_v3` conjuguent les rotations
  modernes à l'écriture 5DS. Les 18 animations sont réencodées, les modèles
  4DS restent identiques. Les 514 poses sont recalculées et les quatorze PNG
  sont identiques aux aperçus v2 : l'intention du mouvement est conservée.
  Les deux planches et l'aperçu filaire Benelli ont été inspectés.

Les anciens dossiers privés ne sont ni écrasés ni supprimés. Leurs empreintes
dans les documents historiques ne désignent plus la version à préparer.
Les nouvelles versions restent désactivées ; les données dérivées du jeu ne
sont pas ajoutées à GitHub.

## Préparations et retour arrière

Le renouvellement `refresh` exige une copie indépendante, aucun essai actif,
les cibles originales intactes et une nouvelle charge entièrement vérifiée.
Il archive les octets exacts du précédent `BENELLI_TRIAL.json`, conserve les
sauvegardes, puis remplace atomiquement la préparation inactive. Un ancien
modèle précisément épinglé reste lisible **uniquement pour restaurer ou
retirer une ancienne préparation**, jamais pour la réappliquer.

Les rapports de répétition portent des noms distincts et ne sont pas écrasés.
Les trois préparations ont été renouvelées sur le personnel v4. Trois cycles
complets sont consignés dans `BENELLI_OFFLINE_REHEARSAL_rotations-v2.json`,
un par copie : chacun retrouve les **24 385 fichiers initiaux**, sans changement
ni fichier supplémentaire, et aucun `active.json` ne reste en place.
Ces opérations ne lancent aucun jeu. Les essais de déformation, chargement,
caméra, événements, sauvegardes et hôte/client restent distincts.

Seize tests synthétiques supplémentaires couvrent les rotations indépendantes,
les matrices de repos inventées, les premières clés, le renouvellement et la
restauration historique. Ils ne remplacent aucune validation en moteur.
