# Czech 2 — placement des joueurs dans les anciens scripts

État : chaîne documentée, initialisation et déclenchement à établir, 25 septembre 2026.
Aucune affectation de script ni téléportation n'est ajoutée au jeu.

## Faits commerciaux

Les quatre `player1assign..4.scr` et les quatre `startscriptengl1..4.scr` existent
dans Scripts.dta, mais aucune de ces huit sources n'a de liaison au registre.
L'audit part de 81 scripts racines et en atteint 83 sur 97 disponibles; les deux
sources de la première paire ne sont pas accessibles depuis ces racines.

Chaque ancien assigner déclare sa frame player puis lui affecte le script de
placement dans `OnUse`, sans initialisation explicite de cette frame. Affecter
ces scripts à des objets arbitraires ne résout pas l'identité du joueur concerné.
Le premier script de placement réagit à **la cinématique 1**, marche vers `en1`
puis, dans `OnCutsceneDone(1)`, téléporte près de `en1/Ger1_1`, regarde `Ger_1`
et termine. Les noms `en1..4` et `Ger1_1` sont bien présents dans le Check2 Patch;
cela ne prouve pas la navigation ou l'absence de collision entre quatre joueurs.

La séquence commerciale liée `cut2.scr` réagit, elle, à **la cinématique 2** :
elle choisit le joueur le plus proche de son porteur, crée un double, cache le
joueur, puis libère le double et réaffiche le joueur à la fin. Ce ne sont donc
pas automatiquement deux implémentations du même événement. Le mécanisme cut2
doit rester intact; aucune scène ancienne n'est substituée à son déroulement.

## Provenance minimale

| Scripts.dta, `scripts/czech2/` | Octets | SHA-256 |
|---|---:|---|
| `player1assign.scr` | 88 | `4cbf72f1777c0d87eb8ea030995f713913847ea286fa4e054757a6c2365bae06` |
| `startscriptengl1.scr` | 407 | `897e19c91c9c9181f1141835482313ce42a5064772b9d97804796fcb72e27fde` |
| `cut2.scr` | 2032 | `ac738c9cf1bbb87d2c2da20645a7f70b4d02160c775e23d9873805c69362bd50` |

Check2 Patch : 49728 octets, SHA-256
`beac21f84e5cfd921b098ee7b648291cb23c35f72a805c5467bf74a91e169f17`.

## Contrat nécessaire

Une variante moderne devra désigner avant chargement le contrôleur unique de
placement, les joueurs effectivement vivants, les scripts déjà affectés et leur
restauration après sortie. Ne pas remplacer leur script actif sans ce contrat.
L'événement 1 doit être observé séparément de l'événement 2, avec une à quatre
personnes, morts antérieures, changement de sélection, interruption et reprise.
Ne téléporter chaque joueur qu'une fois; ne jamais confondre joueur réel et double.
Les checkpoints seuls ne suffisent pas à produire un prototype complet sûr.
