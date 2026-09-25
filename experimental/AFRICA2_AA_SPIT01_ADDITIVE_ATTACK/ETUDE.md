# Africa 2 — attaque aérienne AA_Spit01

État : frame présente, script libre incomplet en contrôle, 26 septembre 2026.
Aucun binding ajouté et aviation commerciale conservée.

`AF2_aa_spit01.scr` : Patch.dta, 2517 octets, SHA-256
`95620529528acd21f44ab5d396b3ec4931067a23046048dc96a1a83fe3766f12`.
Il n'est ni lié ni atteint par les affectations/inclusions littérales. La frame
`aa_spit01` existe en scene2.bin à (−342,205; 25,239; 93,150), distincte de
`spit01`. Aucun autre script Africa2 consulté ne la nomme littéralement; aucun
raccord de signal 1 n'est ainsi démontré.

## Plus qu'un signal d'activation manquant

Le script masque son propriétaire et attend, mais le Whenever
`_PlayerInRange(100)` n'est pas initialement désarmé. Son chemin mène directement
à ATTACK, sans rallumer la frame; signal 1 passe au contraire par ACTIVATE,
qui l'allume et attend 1000 ms. Signal 20 efface la cible puis repart à ATTACK.
Ces trois entrées ne sont donc pas équivalentes.

ACTIVATE saute à ATTACK **avant** les attentes 120000/30000 et la désactivation
finale : ce nettoyage est inatteignable par le flux séquentiel montré. ATTACK
désarme la proximité et choisit une cible, mais saute à END; le `goto ATTACK`
suivant n'en fait pas une boucle active. OnHit et OnDeath ne font que rejoindre
END, sans effacer explicitement la cible ni masquer le propriétaire.

CHOOSETARGET choisit parmi **le camion opelsflakem et quatre joueurs**. Malgré
le commentaire « Spitfire contre convoi allemand », quatre branches attaquent
un joueur vivant. La vérification d'état du camion est commentée. Une boucle
de re-tirage sans attente ni nombre maximal d'essais subsiste si les branches
joueurs sélectionnées sont invalides. Ne pas présenter cette routine comme
une attaque alliée propre et terminée.

## Reconstruction encadrée

Avant un prototype : identifier le type d'acteur et la physique de la frame,
observer l'aviation active et choisir explicitement la faction/cible moderne.
Définir un propriétaire d'activation unique, fermer les trois entrées, borner
la sélection de cible et assurer désactivation/fin sur toutes les sorties.
Ne pas retirer silencieusement les attaques du joueur en prétendant restituer
le script original, ni recopier mes03 sous un second nom.

Les scripts mes03/04, hélices et organisateur restent liés; leur scénario n'est
pas remplacé. La copie de mission demeure bloquée par le script Junkers absent
déjà [classé](../AFRICA2_JUNKERS_PARTICLE_OWNER/ETUDE.md), sans autoriser de stub.
Essais requis : signal répété, proximité avant signal, cible détruite, aucun
joueur valide, impact/mort, sauvegarde, fin de mission et absence de double avion.

scene2.bin : missions.dta, 4905695 octets, SHA-256
`803fc3b327ff08b5b37cf6e206f9634a9c3e866e5327c0767715a97fefeca58c`.
Cette étude complète la
[quarantaine aéronautique](../AIRCRAFT_DECOR_LAB/ORPHAN_SCRIPTS.md), sans convertir
le Spitfire en avion pilotable.
