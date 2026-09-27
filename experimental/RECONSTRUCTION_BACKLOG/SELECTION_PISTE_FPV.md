# Sélection de piste et préparation de transition FPV

**27 septembre 2026.** Ce contrôle complète les
[poids de transition](TRANSITIONS_POIDS_FPV.md) et
[l'attachement natif](ATTACHEMENT_ANIMATION_NATIF.md).

L'image privée du client 1.12 est épinglée : SHA-256
`2c04629cf79b64c0c12f310187974f357ffbfc22bbc11f1488764cd078d3e7aa`.
Le banc entre soit à `0x493186` (mélange), soit à `0x4931d3` (immédiat),
puis s'arrête à `0x493291`. **La branche d'entrée et la liste d'anciennes
pistes sont fournies explicitement.** La décision amont et l'ajout dans
cette liste ne sont pas exécutés.

## Comportement vérifié

Le clip est lu dans le cache de l'objet FPV à
`0xa0 + objet × 624 + état × 48 + canal × 4`. Ce pointeur chargé précède
de 16 octets la cellule contenant son nom de ressource. Les domaines
contrôlés restent 500 objets, 13 états et quatre canaux.

La branche mélange initialise poids zéro et taux 5 ; la branche immédiate
initialise poids 1 et taux zéro. Le code parcourt ensuite la liste des
anciennes pistes pour choisir le premier emplacement libre parmi **0, 1 et 2**.
S'ils sont tous présents, il choisit **3 sans examiner son occupation**.

Ce dernier cas est conservé dans la référence, pas corrigé silencieusement.
Les 56 témoins synthétiques où 0, 1, 2 et 3 sont présents sélectionnent donc
un emplacement déjà occupé. **Cela ne prouve pas que cet état est accessible
dans le jeu** : les invariants du chemin amont restent à établir. Ne pas
présenter cette observation comme un bogue moteur reproduit.

Les arguments demandés sont : clip sélectionné, emplacement choisi, poids
initial et mode **zéro**, puis rafraîchissement. Ces deux méthodes sont
enregistrées par des doubles, pas exécutées par ce banc. Le banc LS3DF séparé
établit ce que fait l'attachement, notamment la signification du mode zéro,
mais les deux ne constituent pas encore une unique scène chargée.

Seuls le clip/emplacement/taux/poids courants, l'état/canal choisis et la pile
peuvent changer. Cache, liste antérieure et table de méthodes restent intacts.
Limite : 4 096 instructions et une seconde, aucun chargeur ou allocateur.

## Résultats et reproduction

`fpv-native-transition-tail-20260927.json` : **848 cas**, incluant les
256 sous-ensembles des huit pistes et les permutations de 0/1/2/3, les
bornes des cellules ainsi que l'objet 359. Emplacements choisis :
568 fois 0, 128 fois 1, 64 fois 2 et 88 fois 3. Douze tests synthétiques
supplémentaires protègent calculs, refus et limites d'exécution/écriture.

```powershell
.\.venv\Scripts\python.exe tools/fpv_transition_audit.py --image 'tmp/stock-menu-analysis.bin' --json-output '.analysis/selection-piste-nouveau.json'
```

L'image et le rapport sont privés ; un nom neuf est exigé. Aucun jeu ni
installateur n'est lancé. La sélection des états par les actions du joueur,
la décision de mélanger, les ressources réellement chargées et la continuité
visuelle restent des obligations distinctes.
