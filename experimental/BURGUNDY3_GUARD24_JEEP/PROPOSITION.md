# Burgundy 3 — garde 24 et Jeep SAS

État : **vestige contradictoire et incomplet**, 14 septembre 2026. Aucun
embarquement, trajet ou HUMAN_Kill n’est activé.

## Preuves conservées

Le registre Burgundy 3 relie BUR03_24 à bur3_24.scr et la_Jeepsas_01 à
bur3_jeepsas.scr. Le Jeep existe donc comme acteur lié, même si son record
d’acteur n’est pas disponible dans l’extraction spatiale actuelle.

Le script de la garde solo conserve quatre groupes commentés :

- embarquement dans la_Jeepsas_01 au siège 0 lors de ACTIVATE ;
- arrêt de conduite puis débarquement si incar est vrai pendant OnAlarm ;
- conduite vers car05 à vitesse 100 ;
- HUMAN_Kill(this) après le trajet.

La variable incar est néanmoins mise à 1 même quand l’embarquement est commenté,
puis remise à 0 à l’alarme. Le squelette est donc partiellement resté actif.

Le contrôleur bur3_jeepsas.scr tourne le capot Object03 de 330 degrés puis fixe
le carburant du Jeep à 0 « pour que personne ne le conduise ». Cette mise en
scène de véhicule immobilisé contredit une restauration directe de la conduite.

Enfin, la section véhicule du check2 Burgundy 3 contient zéro point et aucun nom
car05. La destination de conduite et sa route n’existent donc pas dans la
mission commerciale auditée.

La variante Co_Burgundy3 retire entièrement embarquement, incar, conduite et
HUMAN_Kill ; elle ne complète pas le contrat solo.

## Deux intentions possibles, jamais à fusionner

### H1 — occupant d’ambiance

La garde devait peut-être être assise dans le Jeep, puis arrêter/débarquer à
l’alarme. Cette hypothèse utilise les lignes du bloc incar mais laisse car05 et
HUMAN_Kill désactivés. Elle doit encore prouver que le siège 0 accepte un humain
et que Car_SetFuel(0) n’empêche pas la prise de place.

### H2 — trajet sacrificiel

La garde devait peut-être rester dans le Jeep, conduire vers car05 puis mourir
pour mettre en scène un accident ou une destruction. Cette hypothèse exige une
route véhicule moderne complète, une destination, l’état du Jeep, le motif de
HUMAN_Kill et les effets attendus. Elle est beaucoup plus spéculative.

Les lignes d’arrêt/débarquement et de conduite/kill sont contradictoires si on
les exécute séquentiellement : HUMAN_Drive(car05) arriverait après le débarquement.
Elles représentent donc probablement des alternatives de développement.

## Verdict de reconstruction

Aucun prototype script n’est recevable à ce stade. VARIANTS.plan.disabled
sépare H1 et H2 et fixe leurs preuves manquantes. H1 peut devenir un premier
banc statique, sans moteur ni kill, uniquement après inspection du siège et des
collisions. H2 reste bloquée jusqu’à découverte d’une source de car05 ou création
assumée d’un graphe véhicule moderne.

## Tests futurs

Pour H1 : tester pose, entrée/sortie, capot tourné, carburant nul, alarme, mort,
sauvegarde et occupation concurrente. Le Jeep ne doit jamais rouler.

Pour H2 : vérifier d’abord un check2 véhicule complet dans une copie, puis
conduite, obstacles, fin de route, raison du kill, effets/objectifs, alarme,
destruction anticipée, conducteur mort et reprise. Aucun test H2 ne réutilise le
script H1 ni ne modifie le Jeep commercial de référence.

Retour arrière : restaurer script, registre d’essai et éventuel check2 ensemble.
La mission stable reste inchangée.

