# Africa 5 — proximité du sniper 31

État : contrat documenté, prototype complet bloqué par les interruptions,
25 septembre 2026. Aucune ligne commerciale n'est activée.

## Deux rayons, pas un simple remplacement de portée

`AF4_31.scr` Patch (3462 octets, SHA-256
`6c4dcb2890858f6f1153066909bb02eeead5e9d325a6b10943707c8261f6837e`)
est lié à l'acteur `AF4_31`, présent dans `actors.bin`.
Le détecteur actif `pir` réveille le personnage et active ses alarmes lorsqu'un
joueur est dans les 12 unités. Le détecteur commenté `npir` fait l'inverse au-delà
de 14 : désactivation des alarmes puis saut à END, **sans suspension explicite**.
Les 12/14 forment donc un ancien mécanisme d'entrée/sortie avec bande intermédiaire,
pas une preuve que le rayon d'entrée aurait dû être remplacé par 14.

Deux bascules de `npir` sont également commentées : désarmement dans `OnAlarm`,
réarmement dans `OnAlarmDone`. Réactiver le seul `Whenever` serait incomplet.

## Concurrence avec la confrontation

La cinématique 20 désactive les alarmes, téléporte le sniper entre ses checkpoints,
oriente son arme vers `dummy_attack_schumann`, joue la réplique 09011816 puis
déclenche un tir vers `AF4_23`. Elle ne désarme pas le vestige `npir`, actuellement
inactif. Un événement de sortie de rayon réactivé pourrait donc interrompre
la séquence par son `goto END`.

La variable `atcutscene` ne suffit pas à protéger la suite : elle repasse à zéro
avant `CSC_EndCutscene`. `OnCutsceneDone(20)` contient encore deux attaques,
10000 puis 60000, et réactive les alarmes entre les deux. Un test sur cette
variable seule laisserait la phase post-cinématique exposée. Mort, alarme et
signaux 1/9 ont par ailleurs leurs sorties propres, avec les valeurs sauvegardées
77/88 : elles ne peuvent pas être réutilisées comme nouveau sélecteur arbitraire.

## Suite sûre

Le profil commercial 12 unités reste le défaut. Une expérience moderne de
portée peut être spécifiée séparément, mais ne doit pas être présentée comme
restauration de `npir`. Pour le mécanisme historique 12/14, établir d'abord une
table d'états qui exclut toutes les phases de confrontation, couvre annulation,
mort et reprise, puis vérifier les priorités d'événements en moteur.

Tester notamment les franchissements répétés 12/14 avant, pendant et après la
cinématique, une alarme dans la bande intermédiaire, la mort des deux protagonistes
et la reprise à chaque transition. Ne pas ajouter de profil générable avant ce
contrat. Même ensuite, le laboratoire Africa 5 reste bloqué par le détecteur
commercial de piste absent, décrit dans
[l'étude existante](../AFRICA5_OLD_RUNWAY01_DETECTOR/ETUDE.md).
