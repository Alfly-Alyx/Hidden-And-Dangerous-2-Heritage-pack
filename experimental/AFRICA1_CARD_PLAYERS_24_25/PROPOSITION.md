# Africa 1 — joueurs de cartes AF1_24 et AF1_25

État : **activité attestée, nettoyage de sécurité ajouté**, 14 septembre 2026.
Le prototype commun est désactivé ; aucune mission n’a été compilée ou installée.

## Verdict

Les deux scripts conservent le même bloc complet et symétrique : sortir les
cartes avec `Card(1)`, puis appeler `Card(2)` toutes les 1,5 seconde. La commande
est active dans Czech 3 et Castle 2 ; la reconstruction de la partie est donc
bien plus solide qu’une animation au nom inconnu.

Le vestige Africa 1 ne ferme toutefois jamais l’activité. La variante sûre
ajoute `Card(0)` au début de l’alarme, du signal 10 et de `OnDeath()`. La fermeture
d’alarme est directement justifiée par Castle 2 ; les deux autres fermetures
sont des ajouts de sûreté clairement séparés de la séquence historique.

## Inventaire des preuves Base et Patch

| Élément | Base | Patch effectif | Conclusion |
| --- | --- | --- | --- |
| binding | `AF1_24 -> AF1_24.scr`, `AF1_25 -> AF1_25.scr` | inchangé | propriétaires vérifiés |
| posture initiale | `%%sedimL`, acteurs suspendus avec événements actifs | logique identique | joueurs déjà assis |
| réveil | `_PlayerInRange(20)` vers `ACTIVATE` | logique identique | activation locale des deux scripts |
| bloc cartes | `Card(1)`, label `LOOP`, `Card(2)`, délai 1500, boucle, tout commenté | même bloc | intention symétrique directe |
| alarmes | arrêt d’animation, réveil, stop, mise debout et comportement d’alerte | logique identique | priorité à conserver |
| signal 10 | arrêt d’animation, mise debout, regard joueur, fin du script | logique identique | autre sortie d’activité à nettoyer |
| mort | `EndScript()` seulement | logique identique | aucun nettoyage des cartes |

La comparaison ligne à ligne des copies Base et Patch d’AF1_24/25 ne montre
aucune différence sémantique. Les copies Patch restent néanmoins la base des
essais, puisqu’elles sont la couche effective.

## Précédents `HUMAN_ACTIVITY_Card`

- Czech 3 utilise activement `Card(1)` puis `Card(2)` dans les deux scripts de
  porteurs coordonnés.
- Castle 2, scripts C2_11 et C2_12, exécute des cycles `Card(1)` / plusieurs
  `Card(2)` / `Card(0)`.
- Surtout, chacun appelle `HUMAN_ACTIVITY_Card(0)` comme première instruction de
  `OnAlarm()`, avant de mettre l’acteur debout.

Castle 2 ne prouve pas la fermeture sur mort. Cet ajout vise seulement à libérer
les cartes ou l’état d’activité avant `EndScript()` ; il doit être testé.

## Exact historique et ajouts de sûreté

### Exactement conservé

- les deux acteurs utilisent le même cycle ;
- `Card(1)` est appelé une fois à l’activation ;
- `Card(2)` se répète avec un délai de 1 500 ms ;
- aucun nouveau déplacement, dialogue, objet ou signal partenaire n’est ajouté.

### Ajouté pour la sûreté

- un verrou local `cards_active` ;
- `Card(0)` au début de `OnAlarm()` ;
- `Card(0)` au début du signal 10 ;
- `Card(0)` au début de `OnDeath()`.

Le verrou évite d’appeler `Card(0)` sur un acteur qui n’a jamais commencé la
partie. Aucun signal croisé n’est inventé entre 24 et 25 : si l’un meurt sans
alarmer l’autre, le survivant peut continuer son cycle. Ce cas doit être observé
avant de justifier un éventuel coordinateur.

## Niveaux de spéculation

- **Faible** : les deux acteurs devaient jouer aux cartes ; leurs blocs sont
  complets, identiques et la commande est active ailleurs.
- **Faible** : `Card(0)` avant l’alarme ; précédent exact dans Castle 2.
- **Faible à moyenne** : `Card(0)` dans le signal 10 ; c’est une sortie nette
  avant un changement de posture.
- **Moyenne** : `Card(0)` dans `OnDeath()` ; nettoyage logique mais non attesté
  dans les exemples Castle 2.
- **Moyenne** : la proximité seule maintient les deux cycles visuellement
  synchrones, car aucun coordinateur Africa 1 n’est conservé.

## Prototype isolé

`PROTOTYPE_SAFE_CARD_PAIR.scr.disabled` décrit le même delta à appliquer aux
copies Patch d’AF1_24 et AF1_25. Il ne remplace pas leurs gestionnaires : il
ajoute seulement le verrou et la fermeture en tête, puis réactive le bloc
`ACTIVATE` commenté.

Le délai de 1,5 seconde est conservé et les événements humains restent actifs.
La boucle n’ajoute donc ni suspension, ni désactivation d’alarme ou de signaux.

## Activation et désactivation

1. Dupliquer Africa 1 et copier les deux scripts Patch ensemble.
2. Appliquer le même delta aux deux ; ne pas tester un cycle actif contre un
   second script release lors du test visuel final.
3. Ne modifier ni le rayon 20, ni `%%sedimL`, ni les chemins d’alarme.
4. Tester d’abord le cycle sans ennemis, puis les interruptions.
5. Désactivation : restaurer les deux scripts Patch originaux. Aucun frame,
   binding, objet ou signal supplémentaire n’est nécessaire.

## Risques

- les appels indépendants peuvent se décaler et donner une partie désynchronisée ;
- `Card(2)` toutes les 1,5 seconde peut être trop rapide pour l’animation finale ;
- `Card(0)` dans `OnDeath()` peut arriver trop tard pour retirer un prop ;
- un survivant peut continuer à jouer seul si la mort du partenaire ne produit
  aucune alarme reçue ;
- reprise de sauvegarde au milieu de la boucle avec verrou incohérent ;
- fermeture puis `HUMAN_SetAnim("", ...)` pouvant provoquer un saut de posture.

## Protocole de test en jeu

1. Baseline : confirmer les deux poses assises, leur distance et l’activation
   lorsque le joueur entre dans le rayon 20.
2. Variante : observer au moins dix appels `Card(2)` et relever synchronisation,
   cartes visibles, mains, table et boucle.
3. Déclencher chaque alarme utile juste avant `Card(1)`, pendant `Card(2)` et
   pendant le délai ; les deux acteurs doivent fermer les cartes et suivre leurs
   comportements release sans retard.
4. Envoyer le signal 10 aux deux ensemble puis séparément ; aucune carte ne doit
   rester et la mise debout doit rester correcte.
5. Tuer 24, puis 25, pendant chaque phase. Vérifier le corps, les props et le
   comportement du survivant.
6. Tester un seul acteur dans le rayon 20 si leur placement permet de créer ce
   décalage, puis entrer dans le rayon du second.
7. Sauvegarder/reprendre avant l’activation, cartes sorties, pendant la boucle et
   après une alarme.
8. Restaurer les deux scripts et confirmer la baseline assise sans cartes.

Critères d’arrêt : prop orphelin, acteur figé, alarme retardée, boucle non
interruptible, désynchronisation durable ou survivant jouant indéfiniment seul.

## Paire complète reproductible — 26 septembre 2026

Le profil `africa1-card-players-pair` produit ensemble AF1_24 (2705 octets) et
AF1_25 (2679 octets), depuis les deux sources Patch épinglées. L'export d'une
moitié seulement est refusé par le générateur. Le registre et les deux acteurs
sont contrôlés; aucune liaison supplémentaire n'est créée.

Les sorties alarme/signal 10/mort désarment d'abord la proximité, puis effacent
le verrou avant Card(0). L'activation désarme également la proximité avant le
cycle. La cadence historique 1500 est conservée, sans second coordinateur ni
nouveau signal entre les acteurs. Les réactions commerciales propres à chacun
restent distinctes. Ce nettoyage moderne nécessite toujours les observations
de props, de décès et de reprise décrites ci-dessus.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA1/AF1_24.scr` ;
- `.analysis/scripts/patch/SCRIPTS/AFRICA1/AF1_24.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA1/AF1_25.scr` ;
- `.analysis/scripts/patch/SCRIPTS/AFRICA1/AF1_25.scr` ;
- `.analysis/scripts/base/SCRIPTS/CASTLE2/C2_11.scr` ;
- `.analysis/scripts/base/SCRIPTS/CASTLE2/C2_12.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH3/R_cz3_nosic1.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH3/R_cz3_nosic2.scr` ;
- registre `Missions/AFRICA1/Scripts.dta` de `missions.dta`.
