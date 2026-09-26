# Essais natifs dans des copies indépendantes

Cette procédure prépare les **27 reconstructions déjà définies**, pas l'ensemble
des 180 dossiers de recherche. Elle n'active aucune option de l'installateur
public et ne transforme pas un prototype en contenu validé.

## Ce qui change par rapport aux laboratoires A/B

Les 20 laboratoires désactivés utilisent des noms de mission distincts et restent
disponibles. La nouvelle voie d'essai utilise les **missions d'origine** dans une
copie privée du jeu : aucun remappage de nom, menu expérimental supplémentaire ou
gestionnaire à lancer. Elle prépare les 24 profils de scripts et les trois
comparaisons de scène coop, soit 27 paires de fichiers témoin/variante.

Chaque paire comprend les fichiers de la mission et ses scripts commerciaux
effectifs, issus des archives. La variante ne change que les scripts de sa recette
ou la paire `scene2.bin`/`mpscripts.dta` de son ambiance coop. Les fichiers globaux
proviennent de la copie de l'installation présente : ce n'est **pas** une preuve
de compatibilité des reconstructions avec toutes les corrections Heritage.
Les surcharges de la mission remplacées pour l'essai sont sauvegardées, puis
restaurées. Les menus et catalogues ne sont pas modifiés par cet outil.

## Isolation réelle

`tools/reconstruction_sandbox.py` copie les fichiers en les lisant et en créant
de nouveaux fichiers. Il n'utilise ni lien physique, ni jonction, ni lien
symbolique. Une archive source déjà liée physiquement devient un fichier
indépendant dans la copie. Chaque contenu est relu et son empreinte contrôlée.

Une session est obligatoirement un nouveau sous-dossier direct de
`.analysis/reconstruction-sandboxes/`. Le jeu copié est dans son sous-dossier
`game/`; les manifestes, contenus désactivés, sauvegardes et journaux sont à côté,
hors des chemins chargés par le jeu. L'ensemble reste ignoré par Git.

La copie conserve les profils et sauvegardes présents, mais avec des fichiers
indépendants : les futurs essais ne doivent jamais démarrer l'exécutable de
l'installation personnelle. La protection des fichiers ne démontre pas encore
le comportement du moteur ou d'éventuels accès externes; surveiller les journaux
et le dossier de travail lors du premier lancement.

```powershell
.\.venv\Scripts\python.exe tools\reconstruction_sandbox.py clone --source "D:\Games\Hidden and Dangerous 2" --session .analysis\reconstruction-sandboxes\native-trials-20260926 --build
.\.venv\Scripts\python.exe tools\reconstruction_trial_deploy.py prepare --session .analysis\reconstruction-sandboxes\native-trials-20260926
```

Sans `--build`, `clone` ne fait qu'un relevé. Un dossier existant n'est jamais
écrasé. Une copie interrompue n'a pas de marqueur `READY.json` valide et ne peut
pas recevoir de déploiement. Pour reprendre une préparation de configurations
interrompue sur une copie déjà vérifiée, `prepare --resume` recalcule chaque
configuration et n'accepte ses fichiers existants que s'ils sont identiques.

## Sélection, contrôle et retour arrière

Fermer tous les clients et serveurs H&D2 avant de changer les fichiers. L'outil
vérifie les processus, l'identité de la copie, les empreintes des archives, de
l'exécutable, des bibliothèques racine et des plugins racine concernés. Il refuse
les liens et les fichiers partagés dans les cibles ou ses données de contrôle.
La préparation exige le client Sabre Squadron 1.12 original déjà épinglé par les
outils du projet, SHA-256
`1eebde4710f800f712a05b1ecee2ba862c144f478df89b58e54c912e857ee78c`.

Exemple du premier profil solo, **sans lancer le jeu** :

```powershell
.\.venv\Scripts\python.exe tools\reconstruction_trial_deploy.py apply --session .analysis\reconstruction-sandboxes\native-trials-20260926 --profile czech2-ger12-lie --mode baseline
.\.venv\Scripts\python.exe tools\reconstruction_trial_deploy.py status --session .analysis\reconstruction-sandboxes\native-trials-20260926
```

Le résultat attendu est `applied_not_run` et aucune cible modifiée après écriture.
À l'étape de test seulement, démarrer le client de **cette copie**, avec son
dossier `game/` comme dossier de travail, puis utiliser la mission Czech 2
habituelle. Aucune commande du préparateur ne démarre le client.

Après fermeture du jeu, revenir à l'état initial, puis préparer la variante :

```powershell
.\.venv\Scripts\python.exe tools\reconstruction_trial_deploy.py restore --session .analysis\reconstruction-sandboxes\native-trials-20260926
.\.venv\Scripts\python.exe tools\reconstruction_trial_deploy.py apply --session .analysis\reconstruction-sandboxes\native-trials-20260926 --profile czech2-ger12-lie --mode variant
```

Une seule configuration peut être active. Il faut la restaurer avant d'en
sélectionner une autre, y compris pour passer du témoin à la variante. Les deux
profils Arctic 4 du garde 3 et les deux profils d'explosion Burgundy 3 ne peuvent
donc pas être cumulés accidentellement.

Le journal est écrit **avant** toute modification. Chaque fichier préexistant
est sauvegardé avec empreinte. Une restauration vérifie tous ses contenus avant
de commencer; si un fichier a été modifié ensuite, elle refuse de l'écraser et
conserve le journal. Les fichiers créés par l'essai sont déplacés dans
`retired/<transaction>/` avec suffixe `.disabled`, pas effacés. Seuls les dossiers
vides créés par cette transaction sont retirés. Les sauvegardes de progression
créées pendant le test ne figurent pas parmi les cibles et sont conservées.

En cas d'interruption pendant l'écriture, le même journal permet de restaurer
un mélange de fichiers encore initiaux et déjà déployés. Un verrou de processus
interrompu n'est jamais retiré automatiquement : vérifier d'abord que l'opération
est réellement terminée et identifier ce verrou précis avant toute reprise.

## Cinq témoins à observer avant leur variante

Deux missions commerciales présentent des références à des scripts absents :

- Africa 5 : `af4_runway01_detector.scr`, pour ses quatre profils;
- Co-Burgundy 1 : `bu1_diary.scr` et `bur1_obj_carnage.scr`, pour l'ambiance coop.

Les configurations **conservent ces absences et les liaisons commerciales** dans
le namespace d'origine. Aucun script vide, suppression de liaison ou seconde
autorité d'objectif n'est introduit. Les exceptions sont limitées aux noms
exacts et à l'empreinte du registre commercial connu; une absence supplémentaire
est refusée. Le générateur des laboratoires complets garde ses refus habituels.
Si la copie de l'installation contient déjà un remplacement local pour l'un de
ces fichiers absents des archives, il est sauvegardé et déplacé hors du jeu copié
pendant l'essai, puis restauré. Sa présence ne masque donc pas l'état commercial
que le témoin doit observer. L'installation personnelle reste intacte.

Les témoins peuvent être préparés pour observer le comportement réellement livré.
Les cinq variantes restent verrouillées jusqu'à un résultat `baseline` réel,
validé par le registre de preuves, avec l'exécutable et les deux empreintes
**natives** correspondants. Un simple drapeau de commande ne peut pas contourner
ce contrôle. Pour Africa 5, observer le dialogue de Schumann et le contrôleur
central de piste; pour Co-Burgundy 1, observer chargement, objectifs et progression.
Si le témoin échoue, consigner l'échec : ne pas transformer une référence absente
en fonctionnalité reconstruite sans preuve.

## Essais coopération

Préparer un hôte et deux clients indépendants; aucune archive ne doit être liée
physiquement entre eux. Sur les trois copies, choisir le **même profil et le même
mode témoin/variante** avant de démarrer les clients. Le profil d'ambiance reste
une mission de coopération officielle, pas une adaptation solo. Tester ensuite
connexions, distances, reconnexion, cadence des sons et autorité des événements.

Les noms de session locaux prévus pour les clients sont
`native-trials-20260926-client1` et `native-trials-20260926-client2`.
Un `READY.json` valide et les contrôles de configuration, pas l'existence du
dossier seul, font foi pour leur préparation.

## Vérification hors moteur et preuves ultérieures

```powershell
.\.venv\Scripts\python.exe tools\reconstruction_trial_deploy.py rehearse --session .analysis\reconstruction-sandboxes\native-trials-20260926
.\.venv\Scripts\python.exe tools\reconstruction_sandbox.py verify --session .analysis\reconstruction-sandboxes\native-trials-20260926
```

La répétition hors moteur déploie, relit et restaure les 27 témoins et les
22 variantes sans préalable moteur, soit **49 cycles de fichiers**. Elle ne
contourne pas les cinq barrières de témoin réel. Une comparaison finale de tous
les fichiers du jeu copié doit retrouver exactement le manifeste initial.
Le rapport `OFFLINE_REHEARSAL.json` conserve les empreintes et journaux, avec
`runtime_tests_performed: 0`. Un rapport existant n'est pas écrasé.

Après de vrais essais, `verify` peut signaler des profils, sauvegardes ou journaux
modifiés : les examiner, ne pas les effacer pour obtenir artificiellement un
résultat identique. `status` contrôle seulement les fichiers de l'expérience
active. Aucun des outils ne remplit le registre d'essais à la place du testeur.

Les JSON sous `presets/` contiennent les chemins et empreintes des ensembles
natifs. Ils diffèrent légitimement des empreintes des laboratoires renommés :
utiliser les manifestes du déploiement réellement testé et les conserver avec
les captures. La procédure de preuve reste celle de [RECONSTRUCTION.md](RECONSTRUCTION.md).

## Préparation effectivement vérifiée le 26 septembre 2026

- Trois copies indépendantes ont été créées, chacune avec 24 385 fichiers,
  6 508 813 370 octets et le même manifeste initial.
- Les 27 configurations ont été reconstruites dans chacune des trois copies;
  leurs empreintes de protocole correspondent toutes au registre actuel.
- Les **49 cycles de fichiers** ont été effectués sur l'hôte. Tous les retours
  arrière ont réussi; la comparaison globale finale retrouve exactement les
  fichiers initiaux, sans ajout résiduel ni contenu changé.
- Le rapport local est `OFFLINE_REHEARSAL.json` dans la session hôte. Les données
  commerciales, sauvegardes, fichiers écartés et journaux restent hors de Git.
- **296 tests Python réussis sur 297 dans la copie de publication**; un test de création de lien symbolique
  n'a pas pu s'exécuter sans privilège Windows. Les liens physiques, les cibles
  modifiées, les interruptions et les restaurations ont leurs tests distincts.
- **Zéro essai moteur** et aucun lancement de jeu ou d'installateur par ces outils.
  Les 165 résultats expérimentaux restent `pending`.

Les anciennes fiches sous `.analysis/reconstruction-trials/preparation-20260926/`
décrivent une préparation antérieure des laboratoires. Pour les essais natifs,
utiliser les protocoles et études actuels du registre et les empreintes sous
`presets/`, pas les anciennes empreintes de missions renommées.
