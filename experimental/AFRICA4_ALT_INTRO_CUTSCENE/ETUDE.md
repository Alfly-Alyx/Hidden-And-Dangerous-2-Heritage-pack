# Étude expérimentale — introduction alternative d'Africa 4

État : **reconstruction moderne incomplète et désactivée**, 15 septembre 2026.
La release Dakota/parachutiste reste inchangée ; aucune compilation.

## Verdict

`AF3b_cutscene.scr` conserve deux branches abandonnées : un panoramique depuis
`camera_rozhlizeni01` vers deux dummies puis `Opel02`, et l'enchaînement vers la
cinématique 2 utilisant `camera_cut04`. `AF3b_player04.scr` conserve, lui aussi
commentée, la réaction du joueur 04 : déplacement vers `AF3b_pl04_01`, posture
accroupie, arme au bras, fin et téléport de nettoyage.

Ce n'est pas une simple réactivation. Le contrôleur ancien n'est pas lié ; la
release lie `camera_cut01` à `CUTcamera_Af3b.scr` et `script_mise_next.scr`
lance déjà la cinématique 1. Ajouter l'ancien contrôleur produirait deux
propriétaires des mêmes événements et du contrôle caméra.

La variante doit être une entrée exclusive, avec identifiants réservés après
audit, caméras modernes et un seul propriétaire de `CSC_EndCutscene()`.

## Inventaire frames/checkpoint

| Nom historique | État vérifié | Décision |
| --- | --- | --- |
| `camera_cut01` | présent et lié à la release | ne pas réutiliser dans l'entrée moderne |
| `camera_cut02`, `camera_cut03` | absents de `scene2.bin` et `actors.bin` | recréer sous noms modernes |
| `camera_cut04` | absent | recréer sous nom moderne ; transform inconnu |
| `camera_rozhlizeni01` | absent | recréer sous nom moderne |
| `dummy_rozhlizeni01/02` | présents dans `scene2.bin` | cibles de regard réutilisables |
| `Opel02` | acteur présent et lié | troisième cible attestée |
| `AF3b_pl04_01` | attesté par l'inventaire antérieur de mission ; non revalidé dans l'extrait courant dépourvu de `check2.bin` | revalider dans le `check2.bin` complet avant prototype |

Le handler actif de `AF3b_player04.scr` se termine après la cinématique 1. Ses
handlers de scène 2 sont commentés et le script n'est pas lié directement :
`AF3b_spawn04.scr` tente de l'assigner sur `OnUse`. Ce cycle de vie doit être
remplacé par une attribution explicite dans la variante, puis restauré.

## Enchaînement reconstruit

Le plan et les fragments désactivés définissent l'ordre suivant :

1. sélection préchargement de l'intro alternative, empêchant le lancement de
   la cinématique release ;
2. scène A : caméra moderne 01, puis panoramique moderne vers
   `dummy_rozhlizeni01`, `dummy_rozhlizeni02` et `Opel02`, puis caméras modernes
   02 et 03 ;
3. `CSC_EndCutscene()` unique, nettoyage A, puis lancement de la scène B ;
4. scène B : caméra moderne 04 et réaction du joueur 04 vers
   `AF3b_pl04_01` ;
5. le contrôleur central, pas le joueur, termine B après un délai borné ;
6. `OnCutsceneDone(B)` neutralise le cadre caméra, coupe les sous-titres,
   restaure le fade et termine le contrôleur ; le joueur s'arrête, est recalé
   sur le checkpoint et revient en garde.

Les identifiants `ALT_SCENE_A/B` restent des jetons non compilables tant qu'un
audit global n'a pas réservé deux valeurs libres. Les temps du panoramique et
de la scène B sont des créations modernes à valider.

## Garantie caméra et commandes

[`PROTOTYPE_ALT_CONTROLLER.scr.disabled`](PROTOTYPE_ALT_CONTROLLER.scr.disabled)
centralise les deux `CSC_EndCutscene()`. Le joueur ne peut donc pas laisser la
caméra verrouillée s'il est absent, mort ou bloqué. Le nettoyage est répété dans
les deux `OnCutsceneDone` : frame caméra nulle, sous-titres coupés et fade-in.

[`PROTOTYPE_PLAYER04_REACTION.scr.disabled`](PROTOTYPE_PLAYER04_REACTION.scr.disabled)
ne termine aucune cinématique. Il restaure déplacement/posture après la
notification de fin. Une version jouable devra aussi définir le skip/abort du
moteur ; si aucun callback fiable n'est disponible, la variante reste bloquée.

## Tests

1. Auditer globalement deux identifiants libres et revalider `AF3b_pl04_01`.
2. Créer quatre caméras sous noms `camera_alt_af4_*`, documenter transform, FOV
   et parentage ; ne pas renommer des frames release.
3. Vérifier un seul lancement et un seul propriétaire caméra dans chaque profil.
4. Tester normal, skip, chargement, joueur 04 absent/mort/bloqué et quatre
   compositions d'équipe. La scène B doit toujours finir par son timeout.
5. Après chaque sortie : vue joueur, commandes, sous-titres, fade, posture,
   arme et script IA doivent être rétablis.
6. Rejouer `INTRO_RELEASE` et comparer Dakota, sons, particules, joueurs
   dupliqués et `camera_cut01` à la baseline.

## Retour arrière

Sélectionner l'intro release, supprimer de la copie les quatre caméras modernes,
le contrôleur et la réaction fusionnée du joueur 04. Remettre les bindings et
scripts Patch commerciaux sans modification.

## Sources internes

- scripts Base/Patch `AF3b_cutscene.scr`, `AF3b_player04.scr`,
  `AF3b_spawn04.scr`, `CUTcamera_Af3b.scr`, `script_mise_next.scr` ;
- `missions.dta : MISSIONS/AFRICA4/scene2.bin`, `actors.bin`, `scripts.dta` ;
- `experimental/AFRICA4_LEGACY_OASIS_INTRO/`.
