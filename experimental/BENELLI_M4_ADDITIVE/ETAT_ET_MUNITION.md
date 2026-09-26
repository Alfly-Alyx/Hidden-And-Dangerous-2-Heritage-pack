# Benelli — munition et état d'objet isolé

Contrôle du **26 septembre 2026**, client Sabre Squadron 1.12 exactement
empreinté dans le [contrat natif](CONTRAT_NATIF.md). Aucun lancement du jeu,
chargement de sauvegarde personnelle, écriture dans le jeu ou allocation de slot.

## Liaison arme–munition

Le membre `0x54` du descripteur de type 1 est bien consommé comme identifiant
de munition par l'initialisation d'une arme (`0x7d4bee`). Le moteur consulte
la table des objets, appelle le lecteur du membre `0x54` de la fiche munition
et initialise les quantités courante/maximale de l'instance (`0x50`/`0x54`).
L'exécution isolée s'arrête à `0x7d4c57`, avant les appels de modèle/scène.

| Couche commerciale | Associations arme → munition contrôlées | Référence -1 | Référence non qualifiée |
|---|---:|---:|---|
| Base | 49 | 11 | aucune |
| Patch | 49 | 11 | aucune |
| Sabre | 55 | 11 | 270 → 102, objet de type 2 |
| PatchX01 | 55 | 11 | 270 → 102, objet de type 2 |

**208 associations typées concordent.** Le cas 270 n'est ni forcé dans une
catégorie munition, ni présenté comme validé. Les références -1 sont recensées,
sans exécuter un comportement de grenade, couteau ou arme spéciale.

La munition officielle **179 contient la quantité flottante 7,0** dans les
quatre couches. Une copie **en mémoire seulement** de la fiche Side by Side,
dont cette seule référence est remplacée par 179, initialise bien 7/7 sur
une instance synthétique 359. Ce témoin n'est **pas une fiche historique
Benelli**, une reconstruction de sa mécanique ou une entrée additive installée.
La routine de consommation `0x7d4ab0` soustrait une quantité et borne le résultat
à zéro ; les cas 7→6, 1→0 et 0→0 sont contrôlés sans projectile ni tir.

Cela établit une quantité stockée et consommée, pas encore une capacité réelle
mesurée, un comportement de chargeur tubulaire ou la chronologie du rechargement.

## Enveloppe d'un objet sauvegardé

`tools/item_instance_state.py` est un codec original strict pour **un objet
sans contenu imbriqué**, et non un éditeur de sauvegardes de partie.

L'enveloppe `0xad2c` contient quatre scalaires (identifiant de slot, trois
valeurs opaques de placement), l'état `0x2cc` et les enfants `0x268`, ici vides.
L'état commun `0x2e6b` écrit les tags 100–104. L'état d'arme ajoute onze tags
200–210 ; les deux premiers conservent les quantités courante et maximale.
Les autres valeurs restent des bits bruts tant que leur usage n'est pas prouvé.
Le codec refuse tailles incorrectes, champs inconnus/dupliqués, booléens non
canoniques, enfant imbriqué ou slot hors 0–499.

Les routines natives `0x7de840`/`0x7deb60` écrivent puis lisent respectivement
**224 octets** pour cette arme et **114 octets** pour l'objet générique.
Les slots 255, 256, 359 et 499 ne sont pas tronqués à huit bits. Le lecteur
retrouve les trois scalaires de placement et les onze champs d'arme. Si la
fiche de l'objet manque à la lecture, aucune instance n'est reconstruite :
retirer un mod d'objets n'est donc pas une migration de sauvegarde sûre.

## Asymétrie découverte : ne pas la masquer

Pour le bloc **commun**, l'écrivain émet 102/103 pour les membres `0x24`/`0x20`,
mais le lecteur de ce client attend **202/203** pour les restaurer. Sa table
de dispatch (`0x7d4514`, branches `0x7d43db`/`0x7d43fe`) ignore 102/103.
Le membre `0x20` représente un lien propriétaire sérialisé comme identifiant.

L'oracle expose explicitement cette différence : les données synthétiques
non nulles ne font pas un aller-retour sans perte. Il ne change pas les tags,
ne « répare » aucune sauvegarde et ne modifie pas l'exécutable. Un second
témoin prouve que 202/203, placés **dans le conteneur commun**, sont bien lus.
Ils ne doivent pas être confondus avec les tags 202/203 de l'état d'arme,
qui ont un autre propriétaire et d'autres membres.

Ce résultat local ne démontre pas à lui seul une perte de lien dans une partie
complète : des étapes d'initialisation ou de rattachement extérieures peuvent
intervenir. Il impose de conserver la validation globale ouverte.

## Isolation, reproduction et limites

`tools/item_state_oracle.py` utilise le même cache commercial privé vérifié
que l'oracle de descripteurs. Les entrées/sorties sont des doubles limités
à **un tampon de 32 Kio en mémoire**. Fabriques d'instances, registre et
recherche de propriétaire sont synthétiques ; leurs fonctions natives, les
modèles, l'IA, le réseau et les appels Windows ne sont pas exécutés.

```powershell
.\.venv\Scripts\python.exe tools/item_state_oracle.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output .analysis/etat-munition-nouveau.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_item_instance_state.py
```

Quatorze tests couvrent le codec, les refus, les tampons isolés, la conservation
des slots/états, les références de munition et l'asymétrie. Six sont purement
synthétiques ; les huit autres exigent le cache privé exact, non redistribué.

**Toujours non qualifiés :** format complet des sauvegardes, inventaires
imbriqués, instances de munition, vrais constructeurs, ordre des propriétaires,
rechargement, mécanismes de tir et migration/retrait du mod. Les indicateurs
`whole_saved_game_qualified`, `live_reload_qualified` et `item_slot_allocated`
restent faux. Ces preuves permettent de préparer la suite, pas d'activer B2–B4.
