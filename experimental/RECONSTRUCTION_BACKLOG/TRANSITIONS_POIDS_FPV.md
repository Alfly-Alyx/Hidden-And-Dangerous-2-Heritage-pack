# Transitions FPV : poids et retrait des anciennes pistes

**27 septembre 2026.** Ce banc exécute le contrôleur de mélange du client
et le réglage des poids du modèle dans `LS3DF.dll`. Le détachement et le
rafraîchissement restent des appels enregistrés sans exécution. Il complète les
[poses partielles](POSES_PARTIELLES_NATIVES.md), la
[progression temporelle](TEMPS_ANIMATION_NATIF.md) et la
[chaîne de calcul des mains](CHAINE_ANIMATION_MAINS.md).

## Source et domaine

Image privée décompressée du client 1.12, **8 101 888 octets**, SHA-256
`2c04629cf79b64c0c12f310187974f357ffbfc22bbc11f1488764cd078d3e7aa`.
L'image doit correspondre exactement avant import de l'émulateur.
La routine `0x491440…0x491631` est exécutée, avec des objets inventés.
La bibliothèque LS3DF est également épinglée, SHA-256
`12c61eed2aec0c45700ad0a5ddfd7cbb3cbf0ea15ec67de155790bb24e7756ee` ;
seul son réglage de poids `0x10034460…0x100344dd` est permis.
Aucun chargement Windows, point d'entrée du jeu, allocateur ou API système.

Quatre conditions sont fournies explicitement : activation globale, instance
active, animation courante présente, modèle présent. Si l'une manque, le
contrôleur ne change rien et ne demande aucune opération au modèle.

Le domaine du banc accepte un pas entier de 0 à 1 000 000, un poids dans [0,1],
un taux de 0 à 10, zéro à trois anciennes pistes et des emplacements distincts
de 0 à 7. Il ne prouve pas que le client crée toutes ces combinaisons en jeu.
Les pas négatifs, les doublons et les valeurs non finies sont refusés.

## Règles établies

Le facteur numérique exact est le float32 **0.0010000000474974513**.
Il ne suffit pas à qualifier l'unité de l'horloge qui produit le pas.

- Si le poids courant vaut déjà exactement 1 à l'entrée, toutes les anciennes
  pistes sont détachées **de la dernière à la première**. Aucun nouvel appel
  de réglage de poids ou de rafraîchissement n'est demandé dans cette branche.
- Sinon, le poids courant augmente de `pas × taux × facteur`, avec plafond 1,
  puis un réglage de poids est demandé pour son emplacement.
- Chaque ancienne piste diminue selon **son propre taux**. Un poids devenu nul
  ou négatif provoque son détachement et la réduction de la liste. Les autres
  pistes conservent leur ordre et reçoivent un réglage de poids.
- Une ancienne piste de taux zéro garde son poids pendant cette branche.
- La branche de progression se termine par une demande de rafraîchissement.
- **Atteindre 1 pendant le calcul ne déclenche pas immédiatement la branche
  d'effacement global.** Une ancienne piste encore positive peut survivre
  jusqu'à la mise à jour suivante, même si celle-ci a un pas nul.
- Un pas nul n'empêche pas de retirer une ancienne piste déjà de poids zéro,
  ni d'effacer la liste lorsque le poids courant vaut déjà 1.

Le code de changement d'animation voisin est également observé statiquement :
en cas de transition avec une ancienne animation active, il mémorise son
emplacement/taux/poids, puis initialise le nouveau poids à zéro et son taux à 5
(`0x493186…0x493198`). Sans ce cas, poids 1 et taux zéro
(`0x4931d3…0x4931e5`). Cette création de transition n'est pas exécutée par
le présent banc ; l'allocation et le choix de l'emplacement restent distincts.
Le [banc de sélection](SELECTION_PISTE_FPV.md) contrôle maintenant ce choix
et ces paramètres initiaux avec branche et liste fournies explicitement.
L'[attachement LS3DF](ATTACHEMENT_ANIMATION_NATIF.md) est vérifié séparément
sur les véritables pistes, dans des conteneurs synthétiques.

## Poids natifs, détachement et rafraîchissement enregistrés

Les trois méthodes virtuelles contrôlent destinataire, site appelant,
arguments et pile. Leur portée est distinguée :

- `+0x84` : animation nulle, emplacement, poids 1, mode 0 ;
- `+0x94` : emplacement et nouveau poids, transmis au **véritable réglage
  natif LS3DF**, qui écrit dans un contrôleur synthétique de huit pistes ;
- `+0x24` : demande de rafraîchissement du modèle.

Les écritures de poids et du drapeau de recalcul du contrôleur sont vérifiées,
ainsi que la conservation des autres pistes. Les méthodes de détachement et
rafraîchissement **ne sont pas exécutées** : leurs doubles retournent après
enregistrement. Aucun mélange visuel ou traitement d'événement n'est revendiqué.

Seuls le poids courant, la fin de liste, les enregistrements de cette liste,
les poids/drapeau du contrôleur synthétique et la pile peuvent être écrits.
Les identifiants d'animation sont conservés
pendant les décalages. Les autres champs et la table de méthodes en lecture
seule sont comparés après calcul. Limite : 12 000 instructions et une seconde
par cas ; contrôle x87 synthétique 0x027f.

## Résultats et reproduction

`fpv-native-blend-v2-20260927.json` : **393 cas**, **350 anciennes pistes retirées**,
**698 demandes de poids**, **350 demandes de détachement** et **316 demandes
de rafraîchissement**. Les 698 demandes de poids passent effectivement par
le réglage natif LS3DF. Les états et listes d'arguments concordent exactement
avec la référence indépendante. Le rapport v1, sans exécution de ce réglage,
reste conservé comme étape historique. Treize tests synthétiques couvrent les règles,
les limites d'entrée et les barrières d'exécution/écriture.

```powershell
.\.venv\Scripts\python.exe tools/fpv_blend_audit.py --image 'tmp/stock-menu-analysis.bin' --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/transitions-poids-nouveau.json'
```

L'image est privée, dérivée localement de l'exécutable épinglé ; elle n'est
pas fournie dans le dépôt. Rapport neuf obligatoire. Aucun jeu ni installateur
n'est lancé ou modifié. La politique de sélection des clips, leur attachement,
les poses supplémentaires, les événements et la continuité réelle restent à vérifier.
