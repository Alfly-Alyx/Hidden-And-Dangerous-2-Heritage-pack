# Sélection native des cibles et préparation des canaux

**27 septembre 2026.** Ce contrôle complète le plan de noms Benelli et les
banques modernes FG42/MG34. Il utilise la même `LS3DF.dll` épinglée que le
[calcul natif](CALCUL_ANIMATION_NATIF.md), sans la charger sous Windows.

Le banc ultérieur d'[attachement natif](ATTACHEMENT_ANIMATION_NATIF.md)
exécute désormais la liaison, le redémarrage et le retrait complets avec
allocation de cibles simulée et bornée. Les résultats historiques ci-dessous
restent ceux des deux blocs séparés ; aucun chargement réel n'en découle.

## Deux blocs indépendants, pas un chargement complet

**Sélection de cible : `0x10020320…0x100203c1`.** Le code parcourt une liste
de nœuds fournie explicitement. Les noms CP1252 sont comparés octet par octet,
avec sensibilité à la casse et à la fin de chaîne. Le premier nom égal gagne.
Les doublons sont donc détectés et refusés par notre audit de banque, même
si le parcours natif sélectionnerait le premier. Une liste vide et un nom
introuvable sont des résultats distincts d'un succès.

Les deux branches de conteneur examinées utilisent respectivement le type 9
et un type témoin 0. Cela démontre leurs lectures de liste, pas la validité
de tout type d'objet possible. Le banc fournit des pointeurs de noms non nuls,
avec décalage signé égal à zéro ; il ne prétend pas qualifier le chargeur de
chaînes. Il s'arrête avant l'appel à `0x10020740` qui attache/alloue une cible.

**Préparation de canaux : `0x100203ce…0x1002048c`.** À partir du bloc 5DS
en mémoire, le code écrit dans un descripteur inventé les drapeaux, comptes
et pointeurs de rotation, position et échelle. Les comptes absents sont mis
à zéro, sans inventer de clés. L'ordre rotation → position → échelle et les
alignements sont confrontés au lecteur de format indépendant. Les données
d'événements restent hors domaine et sont refusées en amont.

Les huit emplacements espacés de `0x1c` sont examinés. Aucun appel de scène,
de chargement, d'allocation ou d'attachement n'est exécuté. L'entrée demeure
en lecture seule, les écritures limitées à la pile et au descripteur choisi.
Budget : 100 000 instructions et une seconde par calcul. La page d'entrée
de 64 Kio borne les noms et le bloc de données ; toute sortie du domaine
ou de la liste d'instructions revue provoque un refus.

## Résultats

Le rapport privé `native-animation-binding-v2-20260927.json` conserve les
empreintes et comptes suivants, sans exporter de géométrie ou de clés :

| Banque et cibles explicites | Séquences | Pistes | Sélections natives | Descripteurs natifs |
|---|---:|---:|---:|---:|
| Benelli + fpv_hands, 45 cibles | 9 | 224 | 448 | 1 792 |
| Benelli + fpv_hands_r, 45 cibles | 9 | 224 | 448 | 1 792 |
| FG42 moderne, 33 cibles | 9 | 27 | 54 | 216 |
| MG34 moderne, 42 cibles | 9 | 36 | 72 | 288 |
| Total des corpus | 36 | 511 | **1 022** | **4 088** |

Chaque piste est sélectionnée dans les deux conteneurs, puis son descripteur
vérifié dans les huit emplacements. Les deux variantes de mains réutilisent
les mêmes neuf clips Benelli : **36 passages ne sont pas 36 clips distincts**.
Les banques modernes sont reconstruites en mémoire depuis leurs recettes
publiques, sans modifier les ressources privées v3 ou leurs aperçus.

Vingt-deux contrôles natifs inventés couvrent en plus : casse, préfixes,
accents CP1252, doublons, absence, listes vides et limite de 128 cibles dont
les noms peuvent atteindre 63 octets. Neuf tests de dépôt couvrent les
références, les bornes et les refus de reçus incomplets ; ils ne nécessitent
aucune bibliothèque commerciale.

## Ce que cela ne prouve pas

Les cibles mains/arme sont réunies **dans le banc**, pas par un chargeur réel.
La construction effective de cette liste par le client, les identités des
objets, leurs attaches, le choix et la durée de vie des pistes, les poses
supplémentaires, le skin et les callbacks ne sont pas qualifiés.
Le champ `actual_model_attachment_qualified` reste donc faux, comme les
indicateurs de jouabilité et de validation moteur des prototypes.

L'[assemblage de poses synthétiques](POSES_PARTIELLES_NATIVES.md) est un autre
contrat : une correspondance de nom ne suffit pas à prouver l'origine de
l'état conservé lorsqu'un canal manque.

```powershell
.\.venv\Scripts\python.exe tools/animation_binding_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/liaison-animation-nouvelle.json'
```

Rapport neuf obligatoire ; aucune installation ou partie lancée.
