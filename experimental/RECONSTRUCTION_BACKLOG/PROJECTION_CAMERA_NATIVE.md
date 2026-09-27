# Matrices natives de caméra et champs de vision

**27 septembre 2026.** Le calcul de perspective est qualifié sur un objet caméra
fourni dans un émulateur isolé. Aucune fenêtre, scène, caméra en jeu ou image
rendue par le pilote graphique n'est exécutée.

## Identification

La fabrique de frames `0x10018e40` sélectionne, pour le type 3, la branche
`0x10018edd` et la table de fonctions `0x1009bd70`. Ses entrées `+0x74` et
`+0x78` sont les setters `0x10009e30` et `0x10009e90`. Ils écrivent les champs
`+0x120` et `+0x12c`, puis appellent `0x10009b30` en mode perspective.

Les wrappers du client `0x465e50` et `0x465e00` transmettent respectivement
ces deux réglages ; les getters `0x465e80` et `0x465e30` relisent leurs champs.
Ce raccord est une preuve statique, pas l'exécution de la sélection finale
de caméra par le client. Le banc emploie les termes **primaire** et **secondaire**
pour ne pas supposer quelle matrice sera utilisée par chaque rendu FPV.

L'analyse statique supplémentaire distingue les cibles du contrôleur FPV :
`+0x30` alimente le réglage primaire, `+0x34` le secondaire, via les méthodes
du module caméra `+0x50/+0x54` et `+0x5c/+0x60`. L'initialisation `0x4920ee`
et la sortie de visée `0x4921cc` donnent au secondaire la constante float32
`0x3f91361e`, environ **65°**. L'entrée en visée `0x492195`, après la demande
d'animation d'état 11, lui donne `0x3f32b8c3`, environ **40°**. Le primaire suit
une autre source : champ global au repos, paramètre d'action à la visée.
Ces écritures sont conditionnelles ; aucun appel de jeu autour d'elles n'est
exécuté par le présent banc.

Dans le parcours de rendu examiné, `0x10061aa7` sélectionne la matrice combinée
`+0x390`, puis `0x10061aea` fournit la projection `+0x350` au pilote. Le bloc
`0x10062178..0x100621a6` rétablit ensuite `+0x1d0/+0x190`. C'est une preuve
statique de deux passes distinctes ; l'entrée effective des nouveaux modèles
dans cette passe et les appels graphiques restent à qualifier.

Bibliothèque verrouillée : `LS3DF.dll`, 864 256 octets, SHA-256
`12c61eed2aec0c45700ad0a5ddfd7cbb3cbf0ea15ec67de155790bb24e7756ee`.
Le binaire client reste la copie privée verrouillée déjà utilisée par les
autres analyses ; aucun binaire commercial n'est publié.

## Comportements vérifiés

- Les deux angles sont bornés entre les constantes float32 **0,01** et **π**.
- En perspective normale, `m00 = cot(angle/2)` et `m11 = m00 × aspect` :
  l'angle est donc horizontal dans ce calcul, non vertical.
- La profondeur homogène vaut `w = z` : l'avant de cette projection est **+Z**.
- Au-delà d'un rapport largeur/hauteur **strictement supérieur à 2,5**, le moteur
  double le demi-angle, puis le borne à **1,5 radian**. Le seuil exact n'est pas
  traité comme un écran ultra-large.
- Les matrices `+0x190`, `+0x2d0` et `+0x350` sont recalculées. La deuxième
  reprend le cadrage primaire avec des plans proche/lointain multipliés par
  10/1 000 en l'absence de lien externe. La troisième possède son propre
  angle et ses propres plans.
- Les quatre demi-étendues au plan proche sont mises à jour ; le compteur
  `+0x104` est incrémenté une fois. Les autres octets de l'objet restent intacts.

`ls3d_camera_projection_oracle.py` exécute les setters complets et le parcours
de perspective sans appel externe, dans les limites d'instructions et
d'écritures annoncées. L'objet synthétique est sans lien de caméra externe,
le mode orthographique est exclu. Les angles, aspect et plans sont validés
avant l'émulation ; nombres non finis et paramètres hors domaine sont refusés.

## Résultat et portée

**352 cas natifs**, dont **88 ultra-larges**, réussissent ; écart maximal nul
avec la référence numérique. Ils couvrent 32 calculs directs et 160 appels
de chacun des deux setters, dont leurs bornes. Le rapport privé est
`.analysis/camera-projection-native-20260927.json`. Huit tests synthétiques
supplémentaires couvrent les formules, seuils, domaines et refus de bibliothèque.

Ce résultat ne qualifie pas encore les valeurs choisies par le client, la
sélection de la matrice FPV, les transformations vue/monde, le viewport,
les effets du correctif écran large, ni le placement des armes modernes.
Il ne permet donc pas d'annoncer leur caméra calibrée ou leur rendu validé.

```powershell
.\.venv\Scripts\python.exe tools/ls3d_camera_projection_oracle.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output .analysis/camera-projection-nouveau.json
```
