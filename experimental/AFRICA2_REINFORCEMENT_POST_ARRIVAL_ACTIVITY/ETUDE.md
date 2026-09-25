# Africa 2 — activités des quatre renforts

État : flux commercial documenté, activité moderne à concevoir après observation,
25 septembre 2026. Aucun trajet de camion ni animation n'est ajouté.

## Le commentaire ne se trouve pas après l'arrivée active

Les quatre scripts `AF2_posily_01..04.scr` sont liés à leurs acteurs existants.
Ils contiennent bien `Label ACTIVITY: // doplnit`, mais leur activation actuelle
sur signal 1 rejoint `ACTIVATE`, se réveille, configure les alarmes, marche vers
`p01_01..p04_01`, puis saute directement à END. **Elle n'entre pas dans ACTIVITY.**
Remplir seulement ce commentaire ne produit donc aucune nouvelle activité à
l'arrivée normale. `OnAlarmDone` y conduit, mais les handlers d'alarme appellent
aussi `EndScript`; leur vie effective doit être observée, pas présumée.

Les anciens labels MOVE des passagers 02/03/04 passent par un embarquement
sièges 1/2/3 avant de tomber dans ACTIVITY. Une activité debout ajoutée aveuglément
à ce label pourrait ainsi s'exécuter alors que le personnage est encore embarqué
si cette ancienne route était réactivée.

## Le camion possède déjà son remplacement

`dummy_posily_activator` est lié au contrôleur Patch effectif. Celui-ci sélectionne
un déclenchement à 590 unités avec test de véhicule ou à 370 unités, puis anime
l'Opel avec `#afr2carcrash.i3d` et `#afr2carcrashs.i3d`. Il active l'effet de mine,
cache le faux conducteur, change l'état de la collision et envoie les quatre
signaux 1. Une autre condition tue les renforts avant activation si la valeur
de campagne 50 est déjà vraie. Ces branches ne doivent pas être doublées.

Le conducteur 01 conserve un ancien parcours `AF2_car01/02/03` derrière un
`goto END` et une note de retrait. Ce trajet n'est pas une activité manquante à
restaurer en parallèle de l'animation du contrôleur.

## Preuves des sources effectives

Tous les scripts ci-dessous proviennent de Patch. Le registre commercial fait
2993 octets, SHA-256 `25b04862dcd9d7c1d0485b913e67579b3f91dc1f7c47bf731fa394dfc279af9d`;
les acteurs 18421 octets, SHA-256 `fe57e4a975505d1cd7ac47f2cf29fa196431cea7dcf5baf82174edf6f12a07c3`.

| Script | Octets | SHA-256 |
|---|---:|---|
| `AF2_posily_01` | 2316 | `f16aac35330728fc5896e80c91ea8cfcb9b316f8321eb7cf4c6cb438c19ae16d` |
| `AF2_posily_02` | 1638 | `da23e8a48498a26a961093dc0c488fa0d50922014954b80413ef4a2181c00e17` |
| `AF2_posily_03` | 1636 | `3ceee8657d932263e494c752e08dd7bfd6804af56237f87b878ff5fb7e1f499f` |
| `AF2_posily_04` | 1669 | `4be25f900cb641877219e45353017fcea9d131dd277512476ad4f6ec18d13d95` |
| `AF2_posily_activator` | 2221 | `13e7a4dc954a5a3c3036a4c6c0754e3720178a7281111a630ba769ed9996553e` |

## Proposition moderne limitée

Une variante future peut remplacer le saut END **après le déplacement à pied**
par une entrée d'activité dédiée, propre à chaque acteur. Ne pas réutiliser MOVE,
faire apparaître un camion supplémentaire ou inventer un second signal 1.
La posture, la durée et le regard ne sont pas attestés par « doplnit » : les
choisir depuis les positions finales observées, les marquer MODERNE et interrompre
l'activité proprement sur alarme ou mort. Le témoin conserve ses fins actuelles.

Essais préalables : quatre arrivées sans blocage, déclencheurs 590/370, valeur 50
avant et pendant activation, mort précoce, alarme pendant la marche, véhicule
occupé, sauvegarde/reprise et fin de mission. Sans observation du retour de
`HUMAN_Move` et des sorties d'alarme, aucun nouveau profil complet n'est fourni.
