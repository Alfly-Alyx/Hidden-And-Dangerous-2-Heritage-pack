# Africa 5 — décalage aléatoire de la palette de visages

État : script complet reproductible désactivé, laboratoire bloqué, 25 septembre 2026.

## Preuve commerciale et choix moderne

`AF4_faceassigner.scr` est lié à `dummy_face_assigner`, présent dans `scene2.bin`.
Il conserve cinq initialisations aléatoires commentées, remplacées par des
indices fixes : allemand 10, quatre autres nationalités 3. Ce ne sont pas des
graines du générateur global : ce sont les indices de départ de palettes.

Le code actif appelle **46 fois `GERMAN_FACE`**, et aucune fois les quatre
autres routines. Les 46 destinataires existent dans `actors.bin`. La routine
allemande parcourt cycliquement quatorze textures, puis revient à zéro. Elle
ne tire pas un visage indépendant pour chaque soldat. Même avec le départ
fixe 10, les quatorze textures sont déjà employées dans la mission.

La variante `africa5-random-german-face-seed` change uniquement l'initialisation
allemande 10 en `_RandomInt(german_faces_count)`, expression historique. Elle
est classée **MODERNE** pour sa sélection partielle et volontaire : les quatre
tirages sans consommateur restent désactivés, les quatre valeurs fixes restent 3.
La déclaration commentée demeure un vestige; aucune seconde déclaration active
n'est ajoutée. Les 46 appels, les textures, leur ordre et le bouclage sont inchangés.

Les visages fixes `AF4_12/e_f0w2` et `AF4_23/e_f080` ne sont pas randomisés.
La ligne `AF4_10/e_f0w1` reste également hors palette : commerciale commentée,
elle est restaurée séparément par `Africa5DormantActorsInstaller.cs`.

## Contrôles et limite Heritage

Quatre sources sont épinglées dans le [catalogue](../reconstruction-variants.json) :
script Patch, registre, acteurs et scène. Source : **6835 octets**, SHA-256
`c4ed19c80aabc200205c1c7a50d8ca063e5ccea2c26be9a6ce22fb9e9eb3ef3d`.
Sortie locale : **6863 octets**, SHA-256
`967febeaf9d9b00fc2053b64d64af4b6923192817aa65d7ec158256e968f881b`.

Quatre tests vérifient l'unique déclaration, la portée de la modification, les
quatorze départs possibles et la commutation du delta avec la restauration
séparée du visage fixe AF4_10 sur une fixture inventée. Le modèle répartit
46 affectations en trois ou quatre occurrences de chaque texture; il ne simule
ni le hasard moteur ni le rendu.

La surcharge installée du script fait **6832 octets**, SHA-256
`98b22d84fc4507a0a322cb60df832096b902bd890cf590db5b47d3f535ed068f`.
Son diff lisible restaure justement AF4_10; une application du delta **en mémoire
seulement** conserve cette ligne active. Cela ne valide pas une installation.
Le générateur strict refuse la surcharge. L'export `--archives-only` est une
référence commerciale isolée, **pas un remplacement du fichier Heritage** :
le copier par-dessus ferait perdre la restauration préexistante d'AF4_10.

Le laboratoire est refusé, comme les filtres du magasin, car
`af4_runway01_detector.scr` manque aux sources commerciales. Aucun fichier
substitut, retrait de liaison ou contournement du contrôle n'est introduit.

## Essais requis

- Débloquer d'abord la fermeture de mission puis comparer les profils exclusifs
  dans une installation de test, sans écraser Heritage.
- Vérifier l'étendue réelle de `_RandomInt(14)`, les 46 acteurs, les visages
  fixes, les corps/modèles et les reprises de sauvegarde.
- Observer les événements aléatoires voisins : le tirage supplémentaire peut
  consommer un état de hasard partagé et modifier leur séquence. Il serait faux
  de garantir statiquement un effet uniquement cosmétique.
- Revenir au profil déterministe et retrouver exactement le cycle commercial.
  Pas de bascule à chaud ni de nouveau numéro de sauvegarde.
