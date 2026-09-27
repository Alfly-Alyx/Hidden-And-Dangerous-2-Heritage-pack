# Montage moderne conforme à la sélection FPV

**27 septembre 2026.** Deux nouveaux modèles et 36 clips dérivés privés sont
construits. Ils remplacent la hiérarchie d'auteur par une hiérarchie compatible
avec la sélection observée dans le client. **Ce n'est pas une arme jouable.**

## Contrainte trouvée dans le client

Le chargeur d'objet `0x7df970` demande `fpv_weapon` avec le masque **1**, qui
sélectionne un visuel, pas un dummy. Le second nom `magazine`, facultatif,
emploie le masque `0x21`. Renommer le dummy de l'ancien assemblage ne suffit donc
pas. La recherche native, sa casse ASCII par défaut et l'énumération des enfants
directs sont exécutées dans `ls3d_frame_find_oracle.py`, sur des arbres synthétiques.

Le client `0x491130` ajoute ensuite la racine et ses **enfants directs** au modèle
des mains. L'examen de `I3D_Model::AddFrame` (`0x100341c0`) montre un ajout unique,
sans descente récursive. Les anciens assemblages laisseraient donc 35/33 nœuds
hors de cette liste d'animation. Ce parcours client et AddFrame sont ici des
preuves statiques ; ils ne sont pas annoncés comme exécutés dans un modèle chargé.

Le contrôle privé `.analysis/fpv-frame-contract-flat-20260927.json` vérifie
30 recherches synthétiques et les deux montages. Les anciennes racines sont
refusées avec le masque 1 ; les nouvelles sont trouvées avec tous leurs enfants.

## Modèles et clips reconstruits

- Le skin de tuyau déjà créé devient le visuel racine `fpv_weapon` ; aucun
  maillage vide n'est inventé pour satisfaire le filtre.
- Les 37/35 autres nœuds sont ses enfants directs, soit **38/36 nœuds** au total.
- Géométrie, deux LOD, matériaux et données de skin sont inchangés octet pour octet.
- Les positions de repos deviennent relatives à cette racine. Les positions
  animées des pièces tenues sont recalculées aux frames entières, en conservant
  leurs rotations originales et les mêmes durées.
- Toutes les clés des mains et des huit os de tuyau sont conservées exactement.
  Les nouvelles banques ont **75/73 pistes**, et des alias distincts des anciennes.

Les anciennes animations ne doivent pas être associées aux nouveaux modèles :
l'appartenance des transformations a changé. Le constructeur le consigne et
vérifie les empreintes des sources. Les corps d'animation restent sous la limite
du banc natif, sans troncature ni suppression de piste.

Empreintes des modèles modernes :

- F35 : `25d5a5a3092f533138efdfd80ed4221e20cd55d8860ffe9a2ef4ccf47606bb70`.
- No. 2 : `47739de82f000d613ed7bd9ff783fdd0090af981c100251e399c5a6d906b4454`.

Les recettes et outils sont publics ; les clips liés aux squelettes commerciaux
restent privés, marqués `DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL`. Aucun modèle
ni texture de mains commerciales n'est exporté. Aucun compagnon de chargement
automatique, descripteur d'arme ou fichier actif n'est créé.

## Contrôles

Seize tests supplémentaires couvrent recherche native de référence, hiérarchie,
géométrie conservée, recalcul des positions, matrices aux clés et entre clés,
refus de sources modifiées et aperçus des deux LOD. Quatre planches privées de
six poses sont inspectées depuis les clips réellement sérialisés, avec référence
numérique des transformations et mains grisées. Ce ne sont pas des captures du jeu.

Le contrôle natif dense séparé est terminé, avec 36 séquences et 2 316 instants
observés : 171 384 poses de nœuds, 85 692 comparaisons de matrices d'équipement,
2 393 586 sommets de mains et 2 001 024 sommets de tuyau. Les deux LOD sont
évalués 4 632 fois ; 4 632 cibles de poignet et 1 000 512 sommets d'extrémités
de tuyau sont contrôlés. Le temps et le skin correspondent exactement à leurs
références ; l'écart maximal de palette est `2,981e-7`. Pour l'équipement,
l'écart maximal est `5,961e-8` aux clés et `0,000152267` entre clés ; pour les
poignets, `1,341e-7` et `0,000156883`. Les extrémités fixes/tenues du tuyau
restent sous `1,491e-8`/`5,266e-8`, dans les seuils préalablement définis.

Rapport privé : `.analysis/fpv-flat-animation-native-20260927.json`. Le temps
et les poses sont lus dans la mémoire native persistante ; palette et skin
sont exécutés dans des émulateurs séparés. La palette de diagnostic représente
encore les nœuds d'équipement par des joints : elle ne qualifie pas la division
des transformations entre véritable visuel skin racine et rendu. Les banques
avec aperçus sont `F35_FlatFPV_Motion_v2` et `F2_FlatFPV_Motion_v2`, sous
`.analysis/modern-assets/`, 34 fichiers chacune. Leurs 36 clips sont vérifiés
par empreinte contre ceux du rapport ; aucun résultat n'est déduit des seuls
tests de référence.

## Association native des os au skin racine

Le banc `ls3d_skin_binding_oracle.py` exécute la découverte des os
`0x100527d0..0x1005295e`, sa descente récursive et les consultations de type
visuel `0x10057050`. La hiérarchie après chargement reste fournie explicitement,
mais le parcours, le tri par identifiant d'os et l'écriture du propriétaire de
chaque joint sont effectués par les instructions natives.

Les deux modèles retrouvent leurs **huit os**, dans l'ordre 0–7, tous rattachés
au skin racine. Les autres pièces ne sont pas confondues avec les os : 20/18
consultations natives du type de visuel pour F35/No. 2. Aucun skin imbriqué ne
coupe leur parcours. Le contrôle de 77 arbres synthétiques couvre aussi les
identifiants réordonnés, chaînes de 64 joints, absence de géométrie et skins
imbriqués ; 49 associations réussies totalisent 550 os. Onze tests supplémentaires.

Point important : un skin imbriqué arrête **la boucle des frères de son niveau**,
pas uniquement la descente dans ses enfants. Ce comportement natif est conservé
dans la référence ; il n'est pas présent dans les deux montages aplatis.
Identifiants dupliqués, trous dans les os collectés et hiérarchies hors domaine
sont refusés, sans créer des entrées de palette nulles.

Rapport privé : `.analysis/skin-binding-native-20260927.json`, avec les mêmes
empreintes de modèles que ci-dessus. Il s'agit d'un skin neuf : libération du
pointeur nul et allocation bornée de son tableau sont des doubles. Le calcul
des limites `0x10052330` est également un double explicitement signalé ; il
n'est **pas exécuté**. Chargement/copie du modèle, palette, skin et rendu restent
hors de ce banc. Les arbres et les champs hors association sont préservés.

Le [calcul natif des enveloppes animées](LIMITES_TUYAUX_ANIMEES.md) est maintenant
contrôlé dans un banc séparé : 304 128 sommets des deux LOD restent contenus
pendant les changements de clips. Il ne remplace pas la copie/visibilité de scène.

## Reproduction et limites

```powershell
.\.venv\Scripts\python.exe tools/build_equipment_fpv_animation.py --case F35 --game 'D:\Games\Hidden and Dangerous 2' --archives-only --previews --output-name F35_FlatFPV_nouveau
.\.venv\Scripts\python.exe tools/fpv_flat_animation_native_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/fpv-flat-native_nouveau.json'
.\.venv\Scripts\python.exe tools/skin_binding_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/skin-binding_nouveau.json'
```

Les [associations et lectures d'animations](RESOLUTION_ANIMATIONS_FPV.md) sont
traitées séparément. Il reste le chargement du modèle, sa copie native et la
répartition effective des transformations entre skin racine et rendu ; puis
caméra, contacts fins des doigts, transitions visuelles, événements et mécanique.
Les [changements de clips pendant la lecture](../RECONSTRUCTION_BACKLOG/ENCHAINEMENT_ANIMATIONS_NATIF.md)
sont désormais contrôlés dans une même mémoire, sans encore qualifier les
contacts ou le rendu pendant les mélanges.
Le sac reste fixe : ni attache dorsale joueur/IA ni physique du tuyau ne sont
réalisées. Les gestes Rel/Jammed ne rechargent et ne débloquent encore rien.
