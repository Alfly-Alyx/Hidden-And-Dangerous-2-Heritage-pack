# Africa 4 — orientation du passager 09

État du 25 septembre 2026 : **documenté, cible historique non retrouvée**.
Ne pas décommenter `HUMAN_TurnAt(dummy_turnat)` : la variable n'est pas déclarée
dans le script du passager 09. Aucune frame ni orientation inventée.

## Comparaison effective Patch

| Acteur | Siège d'Opel02 | Cible déclarée pour `dummy_turnat` |
|---|---:|---|
| AF3b_06 | 0 | `m_AF3_bar_ohen_17` |
| AF3b_07 | 1 | `m_palma` |
| AF3b_08 | 2 | `m_palma15` |
| AF3b_09 | 3 | aucune; appel commenté |
| AF3b_10 | 4 | `dummy_group01_turnat` |

Les voisins ne désignent donc pas une cible commune qui pourrait être recopiée
chez 09. Les frames `m_palma15` et `dummy_group01_turnat` existent dans la scène,
mais cela ne les attribue pas à ce passager.

Le garde 09, son binding, Opel02 et le checkpoint `AF3b_09_01` sont présents.
Sa sortie commerciale reste complète : quitter le siège 3, réactiver les
alarmes sauf le masque 768, attendre trois secondes, rejoindre son point,
s'accroupir, attendre 100 ms puis `HUMAN_LookAround(2)`. Ce regard circulaire
reste actif malgré le `TurnAt` commenté. La retraite 22, l'alarme et la
notification de décès au coordinateur restent inchangées.

Le module Heritage `Africa4DormantInfantryInstaller` réactive déjà les lignes
de suspension/événements après embarquement de 09. Ce travail distinct n'est
pas dupliqué ici; l'étude porte uniquement sur l'orientation finale manquante.

## Décision et tests préalables

Retrouver une cible historique attribuée, ou choisir une orientation **MODERNE**
après mesure de la position finale, de l'axe d'assaut et des lignes de vue.
Le numéro du siège ou la proximité d'une frame ne suffit pas.

Observer les cinq débarquements et la direction réelle de 09. Une éventuelle
variante ne devra changer ni route ni délai, et devra tester alarme pendant
rotation, retraite, mort et sauvegarde. Ne pas ajouter de pause ni supprimer
`LookAround` sans mesurer leur interaction. Aucun prototype complet à ce stade.

## Provenance

`af3b_09.scr`, Patch.dta : 1985 octets, SHA-256
`17a378b8ec84dc0b081f13de98ab2a97096707e29261d24f2770e642e3d70a6c`.
Voisins relus : 06–10 effectifs Patch. Sources de mission :

| Fichier | Source | SHA-256 |
|---|---|---|
| scripts.dta | Base | `bfee17872d0aae55afebbe9ebd007450f2482a78ebea2d6889ba57c96727181e` |
| actors.bin | Patch | `2d6392bef32cd15ebbb26eda6398360b07c993c54a59c4c4b61b954b4ce57b0a` |
| scene2.bin | Base | `14dd52086b2c56cdde594b265e843841979911d1ae1627fd353a02ae955c0c72` |
| check2.bin | Patch | `1b59f0fd53a6569f6b3e9820768090629ebac09d16c1e6cd1f5849f007890f5b` |

Preuves issues des archives; aucune modification de l'installation actuelle.
