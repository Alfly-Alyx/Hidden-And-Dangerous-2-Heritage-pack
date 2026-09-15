# Étude expérimentale — `Mesh24` et `z2_agresor1` à Brest

État : réveil prudent proposé sous forme désactivée, 14 septembre 2026. Aucun
script Brest/Co_Brest n'est modifié.

## Verdict

L'ouverture de `Mesh24` diffuse le signal 1 à dix acteurs dans Brest comme dans
Co_Brest. Neuf le traitent ; `z2_agresor1`, pourtant suspendu, ne le traite pas.
La chaîne est intentionnelle, mais aucune archive retrouvée ne conserve le
handler. Un réveil seul est proposé comme **reconstruction expérimentale 2/4**.
Le départ immédiat vers la route d'attaque n'est pas proposé.

## État officiel de l'agresseur

`z2_agresor1.scr` commence suspendu hors des modes carnage. Sa réaction
officielle à une alarme 2/16/256 est très structurée :

1. attendre tant que la valeur de jeu 6 vaut 1 ;
2. sortir de suspension et basculer la variable locale `suspend` à 0 ;
3. conserver seulement les alarmes 1, 32 et 64 ;
4. aller au label `vybeh` ;
5. réveiller `z2_agresor2`, ouvrir les deux portes puis courir vers
   `z2agres1_1`.

Le signal 1 de `Mesh24` peut donc avoir eu deux sens : rendre l'acteur capable
de percevoir l'alarme, ou lancer immédiatement `vybeh`. Les neuf voisins ne
tranchent pas ce choix : ils se réveillent tous, mais démarrent chacun une
route propre.

## Variantes inspectées

Les copies solo et coopérative sont identiques sur ce point. Les variantes
communautaires `BYTM_brest_ext`, `Co_brest_gestopo`, `Co_brest_gestopoX3` et
`Co_Brest_siop` conservent à la fois l'émission de `Mesh24` et l'absence de
récepteur chez `z2_agresor1`. Les révisions historiques survivantes contrôlées
ne restituent pas davantage le corps manquant.

Archive publique consultée : [Official Coop Map Package](https://github.com/ehylla93/had2-cmp/).

## Prototype prudent

`PROTOTYPE_WAKE_ONLY.scr.disabled` sort seulement l'acteur de suspension et
revient au label `end`. Il laisse volontairement la variable scriptée
`suspend` à 1. Ce décalage est inhabituel mais nécessaire pour que la branche
`OnAlarm()` officielle puisse encore reconnaître l'état dormant, appliquer son
attente sur la valeur 6 et rejoindre `vybeh`.

Mettre aussi `suspend = 0` sans rejoindre `vybeh` casserait la seule transition
officielle vers `z2_agresor2`. Aller directement à `vybeh` inventerait au
contraire une attaque immédiate, sans la garde de valeur 6 et sans événement
d'alarme. Les deux options sont donc écartées.

En carnage, le script désactive signaux et Whenevers avant de se suspendre : le
prototype reste inerte et ne réintroduit pas l'acteur.

## Risques et tests

- vérifier si un acteur physiquement réveillé mais dont le drapeau local vaut 1
  traite bien ensuite une alarme une seule fois ;
- ouvrir `Mesh24` avant/après une alarme et pendant les deux valeurs de jeu 6 ;
- confirmer que `z2_agresor2` ne part qu'au moment de la branche officielle ;
- tester les portes déjà ouvertes, les signaux répétés et les alarmes 1/32/64 ;
- couvrir solo, coop, carnage et sauvegarde/reprise.

Si le moteur réexécute l'initialisation, ignore l'alarme après ce réveil ou
produit une double route, abandonner ce prototype. La variante agressive
`goto vybeh` ne doit pas être substituée automatiquement.

## Sources internes

- `.analysis/scripts/sabre/Scripts/brest/Mesh24.scr`
- `.analysis/scripts/sabre/Scripts/brest/z2_agresor1.scr`
- `.analysis/scripts/sabre/Scripts/brest/z2_agresor2.scr`
- `.analysis/scripts/sabre/Scripts/Co_brest/Mesh24.scr`
- `.analysis/scripts/sabre/Scripts/Co_brest/z2_agresor1.scr`
- les neuf autres destinataires du signal 1 dans les deux dossiers

