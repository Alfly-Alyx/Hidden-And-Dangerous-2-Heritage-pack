# Étude expérimentale — lecture interrompable d'AF4_19

État : **laboratoire uniquement**, 15 septembre 2026. Cette évolution complète
l'étude antérieure `AFRICA5_READING_AF4_19` par un contrat de nettoyage sur
alarme et décès. Aucun fichier du jeu n'est modifié et rien n'est compilé.

## Verdict

Le contenu commercial prouve l'intention mais pas le fonctionnement de
`HUMAN_ACTIVITY_Read`. La note « doplnit az bude fungovat read » indique
explicitement que cette partie devait attendre une API fonctionnelle. Un audit
des scripts Base/Patch ne trouve aucun appel actif à cette fonction.

La seule variante recevable est donc une copie expérimentale d'AF4_19, jamais
le script stable. Elle conserve l'inspection de l'archive et les postures, puis
essaie prise, lecture, arrêt et dépôt. L'arrêt de lecture et le dépôt sont aussi
appelés dans `OnAlarm()` et `OnDeath()` avant la logique commerciale restante.

## Preuves vérifiées

| Élément | Preuve | Conclusion |
| --- | --- | --- |
| porteur | `missions.dta`, `actors.bin` contient exactement `AF4_19` | garde commerciale présente |
| binding | `scripts.dta` lie `AF4_19` à `AF4_19.scr` | propriétaire résolu |
| archive | `scene2.bin` contient `m_AF5_slozky01b14` | cible de `HUMAN_Investigate` résolue |
| livre | `scene2.bin` contient `m_AF5_slozky01a7` | frame prévue par le script résolue ; saisissabilité non prouvée |
| code actif | `HUMAN_Investigate(archive)`, délais, passage debout puis accroupi | baseline à préserver |
| code dormant | prise, deux appels `Read`, dépôt | intention officielle inachevée |
| corpus | zéro appel actif à `HUMAN_ACTIVITY_Read` dans Base/Patch | compatibilité moteur inconnue |

Base et Patch possèdent la même séquence utile. La copie Patch effective est le
point de départ d'un éventuel essai.

## Contrat interruptible

[`PROTOTYPE_INTERRUPT_SAFE.scr.disabled`](PROTOTYPE_INTERRUPT_SAFE.scr.disabled)
est un script complet de laboratoire afin que les sorties ne soient pas perdues
par un simple remplacement de boucle.

Il préserve :

- `HUMAN_Investigate(archive)` au début de chaque cycle ;
- marche, station debout avant lecture et retour accroupi ;
- suspension initiale, signal 1, modes IA et optimisation ;
- calcul et affichage du type d'alarme ;
- reprise `OnAlarmDone() -> ACTIVATE` ;
- message puis `EndScript()` sur décès.

Il ajoute seulement un arrêt de lecture suivi d'un dépôt dans trois chemins :
fin normale, `OnAlarm()` et `OnDeath()`. L'alarme conserve le
`HUMAN_DropObject()` commercial, désormais précédé par l'arrêt explicite de
l'activité.

Cette structure ne suffit pas à garantir le comportement moteur si `Read` est
non interruptible : dans ce cas le prototype est rejeté. Le fichier
[`PROTOTYPE_RELEASE_FALLBACK.scr.disabled`](PROTOTYPE_RELEASE_FALLBACK.scr.disabled)
formalise le retour à la boucle commerciale sans objet tenu.

## Validation progressive

1. Vérifier en éditeur que `book` peut être saisi et qu'il n'est pas un décor
   partagé ou nécessaire à une autre animation.
2. Charger une copie laboratoire. Une erreur de symbole, de signature ou de
   chargement de `Read` impose le repli immédiat.
3. Exécuter cinq cycles complets : un seul livre pris, lu, arrêté puis déposé.
4. Déclencher une alarme avant la prise, pendant la prise, pendant `Read`, après
   l'arrêt et après le dépôt. Le livre ne doit jamais rester attaché.
5. Tuer AF4_19 aux mêmes cinq instants et inspecter main, sol et frame source :
   aucun objet orphelin, invisible ou dupliqué.
6. Tester alarme terminée : `ACTIVATE` doit rétablir exactement marche,
   station debout, IA Zombie puis position accroupie avant la boucle.
7. Sauvegarder/reprendre avant activation, livre tenu, lecture active et après
   alarme ; répéter avec changements de niveau de détail.
8. Remettre le repli et comparer conversation, alarme, décès et progression à
   la release.

Critères d'arrêt : `Read` non interruptible, dépôt absent, duplication,
réapparition incorrecte de la frame, animation bloquée, alarme retardée ou
différence de progression.

## Retour arrière

Réinstaller uniquement le corps de repli dans la copie expérimentale ou
supprimer cette copie. Aucun acteur, frame, binding ni texte n'est ajouté ; le
registre commercial reste inchangé.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_19.scr` ;
- `.analysis/scripts/patch/SCRIPTS/AFRICA5/AF4_19.scr` ;
- `missions.dta : MISSIONS/AFRICA5/actors.bin`, `scene2.bin`, `scripts.dta` ;
- `experimental/AFRICA5_READING_AF4_19/` (étude antérieure).
