# Étude expérimentale — activateurs legacy de Normandy 1

État : paire complète reproductible désactivée, 25 septembre 2026. Aucun binding,
script actif, registre, installateur ou fichier du jeu n'est modifié.

Cette étude applique le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md) :
les activateurs partagés et le réveil par N01 restent la baseline. Seule
l'activation, en solo, du détecteur 30 m déjà présent dans N24/N25 est proposée
comme option expérimentale.

## Verdict

Le registre final a déjà consolidé plusieurs détecteurs sur des scripts communs :

- `N12_A1`, `N12_A2`, `N12_A3` et `N12_A4` utilisent tous
  `X_N1_N12_A1.scr` ;
- `N14_A1`, `N14_A2` et `N14_A3` utilisent tous `X_N1_N14_A1.scr` ;
- `N17_A1` et `N17_A2` utilisent tous `X_N1_N17_A1.scr`.

Cette consolidation doit rester intacte. Les fichiers orphelins N12/N13/N14/N17
ne justifient aucun binding supplémentaire : certains emplacements ont disparu,
un fichier est redondant et un autre envoie un signal que sa cible ne traite pas.

N24 et N25 offrent en revanche une branche additive bornée. Ils sont déjà liés
à leurs scripts acteurs, reçoivent le signal 1 de N01 en solo et contiennent
chacun un détecteur `_PlayerInRange(30)`. La release n'active ce détecteur que
pour les types de partie 3/7. Une copie expérimentale peut l'activer aussi en
solo tout en conservant le signal, les bindings et les chemins actuels.

## N24/N25 : distinguer les deux couches historiques

Les anciens fichiers `X_N1_N24_A1.scr` et `X_N1_N25_A1.scr` ne sont pas les
détecteurs 30 m. Ils dépendent de frames porteuses aujourd'hui absentes et
déclenchent respectivement à 2 m et 3 m :

| Fichier orphelin | Condition | Effet |
| --- | ---: | --- |
| `X_N1_N24_A1.scr` | joueur à moins de 2 m du porteur perdu | signal 1 à N24 |
| `X_N1_N25_A1.scr` | joueur à moins de 3 m du porteur perdu | signal 1 à N25 |

Leur position ne peut pas être déduite de leur nom. Ils ne doivent pas être
recréés près de N24/N25 : cela déplacerait un trigger de niveau sans preuve.

Les scripts acteurs actifs `X_N1_N24.scr` et `X_N1_N25.scr` possèdent leur
propre condition à 30 m, calculée directement depuis la position de l'acteur.
Elle réveille l'acteur sur place puis rejoint `end`. En types 3/7, cette branche
est déjà activée. En solo elle est explicitement désactivée.

## Baseline solo par N01

`X_N1_N01.scr` envoie le signal 1 à N24 et N25 lorsqu'il passe en alarme alors
que le joueur est à moins de 45 m. Les handlers actifs font davantage qu'un
simple réveil :

- N24 rejoint `N24_1`, réactive ses événements et se tourne vers le joueur ;
- N25 attend 3 s, rejoint `N25_1` puis `N25_2`, réactive ses événements et se
  tourne vers le joueur.

Les chaînes `N24_1`, `N25_1` et `N25_2` sont encore présentes une fois chacune
dans `check2.bin`. La branche release possède donc ses routes. L'option 30 m ne
les remplace pas : si N01 s'alarme ensuite, son signal doit toujours pouvoir
déclencher ces déplacements.

La maquette
[`PROTOTYPE_SOLO_PROXIMITY_DELTA.scr.disabled`](PROTOTYPE_SOLO_PROXIMITY_DELTA.scr.disabled)
décrit uniquement le bloc de mode à remplacer dans des copies de test de
`X_N1_N24.scr` et `X_N1_N25.scr`. Les bindings restent :

```text
N24 -> X_N1_N24.scr
N25 -> X_N1_N25.scr
```

L'option est donc additive sur le comportement, pas additive par nouveau
détecteur de scène.

## Classement des autres fichiers

| Fichier orphelin | Constat | Décision |
| --- | --- | --- |
| `X_N1_N12_A5.scr` | même protocole N12/N13 que le script commun ; porteur A5 absent | aucune maquette sans position |
| `X_N1_N13_A2.scr` | signal 1 à N13 à 1 m ; porteur absent | aucune maquette sans position |
| `X_N1_N13_A3.scr` | signal 1 à N13 à 2 m ; porteur absent | aucune maquette sans position |
| `X_N1_N14_A2.scr` | signaux 1 à N14/N15, rayon 3 m | doublon fonctionnel remplacé par le commun déjà lié à l'acteur N14_A2 |
| `X_N1_N17_A2.scr` | signal 2 à N17 seulement | variante cassée/remplacée : N17 traite les signaux 1 et 5, pas 2 |
| `X_N1_N24_A1.scr` | signal 1 à N24 à 2 m ; porteur absent | ne pas inventer sa position |
| `X_N1_N25_A1.scr` | signal 1 à N25 à 3 m ; porteur absent | ne pas inventer sa position |

Il faut parler de « porteur absent ou non libre » avec précision : les acteurs
`N14_A2` et `N17_A2` existent, mais sont déjà liés aux scripts communs release.
Ils ne sont pas disponibles pour réattacher les variantes de même suffixe.

## Risques et protocole de test

### Réalisation hors jeu du 25 septembre 2026

Le profil `normandy-inner-guards-proximity` du
[catalogue](../reconstruction-variants.json) exporte les deux scripts ensemble,
jamais séparément. Il applique une forme plus petite du delta proposé : seule
la ligne `SetWhenever(player, false)` devient `true` dans chaque acteur.
La branche commerciale des types 3/7 et son saut vers `dalej` restent ainsi
octet pour octet identiques. Le changement concerne la branche de repli des
autres types, dans ce laboratoire destiné au solo; il ne constitue pas une
validation de ces autres modes de partie.

Les six sources sont épinglées : les deux acteurs, l'émetteur N01, le registre,
les acteurs sérialisés et les checkpoints. Aucun nouveau porteur, signal,
position ou nom de route. Le générateur vérifie les deux liaisons et les trois
routes existantes. Le détecteur à 30 m ne reçoit pas de nouveau désarmement :
ses interactions avec le signal d'alarme restent à éprouver, comme ci-dessous.

| Sortie complète locale | Octets | SHA-256 |
|---|---:|---|
| N24 | 1857 | `d8c31825aa45b46c0ded16a2a19cd4ad58de9badc3915bdffd5281f397be6ed0` |
| N25 | 1915 | `f89dcd7e860f8986cf1793280131e89cf1fa2350b477f6a5f472bcbc3b566252` |

Le laboratoire inerte comprend 183 fichiers par branche, 157 scripts
accessibles sur 166 présents et les huit objectifs commerciaux conservés.
Espaces : `H2Lab_normandy_f5adb4591fd1_B` et `_V`. Deux tests de contrat et
l'inspection des deux diff confirment que les routes et les gestionnaires ne
changent pas; ils ne démontrent pas l'ordonnancement des événements en moteur.

Le registre libre installé est différent (9007 octets contre 8963 dans
l'archive). Le contrôle strict refuse donc ce profil sur l'installation
actuelle. Le laboratoire a été créé avec exclusion explicite des surcharges,
dont les empreintes sont conservées dans son rapport; aucune compatibilité avec
la mission installée n'est revendiquée.

### Validation moteur — toujours en attente

La proximité 30 m et le signal N01 peuvent se produire dans le même instant.
Le moteur doit démontrer que le réveil est idempotent et que la branche
`alarmed` reste exécutable après la branche `player`.

1. Option coupée : comparer la trace à la release en solo et en types 3/7.
2. Option active, entrée à 30 m sans alarme : N24/N25 se réveillent sur place,
   sans déplacement N24_1/N25_1/N25_2 anticipé.
3. Déclencher ensuite l'alarme de N01 à moins de 45 m : les deux signaux 1 et
   les routes commerciales doivent encore s'exécuter une seule fois.
4. Tester alarme et franchissement des 30 m dans la même fenêtre ; aucun double
   mouvement, blocage ou réarmement après sauvegarde/reprise.
5. Tester mort de N01, N24 ou N25 avant activation et après le premier réveil.
6. En types 3/7, confirmer une trace strictement identique à la release.

Si le handler de proximité consomme l'état du script et empêche ensuite le
signal N01, l'option échoue : elle ne doit pas être compensée en supprimant la
route release.

## Sources internes

- registre effectif `missions/normandy/scripts.dta` ;
- scripts Base `X_N1_N01.scr`, `X_N1_N24.scr`, `X_N1_N25.scr` ;
- sept fichiers activateurs orphelins cités dans le tableau ;
- `actors.bin`, `scene2.bin` et recherche brute dans `check2.bin`.
