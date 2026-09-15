# Étude expérimentale — son de l'explosion du dépôt de Burgundy 3

État : analyse statique et maquette additive désactivée, 14 septembre 2026.
Aucun script commercial, binding ou installateur n'est modifié. La règle
générale est définie dans
[`../PRINCIPE_RECONSTRUCTION_ADDITIVE.md`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md).

## Verdict

Les trois signaux 10 n'ont pas la même valeur archéologique :

- les deux signaux de la route maquis/cinématique sont des **résidus d'un
  protocole remplacé** par l'événement global `OnCutscene(4)` ;
- le signal de `DESTROY_DMG` est un **indice crédible de son composite manquant
  hors cinématique**, car cette branche ne lance jamais la cinématique 4 ;
- aucun élément ne permet de conclure que le son moteur de `MakeExplosion` est
  absent. Ce qui pourrait manquer est uniquement la couche composée des neuf
  frames pilotées par `snd_vybuch_paliva.scr`.

Ajouter naïvement `OnSignal(10)` au récepteur est rejeté : la route cinématique
pourrait déclencher la même séquence jusqu'à trois fois. Une maquette sûre du
point de vue du routage est possible avec un **nouveau signal 11 réservé à la
branche directe**, tout en laissant la branche release inchangée.

## Les trois émissions commerciales

### 1. `bur3_maquis01.scr` : juste avant la mort du dépôt

Lorsque le tir de fusée ou le signal 22 déclenche le maquis, le script :

1. enregistre la valeur 70 à 1 ;
2. attaque le dépôt et attend une seconde ;
3. si le dépôt vit encore, envoie le signal 10 à `e_treeb_160` ;
4. force ensuite l'état du dépôt à zéro.

La mort appelle `bur3_vybuch.scr::OnDeath()`. Comme la valeur 70 vaut 1, ce
dernier lance immédiatement `CSC_RunCutscene(4)`. Le récepteur sonore reçoit
alors directement l'événement global `OnCutscene(4)` et joue déjà ses neuf
sons. Le signal 10 préalable n'est donc pas nécessaire au résultat actuel.

### 2. `bur3_vybuch.scr::OnCutscene(4)` : pendant le même événement

Le contrôleur de l'explosion envoie encore le signal 10 à `e_treeb_160` au
début de son propre `OnCutscene(4)`. Au même moment,
`snd_vybuch_paliva.scr::OnCutscene(4)` active :

- `s_ex_far`, `s_ex_near` et `s_ex_in` ensemble ;
- `s_vrz1`, `s_vrz2`, `s_vrz3` à 150/150/100 ms ;
- `s_kus1`, `s_kus2`, `s_kus3` à 100 ms d'intervalle.

Le signal ne transporte donc aucune information que le récepteur ne possède
pas déjà par l'événement de cinématique. C'est le vestige le plus net d'un
ancien déclenchement par signal.

### 3. `DESTROY_DMG` : destruction directe

Si le dépôt meurt alors que la valeur 70 n'est pas 1, `OnDeath()` rejoint
`DESTROY_DMG` au lieu de lancer la cinématique. Cette branche :

- envoie le même signal 10 ;
- produit les explosions moteur et les particules sur la caméra et le dépôt ;
- ne génère aucun `OnCutscene(4)`.

Le signal est donc orphelin ici et seulement ici. Sa position juste avant les
explosions rend plausible l'intention de réutiliser le mix composite hors
cinématique. Elle ne prouve ni le volume souhaité, ni que ce mix doive se
superposer au son propre de `MakeExplosion`.

## Pourquoi `OnSignal(10)` est dangereux

Dans la route maquis normale, un tel handler pourrait recevoir :

1. le signal du maquis avant `SetActorState(sklad, 0)` ;
2. l'événement `OnCutscene(4)` qui joue déjà le mix ;
3. le second signal émis dans le `OnCutscene(4)` du contrôleur d'explosion.

L'ordre exact entre événements et la sémantique d'un second `FRM_SetOn(true)`
sur un son déjà actif ne sont pas documentés. Il peut en résulter redémarrage,
superposition, séquence décalée ou simple no-op suivant le moteur. L'absence de
certitude suffit à rejeter ce raccord.

## Comparaison des variantes

### Solo Sabre Squadron

Le récepteur `e_treeb_160` est lié à `snd_vybuch_paliva.scr`. La route maquis
choisit la cinématique via la valeur 70 ; la destruction par dégâts choisit la
branche directe. C'est la seule variante examinée qui conserve à la fois les
trois signaux 10 et le séquenceur sonore à neuf frames.

### Co_Burgundy3

La conversion coop réécrit le flux : le maquis envoie le signal 1 à
`BUR3_vybuch`, puis ce contrôleur exécute directement explosions et particules.
Elle ne contient ni `snd_vybuch_paliva.scr`, ni référence à `e_treeb_160`, ni
cinématique 4 pour cette destruction. Ce choix confirme une **refonte**, mais
ne permet pas de décider si la couche sonore solo directe était volontairement
abandonnée ou oubliée.

### Burgundy3_mp

Cette carte multijoueur ne possède qu'un registre minimal et ne conserve pas
la logique de mission étudiée. La présence géométrique du nom `e_treeb_160`
dans son arbre n'est pas une preuve de binding ou de protocole sonore.

## Modèles sonores voisins

Les scripts ambiants de Burgundy 3 (`bur3_snd_vrzik`, `bur3_SND_stromy`,
`bur3_SND_sisky`, `bur3_snd_bunkr`) activent des frames sonores par
`FRM_SetOn(..., true)` depuis une boucle normale, sans cinématique.

Le contrôleur `Brest/hromy.scr` fournit un précédent plus proche : son
`OnSignal(1)` active directement plusieurs frames sonores dans un bloc. Cela
montre que l'API sonore fonctionne hors `OnCutscene`. Aucun précédent voisin
n'atteste toutefois un dédoublonnage automatique lorsqu'un signal et une
cinématique activent la même séquence.

## Proposition additive à deux branches

| Branche | Condition | Comportement |
| --- | --- | --- |
| release cinématique | valeur 70 = 1 | flux commercial inchangé ; `OnCutscene(4)` reste l'unique autorité sonore utile |
| additive directe | valeur 70 != 1 et entrée dans `DESTROY_DMG` | conserver le signal 10 historique sans handler, puis envoyer un nouveau signal 11 monostable vers le mix |

Le signal 11 n'est envoyé par aucune route commerciale vers ce récepteur et
n'est pas utilisé par son script. Dans la maquette, il est ajouté uniquement à
`DESTROY_DMG`; les deux sites cinématiques continuent d'envoyer leur signal 10
ignoré. Cette séparation empêche structurellement le double déclenchement par
la cinématique sans remplacer un comportement release.

La maquette
[`PROTOTYPE_ADDITIF_DIRECT_SIGNAL11.scr.disabled`](PROTOTYPE_ADDITIF_DIRECT_SIGNAL11.scr.disabled)
est un fragment de delta, pas un script autonome. Elle duplique volontairement
le petit corps sonore au lieu de refactorer `OnCutscene(4)`, afin que le chemin
release reste textuellement intact.

## Limites de la preuve

La sûreté démontrée est celle du **routage** : signal distinct, branche
exclusive, réception monostable, aucun changement du chemin cinématique. Le
rendu acoustique n'est pas démontré statiquement. Le prototype doit rester
désactivé tant que le mix hors cinématique, la portée et le cumul avec les sons
de `MakeExplosion` ne sont pas validés en jeu.

## Protocole de test

1. Baseline maquis : tracer valeur 70, deux signaux 10, événement cinématique 4
   et neuf activations sonores ; chaque couche doit être entendue une seule fois.
2. Baseline directe : détruire le dépôt sans le maquis et relever le son moteur,
   les particules et l'absence de séquence composite.
3. Maquette, route maquis : confirmer zéro signal 11 et une restitution
   strictement identique à la baseline cinématique.
4. Maquette, route directe : confirmer un seul signal 11 et une seule séquence
   composite, sans modification des explosions ni des objectifs.
5. Tester la course où le joueur détruit le dépôt pendant la seconde d'attente
   du maquis. La valeur 70 doit sélectionner la cinématique et aucun signal 11
   ne doit partir.
6. Répéter après sauvegarde/reprise avant le tir, après valeur 70 = 1 et pendant
   la cinématique. Aucun événement ne doit être réarmé.
7. Comparer casque/haut-parleurs, intérieur/extérieur et distances proche,
   moyenne et lointaine ; surveiller saturation, phase et redémarrage de clips.
8. Répéter les dégâts sur le dépôt mort et toute tentative de relance de la
   cinématique. Le mix additif doit rester monostable.

Acceptation : la branche cinématique reste identique ; la branche directe joue
au plus une séquence supplémentaire ; aucun objectif, sauvegarde, caméra,
particule ou route du maquis ne change. Au premier double son ou écart de
progression, abandonner la maquette.

## Sources internes

- `.analysis/scripts/sabre/Scripts/Burgundy3/bur3_maquis01.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy3/bur3_vybuch.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy3/snd_vybuch_paliva.scr`
- variante `.analysis/scripts/sabre/Scripts/Co_Burgundy3/`
- arbres `Burgundy3`, `Burgundy3_mp` et `Co_Burgundy3`
- modèles `Burgundy3/bur3_snd_*.scr`, `bur3_SND_*.scr` et
  `Brest/hromy.scr`
