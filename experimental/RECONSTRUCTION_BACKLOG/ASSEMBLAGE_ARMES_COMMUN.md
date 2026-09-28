# FG42, MG34 et ZK-383 : préparation commune désactivée

**28 septembre 2026.** Les trois armes peuvent maintenant être réunies dans
une seule paire de tables privées. Ce travail supprime un conflit de préparation :
copier successivement les tables de trois laboratoires indépendants aurait
conservé seulement les ajouts du dernier. **Aucune arme n'est déclarée jouable.**

## Fusion et retrait

`tools/rigid_weapon_bundle.py` vérifie les trois laboratoires, leurs empreintes
et leurs reçus de retrait, puis reconstruit leurs tables d'origine. Ces deux
tables doivent être **strictement identiques** dans les trois entrées. La variante
de mains et la couche d'archives doivent aussi être les mêmes.

Les ajouts sont rejoués en mémoire : FG42 362/groupe 462, MG34 363/groupe 463,
puis ZK-383 364/groupe 464 et sa munition distincte 365. La munition ne reçoit
pas de groupe FPV. Les quatre records consomment 2 016 octets de réserve sans
changer la capacité de 500 emplacements ni les anciens objets/groupes.

Les textes, sons et autres ressources portant le même nom doivent avoir les
mêmes octets ; une différence, même de casse Windows, est refusée. Rien n'est
écrasé selon l'ordre des entrées. Les tables d'objets et FPV sont les seules
ressources reconstruites. Le retrait inverse les trois transactions et restitue
exactement les instantanés communs. Toute modification ultérieure des résultats,
de l'ordre, des identifiants ou des types du reçu provoque un refus.

Ce reçu concerne les deux tables en mémoire, **pas une transaction de déploiement
sur disque**. Les reçus de textes et de sons restent disponibles dans les
manifestes d'entrée inclus dans le manifeste commun.

## Première construction vérifiée

Le dossier privé `.analysis/item-table-labs/FG42_MG34_ZK383_Current_H_v1`
réunit :

- `FG42_Tables_Current_H_v3`, reconstruit avec les cinq libellés communs ;
- `MG34_Tables_Current_H_v2`, utilisant les mains v10 corrigées ;
- `ZK383_Tables_Current_H_v1`, utilisant la prise droite candidate v9.

Il contient **61 fichiers : 59 charges désactivées, un manifeste et un avertissement**.
Les 272 objets et 277 groupes existants restent intacts, y compris les dix
objets et six groupes modifiés dans les instantanés personnels. Le résultat
compte **276 objets et 280 groupes**. Les huit tables de textes sont partagées
par les trois armes ; quatre WAV originaux et leur définition sonore sont
partagés par FG42/ZK-383, soit **13 ressources communes identiques**.

| Table commune | Taille | SHA-256 |
|---|---:|---|
| Objets | 252 000 | `7e85477a30fd7d8576382e3bc3860e0730076cd2b2ce38f6ecbefa692c247127` |
| Animations FPV | 130 227 | `fa033699bdae94c5fb43e5d73c6886d35564a72b0021ef03f998b4b661f7d60c` |

Le constructeur exécute les lecteurs natifs isolés sur les **276 descripteurs**,
les deux tables, **117 demandes de ressources** et **27 chargements d'animations**.
Chaque arme doit demander exactement ses neuf clips. Ces sous-systèmes restent
dans des émulateurs distincts : aucun modèle de scène, copie de mains, rendu,
événement, sauvegarde, réseau ou fonctionnement simultané en jeu n'est validé.

## Reproduction et limites

```powershell
.\.venv\Scripts\python.exe tools/build_rigid_weapon_bundle_lab.py --fg42 FG42_Tables_Current_H_v3 --mg34 MG34_Tables_Current_H_v2 --zk383 ZK383_Tables_Current_H_v1 --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --output-name TroisArmes_Nouveau
```

Les noms désignent uniquement des enfants de `.analysis/item-table-labs`.
Liens, chemins sortants, fichiers actifs, fichiers non listés et empreintes
modifiées sont refusés. Les entrées sont relues avant toute écriture de sortie ;
le dossier de sortie doit être neuf. Les binaires dérivés commerciaux restent
privés et exclus de Git.

Les sources sont des **instantanés préparés**, non une nouvelle vérification
de l'installation courante. Les autres surcharges de ressources ne sont pas
fusionnées. Benelli, lance-flammes et Garota ne sont pas inclus dans ce lot.
Les défauts de transitions, gestes de mains, caméra, raccordements moteur,
événements et comportements restent des travaux d'implémentation/qualification.
**Ne pas copier ces fichiers dans le jeu.**

Sept tests synthétiques contrôlent les quatre couples couche/variante,
la conservation et le retrait des quatre ajouts, les sources divergentes,
les conflits de ressources, les mutations de reçus, les limites de chemins
et la vérification des 27 clips. Ils n'embarquent aucun fichier commercial.
