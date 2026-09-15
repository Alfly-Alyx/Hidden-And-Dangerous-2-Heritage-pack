# Étude expérimentale — ancien réseau `R_N2_Go_*` de Normandy 2

État : architecture retirée, 14 septembre 2026. Aucun delta n'est proposé et
aucun fichier de mission ou registre n'est modifié.

Selon le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md),
la route retirée n'est pas abandonnée parce qu'une progression actuelle existe :
elle pourrait devenir une branche optionnelle parallèle. Le blocage demeure
ici parce que ses bindings et son contrat complet avec les scripts Ally ne sont
pas conservés, pas parce qu'elle devrait remplacer la release.

Le roster retiré de quinze défenseurs et ses raccords d'activation sont étudiés
séparément dans
[`NORMANDY2_REMOVED_DEFENDERS`](../NORMANDY2_REMOVED_DEFENDERS/ETUDE.md).
Les deux branches ne doivent être combinées qu'après validation indépendante.

## Verdict

`R_N2_Go_13.scr` contient une coquille très probable : il déclare
`Dummy_Go_11a` et `Dummy_Go_11b`, mais envoie deux fois le signal 15 à Go11a.
Les contrôleurs adjacents Go10 et Go12 traitent toujours la paire a/b.

La correction textuelle évidente serait de remplacer le second destinataire
par Go11b. Elle n'est pourtant pas proposée, car les acteurs `Dummy_Go_*` et
leurs scripts ne sont pas reliés dans le registre effectif 1.12. Le défaut vit
dans une route complète retirée ; corriger une seule ligne n'aurait aucun effet
sur la mission active et ferait croire à tort que l'architecture est restaurée.

## Forme du réseau ancien

Les scripts Go1 à Go14 constituent un maillage spatial cohérent :

- chaque contrôleur commence avec son Whenever `Go` désactivé ;
- le signal 5 active sa zone et le signal 15 la désactive ;
- lorsque le joueur entre dans la zone, le contrôleur envoie son numéro aux
  cinq alliés `Ally_1` à `Ally_5` ;
- il désactive les zones précédentes par 15 et active les suivantes par 5.

Go13 suit exactement ce patron : il envoie 13 aux cinq alliés, doit neutraliser
Go11a, Go11b et Go12, puis active Go14. Sa déclaration des deux branches 11 et
la symétrie de Go10/Go12 donnent une confiance 4/4 à la coquille locale :

```text
SendSignal(Go11a, 15);
SendSignal(Go11a, 15);  // devait très probablement viser Go11b
SendSignal(Go12,  15);
```

Go10 active `Go11a`, `Go11b` et Go12. Go12 désactive Go10, `Go11a` et
`Go11b`, puis active Go13/14. Go13 est donc le seul membre de ce voisinage à
oublier la branche b tout en la déclarant.

## Pourquoi ce n'est pas un correctif stable isolé

Le graphe effectif ne résout aucun acteur `Dummy_Go_*`. Le registre Tutorial
et les autres missions montrent que la présence d'un fichier `.scr` dans le
corpus ne suffit pas : sans paire acteur/script, aucun propriétaire ne reçoit
5/15 et aucune zone ne s'exécute.

Deux distributions de démonstration conservées, `sp-unpacked` et
`release-normandy2`, contiennent le même réseau source et la même duplication
dans Go13. Elles documentent donc l'ancienneté du défaut, pas son activité dans
le registre retail. Aucune variante trouvée ne relie ce réseau au contrôleur de
progression final.

Réactiver l'ensemble exigerait en outre de vérifier les signaux 1 à 14 reçus par
les cinq alliés, leurs états actuels, les zones et leur interaction avec les
contrôleurs de vagues. Cette surface dépasse largement la seconde ligne de
Go13.

## Décision

Classer la substitution `Go11a → Go11b` comme **correction archéologique
4/4**, mais **intégrabilité 0/4**. Ne pas créer de prototype exécutable, ne pas
ajouter les bindings absents et ne pas greffer une seule zone sur la mission
1.12.

Une réouverture requiert un ancien registre où les `Dummy_Go_*` sont liés, plus
une version des scripts Ally compatible. Seulement alors la correction Go13
pourrait être testée dans le contexte complet de cette route historique.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/NORMANDY2/R_N2_Go_1.scr` à `_14.scr`
- `.analysis/demos/sp-unpacked/Scripts/Normandy2/R_N2_Go_*.scr`
- `.analysis/demos/release-normandy2/SCRIPTS/NORMANDY2/R_N2_Go_*.scr`
- `.analysis/demos/release-normandy2/MISSIONS/NORMANDY2/Scripts.dta`
- `.analysis/signal-graph-current.json` et `.md`
