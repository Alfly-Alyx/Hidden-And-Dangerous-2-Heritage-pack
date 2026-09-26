# Benelli — contrat natif des fiches et des animations

Établi hors moteur le **26 septembre 2026**, pour le client Sabre Squadron
1.12 possédé. Aucun lancement, modification d'exécutable, accès aux processus
du jeu ni écriture dans une installation. **La sérialisation des fiches
`items.sav` n'est pas celle des sauvegardes de partie.**

## Source et méthode

- Exécutable compacté : 2 277 376 octets, SHA-256
  `1eebde4710f800f712a05b1ecee2ba862c144f478df89b58e54c912e857ee78c`.
- Image privée décompactée : 8 101 888 octets, base virtuelle `0x401000`,
  SHA-256 `2c04629cf79b64c0c12f310187974f357ffbfc22bbc11f1488764cd078d3e7aa`.
  Le cache a été comparé octet pour octet à un nouveau décompactage hors ligne
  de cet original. Ni le cache ni les routines commerciales ne sont publiés.
- `tools/item_native_layout.py` est un décodeur indépendant original.
- `tools/item_native_contract.py` compare ses résultats à des blocs ciblés
  exécutés dans Unicorn, émulateur de processeur isolé. Allocation/libération
  sont remplacées par une arène bornée ; aucun appel système n'est autorisé.
  Destination non revue, image différente, dépassement mémoire ou épuisement
  du budget d'instructions font échouer le contrôle. Le code mappé est non
  inscriptible, les données d'entrée également ; seul l'état fictif est modifié.

Les observations ci-dessous portent sur **ce client**, pas sur un exécutable
Base, une autre version ou un client modifié.

## Fiches d'objets

Le chargeur `0x7dc960` réserve/lit 252 000 octets et boucle sur 500 emplacements.
Un marqueur vide fait avancer de quatre octets ; une entrée présente ajoute
son type puis un bloc de 500 octets. Cela confirme le découpage de 508 octets
complets, sans absorber le marqueur vide suivant.

Le décodeur couvre les deux descripteurs d'action et les trois types d'objet.
Les tailles retournées par les dix sérialiseurs d'action sont respectivement
36, 40, 136, 128, 16, 12, 12, 28, 16 et 0 octets. Un sélecteur nul signifie
l'absence d'action. Pour les sélecteurs 3 et 4, le lecteur natif ne copie que
96 et 88 octets dans l'objet ; les 40 octets supplémentaires sont conservés
comme données non consommées par cette copie, sans leur inventer une fonction.

| Partie | Observation qualifiée |
|---|---|
| Trois champs de modèles/icône | Copies de vingt octets vers les membres `0x24`, `0x2c`, `0x34` |
| Libellé interne de la fiche | N'est pas repris comme chaîne vivante par ce lecteur |
| Actions | Deux sélecteurs à partir de l'offset 136 ; le second dépend de la taille du premier |
| Zone intermédiaire | 32 octets non consommés avant les champs propres au type ; conservés opaques |
| Type 0 | Un membre à `0x54` |
| Type 1 | Membres chargés dans l'ordre `0x58`, `0x5c`, `0x60`, `0x54` |
| Type 2 | Membres chargés dans l'ordre `0x54`, `0x58`, `0x5c`, `0x60`, `0x64` |

Les lecteurs natifs de référence sont `0x7e0150`, `0x7e0910`, `0x7e0a80` et
`0x7e0bb0` ; le calcul de taille commun est `0x7dff10`. Les valeurs non
interprétées restent `value_raw`. Le membre final du type 1 contient notamment
180 pour le Garand et 192 pour le Side by Side ; cela suggère la munition,
mais la preuve du consommateur de ce champ est un travail distinct.

**1 036 entrées vérifiées** : 246 Base, 246 Patch, 272 Sabre, 272 PatchX01.
Pour chacune, copies de noms, membres numériques, octets d'action copiés et
taille du descripteur concordent avec le décodeur indépendant. Les sources
libres de l'installation personnelle sont exclues explicitement et empreintées.

## Liaison Item → FPV

Les arguments des constructeurs `0x490740`, `0x4907e0`, `0x490800` établissent
un tableau de **500 × 13 × 48 octets**, à partir du membre `0xa0`. Chaque état
contient quatre pointeurs d'animation, quatre noms et quatre valeurs.

Le chemin contrôlé est :

1. `0x7d3ec2` conserve l'identifiant d'emplacement dans l'instance d'objet.
2. `0x4923f8` transmet ce numéro comme troisième argument au sélecteur FPV.
3. `0x49122e` le conserve dans le membre FPV `0x54`.
4. Le chargeur soustrait 100 au numéro de groupe (`0x490eb0`) et 2000 au
   numéro d'état (`0x490f62`).
5. Le consommateur `0x492e21` retrouve la même cellule avec l'emplacement de
   l'objet et l'état demandé.

Ces blocs de liaison sont exécutés avec des objets et pointeurs **synthétiques**,
en arrêtant avant les appels de scène, de modèle ou d'animation. La concordance
est donc une preuve de calcul et de circulation des identifiants, **pas une
preuve de rendu ni de fonctionnement de l'arme**.

Conséquence : le candidat objet **359** exige le groupe **459**, actuellement
absent. Le groupe **109** est la case historique 9, non une ressource utilisable
en réaffectant la boussole. Le groupe 359 existant appartient à la case 259.
Aucun de ces groupes n'est modifié par l'outil et aucun slot n'est alloué.

## Ordre des choix et valeurs FPV

Le lecteur natif itère treize états, puis quatre conteneurs dans **l'ordre du
fichier**. Il ne consomme qu'un premier nom/valeur par conteneur. La projection
native refuse donc les groupes incomplets, canaux réordonnés et multiples
variantes qui seraient correctement structurés mais consommés autrement.

Pour une case `(slot, état, choix)`, les noms sont à
`0xb0 + (13 × slot + état) × 48 + choix × 4`, les valeurs seize octets plus loin.
Le consommateur recherche le premier seuil supérieur ou égal au tirage : ce
ne sont pas quatre poids indépendants à additionner. Les 100 retrouvés dans
les associations Benelli sont des **seuils de sélection**, pas des dégâts,
une durée ni une cadence.

L'import `LS3DF.dll::RandFloat` est identifié à l'IAT `0x80f2d4` ; le code
multiplie son résultat par 100 avant conversion. Les tests injectent des tirages
entiers explicites : ils ne prétendent pas qualifier la distribution ni les
bornes exactes du générateur aléatoire. Les états de gameplay, transitions,
événements sonores et interpolation restent à valider séparément.

## Reproduction et limites

```powershell
.\.venv\Scripts\python.exe tools/item_native_contract.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output .analysis/contrat-natif-nouveau.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_item_native_layout.py
```

Le premier outil exige le cache privé exact dans `tmp/stock-menu-analysis.bin`.
Il ne le fabrique ni ne remplace un cache différent. Un nouveau nom de rapport
est obligatoire. Les sept tests purement synthétiques n'exigent aucun fichier
commercial ; les sept tests avec oracle sont ignorés si le cache privé manque.

Restent avant une entrée jouable : consommateurs de la munition et des
paramètres mécaniques, véritable sérialisation des sauvegardes, fiche additive
de laboratoire, préservation complète de la boussole et essais moteur.
Cette preuve de liaison ne lève pas ces autres exigences de B2–B4.
