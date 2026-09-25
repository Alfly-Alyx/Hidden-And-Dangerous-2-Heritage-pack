# Libye 3 — alarmes du conducteur pendant le trajet du Panzer

État du 25 septembre 2026 : **variante historique désactivée**, construite depuis
Sabre Squadron et contrôlée hors jeu. Le profil commercial reste le défaut.
Il s'agit de deux lignes officiellement présentes mais commentées, pas d'un
comportement livré ni d'un correctif déclaré nécessaire sans comparaison en jeu.

## Chaîne commerciale vérifiée

`Li3_German_Con_1` est lié à son script et monte au siège 0 de
`la_Panzer IIIAf_1`. Il se suspend, puis son signal 1 le réveille et lance les
trajets `CON_4` à 40, `CON_5`/`CON_107`/`CON_108` à 50, puis l'arrêt avec
`HUMAN_Drive("", 0)`. Les quatre checkpoints sont nommés une fois chacun dans
`check2.bin`.

Le contrôleur `Li3_Cargo.scr`, lié à `w_explosive_2`, masque initialement le
char. À l'état 2 du cargo, il réalise la chaîne commerciale, révèle le char et
envoie le signal 1 au conducteur et à d'autres acteurs avant de terminer.
La variante ne change aucun élément de cette chaîne.

Comparaison de l'équipage :

| Acteur | Fonction du script | Masque d'alarme commercial |
|---|---|---|
| Con_1 | siège 0 et quatre segments de conduite | lignes false/true commentées |
| Con_2 | siège 1, opérateur | 1023 true actif, pas de trajet |
| Con_5 | siège 2 | 1023 true actif, pas de trajet |
| Con_3 / Con_4 | fantassins : routes CI à pied | 1023 true actif |

Les scripts 2/5 ne sont donc pas des conducteurs alternatifs. Leurs alarmes
restent actives dans la variante; on ne neutralise pas tout le char. L'alarme
du conducteur commercial passe en mode agressif et termine son script : elle
peut théoriquement interrompre le trajet, mais cette conséquence demande une
observation en moteur.

## Modification exacte et preuves

Le profil `libye3-panzer-driver-alarm-gate` du
[catalogue reproductible](../reconstruction-variants.json) retire seulement
les deux préfixes de commentaire :

- `SetAlarmType(1023, false)` avant l'embarquement et la suspension;
- `SetAlarmType(1023, true)` après le dernier appel d'arrêt de conduite.

Pas de nouveau signal, compteur, délai, route, vitesse ou handler. Les sept
sources sont épinglées : conducteur, opérateurs 2/5, contrôleur cargo, registre,
acteurs et checkpoints. Liaisons et présence du conducteur, du véhicule et du
propriétaire cargo sont vérifiées.

Source : 1125 octets, SHA-256
`c4eddcfab4deb0fd26cd2320e3440746b5e97734e405169564541f297f3f9e48`.
Sortie : **1121 octets**, SHA-256
`7e3ddec85b59630239f97f1edfcc28d250e457c04f92a5c7564c97a2cd6ac21c`.
Le laboratoire inerte conserve 85 fichiers, 73 scripts accessibles et six
objectifs par branche. Deux tests de contrat et l'inspection du diff confirment
la portée textuelle de la modification; ils ne simulent ni conduite ni alarmes.

## Risque principal et protocole A/B

Le masque false commence **avant** le signal de départ. S'il n'arrive jamais,
si un trajet n'aboutit pas ou si la conduite est interrompue autrement, la ligne
de réactivation peut ne jamais être exécutée. Aucun timeout moderne n'est
inventé pour dissimuler cette limite de la séquence historique.

1. Observer le témoin avant destruction du cargo, puis pendant le trajet et
   après l'arrêt : visibilité du char, activation et réactions des trois sièges.
2. Comparer la variante sur le même parcours sans alarme; ordre et vitesses
   doivent rester identiques.
3. Déclencher tir proche, dégâts et explosion à chaque segment. Vérifier que
   les opérateurs gardent leur réaction et que le conducteur retrouve ses
   réactions après l'arrêt.
4. Tester route obstruée, destruction du char, mort du conducteur et signal de
   départ absent ou répété. Refuser tout état durablement bloqué.
5. Sauvegarder/reprendre avant signal, en conduite et après arrêt; comparer
   objectifs, extraction et fin de mission au témoin.

Ces essais restent **pending**. Aucun fichier de l'installation n'a été changé.
