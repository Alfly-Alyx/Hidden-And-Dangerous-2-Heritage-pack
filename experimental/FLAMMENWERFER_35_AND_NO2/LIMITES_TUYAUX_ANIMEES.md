# Enveloppes natives des tuyaux pendant les changements de clips

**27 septembre 2026.** Les limites sérialisées des tuyaux sont maintenant
reliées au calcul natif de leurs boîtes englobantes et sphères, puis comparées
aux sommets réellement déformés. **Ce contrôle local ne qualifie pas la visibilité
dans une scène chargée ni le rendu du jeu.**

## Raccordement réalisé

`four_ds_skin.py` restitue désormais, pour les calculs privés, la boîte de base
et les huit boîtes d'os lues dans le fichier ; elles ne sont pas ajoutées au
rapport publiable. Le payload du skin de tuyau est comparé octet pour octet
à celui de la racine `fpv_weapon` du modèle aplati.

Le nouveau `ls3d_skin_bounds_oracle.py` exécute le chemin borné de
`0x10052330`, avec ses transformations des huit coins de chaque boîte,
unions, centre et rayon. Les matrices de joints sont des données explicites
déjà calculées ; la recherche des os et la reconstruction de leurs matrices
ne s'exécutent pas dans ce même appel. Aucune allocation, scène, copie de
modèle, animation, déformation ou fonction graphique n'est appelée par ce
petit banc. La racine synthétique n'a pas de parent ; l'invalidation d'une
hiérarchie de scène complète n'est donc pas qualifiée.

Le contrôle composé emploie ensuite les [lectures persistantes avec changements
de clips](../RECONSTRUCTION_BACKLOG/ENCHAINEMENT_ANIMATIONS_NATIF.md). À chaque
avance, il lit les huit poses d'os, reconstruit leur palette native dans le
repère local du skin, calcule les limites natives et déforme les sommets des
deux LOD par le noyau natif. Chaque sommet doit être contenu à la fois dans
la boîte et la sphère, avec une tolérance préétablie de `2e-6`.

La racine est un visuel : la marche des ancêtres s'arrête à ce niveau. Les
huit joints indépendants produisent donc des matrices **locales au skin** ;
la transformation du visuel racine n'est pas ajoutée artificiellement comme
un neuvième os. Animation, palette, limites et skin utilisent encore des
émulateurs distincts, reliés par leurs valeurs contrôlées.

## Résultats

Rapport privé : `.analysis/skin-bounds-native-20260927.json`.

- **46 cas synthétiques** : 1 à 64 os, translations, rotations, cisaillements,
  échelles signées et boîte dégénérée ; calcul des limites conforme, écart nul.
- **8 séquences** sur les quatre banques F35/No. 2 × deux modèles de mains,
  couvrant les neuf clips dans les deux ordres et leurs changements.
- **352 instants**, **704 évaluations de LOD**, **304 128 sommets déformés**
  et **22 528 transformations de coins**.
- Écart maximal de palette : `2,981e-8`. Écarts des limites et du skin : zéro.
  Dépassements observés de la boîte et de la sphère : **zéro**.

Douze tests supplémentaires protègent calculs, données privées, refus des
domaines invalides, bornes d'exécution et détection des dépassements. Un cas
de test tient explicitement compte de l'arrondi float32 du rayon : une sphère
de rayon stocké `sqrt(3)` peut avoir un écart géométrique de `3,109e-8`, sans
changer le seuil préétabli du contrôle.

## Limites conservées

Ce travail concerne le tuyau, pas les limites cumulées de tous les visuels
de l'arme, des mains et du personnage. Le calendrier des poids reste un scénario
de diagnostic. La lecture des ressources, le clonage, les décisions clientes,
le calcul de visibilité de scène, les contacts pendant les mélanges et le
rendu complet ne sont pas exécutés ensemble. Aucun jeu ni installateur n'est
lancé ; les installations personnelles restent inchangées.

```powershell
.\.venv\Scripts\python.exe tools/skin_bounds_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/skin-bounds_nouveau.json'
```
