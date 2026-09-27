# Sélection de piste et préparation de transition FPV

**27 septembre 2026.** Ce contrôle complète les
[poids de transition](TRANSITIONS_POIDS_FPV.md) et
[l'attachement natif](ATTACHEMENT_ANIMATION_NATIF.md).

L'image privée du client 1.12 est épinglée : SHA-256
`2c04629cf79b64c0c12f310187974f357ffbfc22bbc11f1488764cd078d3e7aa`.
Le banc entre soit à `0x493186` (mélange), soit à `0x4931d3` (immédiat),
puis s'arrête à `0x493291`. **La branche d'entrée et la liste d'anciennes
pistes sont fournies explicitement.** La décision amont et l'ajout dans
cette liste ne sont pas exécutés par ce premier banc ; leur contrôle séparé
est décrit plus bas.

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
les ressources réellement chargées et la continuité
visuelle restent des obligations distinctes.

## Décision amont et copie de la piste précédente

Le nouveau `fpv_transition_decision_oracle.py` entre à `0x492f8e` et exécute
la décision cliente ainsi que `IsAnimationActive` (`0x10034600..0x1003462b`)
dans la DLL épinglée. L'activité est lue dans un contrôleur synthétique ; elle
n'est plus remplacée par une réponse de méthode simulée. La capacité de la
liste est préparée avec une place libre, ce qui exclut son agrandissement.

En l'absence de clip, le chemin immédiat ne consulte pas l'activité. Un clip
inactif ou un contrôleur absent entraîne aussi le chemin immédiat. Un clip
actif est copié par les instructions natives dans la liste précédente : ses
16 octets (identifiant, piste, taux et poids) sont conservés, **y compris un
taux nul**. Le nouveau clip commence alors à poids zéro et taux 5. Les anciens
enregistrements et le contrôleur restent intacts. La recherche de piste garde
la règle 0/1/2 puis 3 non vérifié, sans correction silencieuse.

Rapport privé `.analysis/fpv-transition-decision-20260927.json` : **3 112 cas**,
**2 852 consultations natives**, **1 308 ajouts natifs**. Objets 0/359/360/361/499,
13 états, quatre canaux, tous les sous-ensembles distincts de pistes précédentes
pour chacun des huit emplacements courants, et permutations de 0/1/2/3. Les
152 sélections synthétiques de la piste 3 déjà occupée ne prouvent toujours pas
qu'une telle collision est accessible dans une partie. Onze tests supplémentaires
protègent les références et gardes d'exécution/écriture.

L'attachement et le rafraîchissement restent enregistrés par des doubles dans
ce banc ; l'allocateur est interdit, pas simulé. Le
[banc de lecture persistante](ENCHAINEMENT_ANIMATIONS_NATIF.md) exécute ensuite
attachement/poids/lecture dans une autre instance, avec un calendrier explicite.
Les deux preuves ne constituent pas encore la chaîne cliente complète.

```powershell
.\.venv\Scripts\python.exe tools/fpv_transition_decision_audit.py --image 'tmp/stock-menu-analysis.bin' --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/decision-transition-nouveau.json'
```
