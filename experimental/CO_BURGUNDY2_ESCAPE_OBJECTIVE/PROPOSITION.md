# Étude expérimentale — objectifs 15573 et 15577 de Co_Burgundy2

État : **vestige remplacé pour 15573, création hybride seulement ; 15577 bloqué**,
14 septembre 2026. Aucun prototype exécutable n'est fourni et aucun fichier
commercial n'est modifié.

Selon le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md),
la sécurisation coop actuelle doit rester la branche release. Une future route
d'évasion ne serait recevable que comme objectif et progression distincts,
avec un arbitre garantissant qu'un fugitif sorti de la zone ne valide pas
simultanément la sécurisation. Aucun tel contrat n'est encore démontré.

## Verdict

| Texte solo omis | Fonction | Classification coop | Décision |
| ---: | --- | --- | --- |
| `15573` | personne ne doit s'échapper | scénario remplacé/reconçu ; quelques actifs subsistent | ne pas « restaurer » par deux handlers |
| `15577` | toute l'unité doit survivre | sémantique réseau absente | aucun prototype avant preuve d'un événement de mort fiable |

`15573` n'a pas été fusionné littéralement dans `15572`. Le contrôleur coop ne
conserve ni son état ni ses deux échecs. En revanche, la nouvelle condition
« sécuriser la zone » exige la neutralisation des ennemis et rend fonctionnellement
la fuite impossible. Les comportements de fuite ont été retirés des deux acteurs
concernés. Le détecteur encore lié est donc un **vestige d'architecture**, pas la
preuve d'une chaîne jouable amputée de son seul récepteur.

Une variante d'évasion reste techniquement imaginable parce que les véhicules et
les chemins nommés sont encore présents dans les données coop. Elle demanderait
toutefois de réintroduire une logique d'acteur supprimée et de renégocier deux
objectifs coop actuels. Elle doit être présentée comme **création moderne fondée
sur des actifs officiels**, jamais comme restauration minimale.

## Comparaison des objectifs

La carte solo déclare, dans l'ordre :

| N° solo | Texte |
| ---: | ---: |
| 1 | `15570` |
| 2 | `15571` |
| 3 | `15573` — aucun fugitif |
| 4 | `15572` — sécuriser la zone |
| 5 | `15575` |
| 6 | `15576` |
| 7 | `15577` — toute l'unité survit |

La carte coop déclare seulement `15570`, `15571`, `15572`, `15575` et `15576`,
numérotés 1 à 5. Le contrôleur coop est réécrit pour cette séquence :

- objectif 1 réussi quand la valeur 16 passe à 0, c'est-à-dire à la mort de
  `gumak` ;
- objectif 2 : collaborateur capturé ;
- objectif 3 réussi quand la valeur 14 vaut 1, compteur coop de sécurisation ;
- objectif 4 : équipe regroupée ;
- objectif 5 : documents.

Il n'existe donc aucun numéro libre implicite à viser. Ajouter `15573` comme
objectif 6 serait déjà un choix de variante, pas la remise en place d'un numéro
oublié.

## Ce qui subsiste réellement de l'évasion

### Émetteur orphelin

Les copies solo et coop de `detect_motopryc.scr` sont identiques et surveillent
encore :

```text
ge_dilna à moins de 20 unités -> signal 3 vers objectyves
gumak    à moins de 20 unités -> signal 4 vers objectyves
```

Le contrôleur solo traite ces signaux, affiche respectivement le départ des
soldats ou de `gumak`, échoue son objectif 3 puis arrête la mission. Le contrôleur
coop ne traite ni 3 ni 4. Comme ses acteurs ne rejoignent plus les routes de
fuite, ces émissions sont normalement inatteignables ; leur liaison conservée
est un faux indice si elle est étudiée isolément.

### Logique supprimée chez les acteurs

Dans le solo, `gumak.scr` choisit un véhicule selon les valeurs 5 à 8 :

- route à pied `gumak1`, embarquement dans `la_citroen`, conduite par `bmv2` ;
- ou route `gumak2`, embarquement dans `bmw`, conduite par `citron1`.

La copie coop supprime les frames de véhicule, les deux labels et tous les appels
d'embarquement/conduite. Après une alarme distante, elle attend seulement qu'un
joueur soit à moins de 30 unités puis termine. Elle remplace aussi la valeur de
vie 15 par 16, précisément celle que l'objectif coop 1 attend à zéro.

Dans le solo, `ge_dilna.scr` peut rejoindre `bmw`, attendre son passager puis
conduire par `bmv2`. La copie coop conserve quelques déclarations (`pryc1`,
`bmw`) mais retire l'assise, le son, l'embarquement et la conduite ; elle ne fait
plus que rejoindre `ge_dilna1` en réaction de combat.

### Actifs de mission encore présents

Une lecture temporaire de `SabreSquadron.dta`, sans écriture dans le jeu, confirme
dans **les deux** dossiers de mission les identifiants `gumak1`, `gumak2`,
`citron1`, `bmv2`, `pryc1`, `ge_dilna_sit`, `gumanastup` et `la_citroen`. Les
acteurs `bmw` et `la_citroen` existent aussi dans `Co_Burgundy2/actors.bin`, et
les scripts coop `testbmw.scr`/`testcitroen.scr` contrôlent encore leurs valeurs
8/7. `car_table.dat` est identique entre solo et coop. En revanche, `badmusic`
n'apparaît pas dans la scène coop.

Ces preuves établissent la disponibilité matérielle des véhicules et parcours,
pas leur aptitude multijoueur ni la présence d'un comportement de fuite actif.

## Pourquoi 15573 ne doit pas être restauré tel quel

Deux conflits structurels empêchent un raccord minimal :

1. si `gumak` s'échappe vivant, la valeur 16 ne passe pas à 0 et l'objectif coop
   1 « éliminer l'officier SS » ne peut pas réussir ;
2. un ennemi sorti vivant peut empêcher la valeur 14 d'indiquer la sécurisation,
   donc bloquer l'objectif coop 3 `15572`.

Le scénario coop a ainsi remplacé la bifurcation « tuer ou laisser fuir » par
« tuer et sécuriser ». Restaurer seulement les handlers 3/4 créerait des échecs
jamais émis. Restaurer les routes créerait au contraire un blocage des objectifs
actuels. Une variante cohérente doit choisir une nouvelle règle de mission.

## Variante expérimentale concevable, non produite

### Partie officielle réutilisable

- texte `15573` ;
- détecteur et signaux 3/4 ;
- véhicules, points d'embarquement et chemins nommés ;
- arbres de décision solo de `gumak` et `ge_dilna` comme références.

### Création moderne obligatoire

- décider si `gumak` peut fuir malgré l'objectif qui exige sa mort, ou exclure
  `gumak` et modifier le sens du texte ;
- définir comment le compteur de sécurisation traite un fugitif sorti de zone ;
- arbitrer les sièges déjà occupés par plusieurs joueurs ;
- décider qui possède l'autorité sur l'embarquement, la conduite et l'émission
  d'échec ;
- rendre les signaux idempotents et persistants après sauvegarde/reprise ;
- remplacer ou omettre le cue `badmusic` absent de la scène coop.

**Faisabilité : 2/4. Fidélité atteignable : 2/4.** Les actifs réduisent le coût,
mais les règles décisives seraient nouvelles. Aucun `.scr.disabled` n'est donc
justifié à ce stade.

## Objectif 15577 — survie de toute l'unité

Le solo n'effectue qu'un test final de `_IsTeamMemberDead()` avant de réussir
l'objectif 7. Le coop ne déclare pas `15577` et ne conserve aucun événement de
mort joueur permettant de reproduire correctement ce résultat. Ses zones de
respawn rendent un simple décompte instantané encore moins fidèle.

La sémantique expérimentale cohérente avec Co_Libye2 et Co_Burgundy1 serait :

- cohorte : joueurs alliés actifs au début de la phase pertinente ; spectateurs
  exclus ;
- toute mort d'un membre de cette cohorte disqualifie définitivement l'objectif ;
- respawn et reconnexion ne réparent pas la disqualification ;
- une déconnexion d'un joueur vivant reste neutre ;
- succès seulement à la fin normale de la mission si aucune disqualification
  n'a été enregistrée.

Sans callback ou valeur serveur autoritaire distinguant mort, respawn,
spectateur et déconnexion, cette politique ne peut pas être implémentée avec
fidélité. **Faisabilité : 2/4 ; fidélité théorique : 3/4 ; prototype bloqué.**

## Tests requis avant tout futur prototype

Pour l'évasion : tester véhicule libre/occupé/détruit, deux joueurs au même
siège, les deux fugitifs simultanés, mort pendant l'embarquement, arrivée dans la
zone, compteur 14, valeur 16, signaux répétés, sauvegarde/reprise et hôte/client.
Le test doit démontrer qu'un seul verdict de mission est produit.

Pour la survie : tester mort avant/après activation, respawn, changement de zone,
connexion tardive, spectateur, déconnexion vivant/mort, reconnexion et migration
d'hôte. Toute ambiguïté sur une mort passée interdit le succès.

## Sources internes

- `.analysis/metadata/sabre/GameData/Gamedata01.gdt`
- `.analysis/metadata/sabre/GameData/mpmaplist.txt`
- `.analysis/scripts/sabre/Scripts/burgundy2/objectyves.scr`
- `.analysis/scripts/sabre/Scripts/co_burgundy2/objectyves.scr`
- copies solo/coop de `detect_motopryc.scr`, `gumak.scr`, `ge_dilna.scr`,
  `testbmw.scr` et `testcitroen.scr`
- `output/audit/map-inventory.json`
- fichiers de mission lus temporairement depuis `SabreSquadron.dta`
- `experimental/CO_LIBYE2_OBJECTIVE4_SURVIVAL/ETUDE.md`
- `experimental/CO_BURGUNDY1_OBJECTIVE7_SURVIVAL/ETUDE.md`
