# Africa3 — synchroniseurs manquants

État : **deux bindings fossiles, aucune restitution historique possible**, 14
septembre 2026. La mission commerciale reste intacte.

## Verdict

Le registre effectif contient 84 bindings et désigne deux fichiers absents :

| Propriétaire enregistré | Fichier attendu | Verdict |
| --- | --- | --- |
| `AF3a_14_lookAF15` | `AF3a_1415synchronizer.scr` | ancienne architecture très probablement remplacée par la conversation 14/15 active |
| `AF3a_22_look1_01` | `AF3a_2223synchronizer.scr` | comportement irrécupérable ; seule une coordination moderne distincte est étudiable |

Une recherche sur 214 entrées Africa3 de `Scripts.dta`, `Patch.dta` et
`SabreSquadron.dta` ne trouve aucun des deux noms. Le registre de
`missions.dta` est leur seule trace commerciale locale. Le périmètre
communautaire communiqué ne fournit pas davantage les fichiers.

## 14/15 — conversation déjà remplacée

La release possède une chaîne complète et liée :

- `dummy_rozhovor_02_activator -> AF3a_rozhovor_02_activator.scr` ;
- `dummy_rozhovor_02 -> AF3a_rozhovor_02.scr` ;
- le contrôleur attend le joueur et la présence de `AF3a_14`, puis lance la
  conversation ;
- les voix 07991515 à 07991535 sont distribuées entre les deux soldats ;
- le signal 9 arrête les activités et tourne chacun vers l'autre ;
- les signaux 10 et 11 démarrent puis arrêtent les animations de parole ;
- le signal 12 rend aux deux acteurs leur activité normale ;
- mort ou alarme envoie le signal 2 au contrôleur et coupe les voix.

Le frame `AF3a_14_lookAF15`, propriétaire du binding manquant, sert déjà de
cible de regard aux deux scripts d'acteur. Son transform le place à 3,11 unités
de 14 et 1,16 unité de 15. Il ressemble donc à un vestige d'une implantation
ancienne, mais son nom et sa position ne révèlent pas le code perdu.

**Décision :** ne pas recréer `AF3a_1415synchronizer.scr`, ne pas ajouter un
second contrôleur et ne pas réaffecter le point de regard. Toute nouvelle
séquence doublerait potentiellement regards, animations et voix que la release
orchestre déjà.

## 22/23 — données qui subsistent

Les deux soldats sont officiels et proches :

| Frame | Position commerciale `(x, y, z)` |
| --- | --- |
| `AF3a_22` | `(14.524426, 0.057373, -32.377998)` |
| `AF3a_23` | `(15.959481, 0.017068, -31.614790)` |

Leur distance est d'environ 1,63 unité. `AF3a_22.scr` déclare `AF3a_23` sans
l'utiliser ; `AF3a_23.scr` déclare symétriquement `AF3a_22` sans l'utiliser.
Le premier boucle sur `%%mina`, le second joue `%%mina2` avant de rejoindre sa
position assise. Aucun dialogue, identifiant vocal ou échange de signal entre
eux ne subsiste.

Le propriétaire fossile `AF3a_22_look1_01` est à environ 48,96 unités de chacun
des deux acteurs. Les scripts actuels ne le recherchent pas et ne possèdent que
le gestionnaire de signal 20, réservé à leur passage en réaction de combat.

Le synchroniseur commercial survivant de 05/06 n'est qu'un analogue : il exige
les deux soldats à moins de six unités de son propriétaire et envoie deux
phases par signaux 1 et 2. Copier ce code pour 22/23 échouerait avec le point
fossile lointain et avec des acteurs qui ne traitent pas ces signaux.

## Surface moderne autorisée

Une éventuelle variante s'appelle par exemple
`Africa3 — coordination 22/23 (test)` et ne réutilise pas le nom du fichier
perdu. Elle reste désactivée par défaut et séparée de la conversation 14/15.

Le concept minimal est limité à un seul cycle de travail coordonné, sans voix :

1. un nouveau contrôleur **MODERNE** près du milieu des acteurs, autour de
   `(15.242, 0.037, -31.996)` ;
2. des copies expérimentales des deux scripts, car les scripts release ne
   reçoivent aucun signal de synchronisation ;
3. un protocole de départ et d'abandon réservé, dont les numéros de signaux ne
   sont choisis qu'après audit global ;
4. réutilisation exclusive des animations déjà attestées `%%mina` et
   `%%mina2`, une fois chacune ;
5. abandon immédiat au premier mort, à l'alarme ou au passage en combat, puis
   retour aux comportements release ;
6. aucun sous-titre, aucune voix ni aucun objectif ; si le test exige un
   monostable persistant, sa nouvelle valeur sauvegardée est allouée après
   audit, versionnée et marquée **MODERNE**, jamais présentée comme historique.

Ce concept ne reconstitue pas `AF3a_2223synchronizer.scr`. Il teste seulement
si la déclaration réciproque inutilisée peut soutenir une mise en scène moderne
cohérente. Le protocole détaillé est dans
[`PROTOCOLE_22_23.md`](PROTOCOLE_22_23.md).

## Interdictions

- ne jamais attacher un fichier inventé à `AF3a_14_lookAF15` ;
- ne pas lancer deux contrôleurs sur 14/15 ;
- ne pas copier le synchroniseur 05/06 sous un nouveau nom sans récepteurs ;
- ne pas attribuer de dialogue perdu à 22/23 ;
- ne pas modifier les scripts release d'Africa3 ;
- ne pas présenter le point milieu moderne comme le transform original.

## Sources internes

- `missions.dta : MISSIONS\AFRICA3\scripts.dta`, `actors.bin`, `scene2.bin` ;
- `Scripts.dta` et `Patch.dta : SCRIPTS\AFRICA3\AF3a_14.scr`,
  `AF3a_15.scr`, `AF3a_22.scr`, `AF3a_23.scr`,
  `AF3a_rozhovor_02.scr`, `AF3a_rozhovor_02_activator.scr`,
  `_inc_rozhovor.scr`, `AF3a_0506synchronize.scr` ;
- `.analysis/af3-sync-search.json` ;
- audit effectif `tools/script_binding_audit.py --mission Africa3`.
