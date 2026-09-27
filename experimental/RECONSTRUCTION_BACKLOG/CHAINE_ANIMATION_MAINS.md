# Chaîne native des animations Benelli vers les mains

**27 septembre 2026.** Les trois bancs indépendants sont désormais raccordés :
[canaux et poses](POSES_PARTIELLES_NATIVES.md) →
[matrices du squelette](PALETTE_MAINS_NATIVE.md) →
[déformation CPU](DEFORMATION_MAINS_NATIVE.md).
Les neuf animations commerciales et les deux mains épinglées sont lues en
mémoire ; aucune clé, géométrie ou matrice commerciale n'est publiée.

## Une condition initiale explicite, pas une preuve de lecture en jeu

**Chaque mesure repart de la pose de repos du modèle de mains.** C'est une
condition de diagnostic volontaire : elle ne prétend pas reproduire la pose
précédente choisie par le client. Les pistes et canaux absents conservent
exactement cette condition fournie. Ils ne sont pas ajoutés à l'animation.

Ce point est particulièrement important pour `aimshot`, sans piste de joint
de main : l'effet d'une transition après la visée dépend de l'état déjà présent.
Les contrôles ci-dessous ne démontrent donc ni ce passage ni la continuité
entre armement, visée, tir, incident, rechargement et désarmement.

Les 37 nœuds des mains sont examinés, y compris la racine `a` quand elle reçoit
un canal. La pose de cette racine est calculée, mais **sa transformation de
rendu n'est pas appliquée** par le noyau de peau relatif. Les cibles d'arme
sont reconnues et distinguées ; elles ne sont pas comptées comme des joints
de main. Les doublons et noms non résolus sont refusés.

## Passage des clés sans approximation supplémentaire

Le banc de pose accepte au plus trois clés par canal. Le raccordement lui
fournit les **deux clés originales encadrant le temps demandé**, avec leurs
repères et valeurs inchangés, ou la clé tenue à une extrémité. Il n'invente
pas une nouvelle clé interpolée et ne normalise pas les valeurs sources.

Le choix utilise l'indice entier natif `temps / 40`. Les décalages float32,
interpolations et normalisations restent exécutés dans les routines d'origine.
Les tests indépendants comparent cette fenêtre au canal entier, jusqu'à
180 clés irrégulières, à leurs frontières et dans le domaine temporel autorisé.
Le banc d'échantillonnage antérieur a déjà comparé les canaux Benelli complets
au calcul natif ; ce raccordement ne remplace pas cette preuve par un lecteur
de valeurs générées.

La pose résultante alimente les joints identifiés par leur véritable numéro,
puis les matrices et le noyau CPU. Les trois phases utilisent des mémoires
émulées indépendantes avec leurs garde-fous propres ; il ne s'agit pas d'un
objet chargé et animé dans une scène réelle. Ni le contrôleur de durée,
ni les événements, ni le rendu ne sont exécutés par ce raccordement.

## Résultats disponibles

`benelli-native-pose-chain-boundaries-20260927.json` couvre cinq instants
par animation et variante : zéro, unité 1, milieu, unité précédant la fin,
fin exacte. Soit **90 échantillons**, **3 330 poses de nœuds**,
**3 240 joints** et **93 015 sommets déformés**.

Les 3 320 canaux présents sont appliqués ; 1 500 poses de nœuds sans canal
conservent la condition de départ déclarée. Ce compte est une observation,
pas un comblement de pistes manquantes.

Résidus maximaux : **zéro** pour les poses, **3,577 × 10⁻⁷** pour les matrices,
**zéro** pour la déformation alimentée par ces matrices. Dix tests nouveaux
utilisent uniquement des données inventées et vérifient fenêtres, conservation,
refus et comptes d'échantillonnage.

Le mode plus dense `half-frames` est disponible. Il examine chaque repère et
chaque milieu de repère ; son nom ne définit aucune fréquence en secondes.
Seul un rapport effectivement terminé peut être utilisé comme preuve de ce mode.

## Reproduction

```powershell
.\.venv\Scripts\python.exe tools/benelli_pose_chain_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --sampling boundaries --json-output '.analysis/chaine-mains-nouveau.json'
.\.venv\Scripts\python.exe tools/benelli_pose_chain_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --sampling half-frames --json-output '.analysis/chaine-mains-dense-nouveau.json'
```

Les rapports doivent être neufs. L'installation personnelle reste en lecture
seule. **Ni jouabilité ni validation moteur ne sont acquises** : initialisation
effective, transitions, liaison au modèle chargé, racine/caméra, sons,
événements, sauvegardes et multijoueur restent des obligations distinctes.
