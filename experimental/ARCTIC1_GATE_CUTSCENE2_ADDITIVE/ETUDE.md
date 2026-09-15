# Arctic 1 — caméra K2 de la scène de la grille

État : **profil sélectionné seulement, non activé**, 15 septembre 2026. Aucun
fichier de mission ou d'installation n'est modifié et rien n'est compilé.

## Verdict

Le lien commercial `K2 -> kamera 2.scr` existe encore et le contrôleur emploie
les caméras `K2` puis `K2a`. L'ancien `SendSignal(K2, 1)` du garde est cependant
commenté avec une note explicite : des changements ultérieurs ont cassé la
scène. Le réactiver à côté de la branche release n'est donc pas additif : il
ferait concourir deux chorégraphies du même garde.

Une seule variante est retenue pour essai : **K2_SELECTED_TEST**. Elle est une
alternative atomique au mouvement release lors du premier déclenchement, pas
une seconde action superposée. Elle conserve la voix release en envoyant une
seule fois le signal 1 à `dummy_Dabing_GG`, puis lance une seule fois K2. Les
déplacements manuels release sont alors omis pour laisser l'unique
`OnCutscene(2)` du garde piloter le corps. Le profil par défaut reste
**RELEASE_DIALOGUE**.

## Ce qui est prouvé

- `Gate_Guard` résout `K2` et `dummy_Dabing_GG` ;
- `K2` est lié à `kamera 2.scr` dans le registre effectif ;
- `kamera 2.scr` reçoit 1, lance la cutscene 2, passe de `K2` à `K2a` puis
  revient à `K2` avant la fin ;
- `R_Arc1A_dabind_GG.scr` joue exactement les cinq répliques 01990236 à
  01990240 sur un seul signal 1 ;
- `R_Arc1A_Gate_Guard.scr` possède encore la chorégraphie complète
  `OnCutscene(2)` et les signaux 10/11 vers Herman ;
- la branche release joue ces mêmes cinq voix, puis effectue sa propre
  séquence accroupi/rotation/retour de garde sans caméra.

## Risques qui empêchent une restauration stable

Le simple ajout de `SendSignal(K2, 1)` après la branche release peut déclencher
en même temps la séquence manuelle et `OnCutscene(2)`. Il peut aussi réafficher
les mêmes sous-titres pendant que le dummy joue les voix. Enfin, le
`OnCutsceneDone(2)` du garde apparaît textuellement dans le bloc
`OnAlarmDone()` ; son enregistrement effectif par le moteur doit être confirmé
avant de compter sur ce nettoyage.

`K2a` n'est pas un second déclencheur : c'est une caméra interne choisie par
`kamera 2.scr`. La variante ne doit jamais lui envoyer de signal directement.

## Contrat de sélection

Le contrat exécutable futur est décrit dans
[`PROFILE_SELECTOR.plan.disabled`](PROFILE_SELECTOR.plan.disabled). Il impose :

1. un choix avant le déclenchement entre release et K2 ;
2. un verrou one-shot commun aux deux profils ;
3. une seule émission de la voix release ;
4. zéro instruction de mouvement release dans le chemin K2 ;
5. retour au loop de garde uniquement après la fin/annulation de la cutscene ;
6. arrêt propre de la voix en cas d'alarme ou de mort.

Aucun `.scr.disabled` n'est fourni : le placement ambigu du handler de fin et
la synchronisation voix/sous-titres empêchent de présenter un faux prototype
compilable.

## Tests obligatoires

- baseline release, cinq voix une fois, aucune caméra ;
- K2 sélectionné, cinq voix une fois, aucun mouvement concurrent ;
- seconde entrée dans le rayon pendant la scène : aucun second départ ;
- alarme et mort avant, pendant chaque plan et juste avant la fin ;
- skip de cutscene, sauvegarde/reprise et retour caméra joueur ;
- Herman reçoit 10 puis 11 une seule fois ;
- sous-titres activés puis désactivés, sans ligne doublée ;
- absence de régression sur walkers, objectif 1 et scène guide 3/4.

## Sources internes

- `.analysis/arctic1-full/MISSIONS/ARCTIC1/scripts.dta` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_Gate_Guard.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/kamera 2.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_dabind_GG.scr`.
