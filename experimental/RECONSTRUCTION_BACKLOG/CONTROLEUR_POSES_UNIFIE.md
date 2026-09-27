# Attachement, temps et poses dans une même mémoire native

**27 septembre 2026.** Les appels d'[attachement](ATTACHEMENT_ANIMATION_NATIF.md),
de [progression temporelle](TEMPS_ANIMATION_NATIF.md) et de
[pose](POSES_PARTIELLES_NATIVES.md) sont maintenant raccordés dans **la même
machine émulée et sur les mêmes objets**. Ce n'est toujours pas une scène chargée.

## Chaîne effectivement exécutée

Le banc attache d'abord les clips par `SetAnimation` dans les huit emplacements,
avec les vraies recherches, références et structures de cible. Il appelle
ensuite `0x10020150`, qui parcourt lui-même ces structures et appelle
`0x1001eed0`. Le calcul de pose parcourt les canaux originaux complets déjà
attachés ; il ne reçoit pas des valeurs pré-échantillonnées ni des pistes
fabriquées par le banc de pose précédent.

Le code de fin de pose est exécuté jusqu'au retour, mais les branches vers
des callbacks sont interdites. Les cibles n'ont aucun callback ni pose
supplémentaire. Le chemin de conversion d'une rotation sous forme matricielle
reste fermé : les rotations initiales sont explicitement des quaternions.
La source LS3DF reste épinglée à
`12c61eed2aec0c45700ad0a5ddfd7cbb3cbf0ea15ec67de155790bb24e7756ee`.

Après l'attachement, les transformations de repos fournies sont inscrites
**une seule fois** comme condition de diagnostic. Elles ne sont plus réinitialisées
à chaque mesure : la mémoire native conserve les poses d'une mise à jour à
l'autre. Cette condition ne prétend pas être celle choisie réellement par le
jeu. Les modes 1 et 2 sont eux aussi des paramètres explicites du contrôle,
pas une lecture des propriétés d'une ressource chargée.

La référence indépendante utilise les deux clés originales encadrant le temps
pour le calcul Python déjà recoupé ; seul ce calcul de référence utilise une
fenêtre. La routine native conserve les canaux complets. Les références de
temps, d'attachement et de pose sont comparées ensemble après chaque mise à jour.

## Ordre observé aux frontières

L'ordre natif est : avancer les temps actifs → calculer les poses → traiter
la fin ou la boucle. Il en résulte notamment :

- à la frontière d'une animation non bouclée, la pose terminale est appliquée
  **avant** la désactivation de la piste ;
- en mode boucle, cette pose est calculée avant la soustraction d'une durée ;
  le compteur peut être revenu à zéro alors que la cible montre encore la fin ;
- un appel de pas nul sur un contrôleur propre ne rééchantillonne pas cette
  pose au début de la boucle ;
- un premier appel de pas nul après attachement calcule en revanche la pose,
  car l'attachement a marqué le contrôleur pour recalcul ;
- les pistes inactives ou de poids nul ne modifient pas leurs canaux, et les
  cibles/canaux absents conservent leur état antérieur ;
- le bouclage reste une correction unique, pas un modulo arbitraire.

Ce sont des contrats de calcul contrôlés, **pas un défaut visuel reproduit en jeu**.
L'horloge réelle, les appels de rafraîchissement et la sélection des clips par
les actions du joueur peuvent modifier la séquence d'appels observée.

## Résultats

`native-unified-animation-ticks-20260927.json` :

- témoins inventés : **22 séquences**, **168 mises à jour**, **144 appels
  de pose**, **285 canaux appliqués** ;
- deux variantes de mains Benelli avec l'arme, FG42 et MG34 modernes :
  **80 séquences**, **720 mises à jour**, **8 706 appels de pose**,
  **15 856 canaux appliqués** ;
- résidu maximal des poses : **zéro** sur les deux corpus.

Les neuf clips de chaque banque sont contrôlés séparément en modes 1 et 2,
puis en deux configurations de chevauchement avec huit clips simultanés.
Cette combinaison est un témoin, pas une affirmation sur une transition
réellement déclenchée par le client. Treize nouveaux tests protègent
persistance, ordre des frontières, poids nul, refus et barrières d'exécution.

Les entrées, structures de liaison, références et champs hors temps/pose sont
préservés. Les mises à jour sont bornées à 1 024 pas non négatifs de 0 à
10 000 unités, deux millions d'instructions et dix secondes par appel.
Les limites d'attachement restent celles du banc associé.

```powershell
.\.venv\Scripts\python.exe tools/animation_tick_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/controleur-poses-nouveau.json'
```

Rapport neuf obligatoire. Ni chargeur natif, pose supplémentaire, callback,
caméra, peau, rendu, audio ou jeu n'est exécuté. La relocalisation des clips
et l'allocation bornée de cibles restent explicitement simulées. La chaîne
de [matrices et peau](CHAINE_ANIMATION_MAINS.md) antérieure reste une preuve
distincte ; aucune jouabilité ni validation de scène n'est annoncée.
