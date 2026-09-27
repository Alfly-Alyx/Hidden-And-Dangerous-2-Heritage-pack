# Calcul natif de déformation des mains

**27 septembre 2026.** Le noyau CPU de déformation est désormais reproduit
et comparé au code natif. Il reçoit des matrices déjà préparées : la
construction de ces matrices depuis une animation et un modèle chargé reste
une étape distincte, non qualifiée par ce banc.

## Correction du lecteur : deux bases d'indices différentes

Le créateur de visuel `0x10019750`, type 2, sélectionne la table `0x1009c5f8`.
Son entrée `+0x70` est le lecteur de peau `0x10053900` : il lit directement
les parents dans le descripteur `+0x80`, les matrices inverses de repos dans
des enregistrements de 96 octets, puis les paires de sommets sans conversion
(`0x10053af9…0x10053b07`). Cette partie est examinée **statiquement**, sans
appeler les allocations ou les lectures du moteur.

Le calcul `0x10065c60` soustrait une matrice et un octet aux pointeurs de
palette et de parents avant d'utiliser chaque indice. La construction de la
palette dans son appelant range, elle, les matrices dès l'élément zéro.
Il n'y a donc **pas de conversion à ajouter aux fichiers** :

- identifiant d'un nœud joint : base zéro, de 0 à N−1 ;
- indice d'os d'une paire de sommet : base un, de 1 à N ;
- parent : même base un, avec zéro comme absence de parent.

L'ancien contrôle du lecteur acceptait à tort l'indice zéro et refusait N.
Il est corrigé, ainsi que sa fixture inventée. Les mains réelles utilisent
des indices de 2 à 35 sur 36 os : cette particularité masquait l'erreur de
borne. Aucun octet des fichiers commerciaux n'est modifié.

## Calcul établi

Pour un sommet et un octet `b`, le poids parental est **b / 256**, pas b / 255.
La constante float32 `1/256` est lue à `0x1009d2bc`.

- Octet zéro : transformation par la matrice de l'os seul.
- Octet non nul : mélange `(1 − b/256) × os + (b/256) × parent`.
- Parent zéro : la seconde contribution est le sommet original, sans
  transformation. Il n'y a aucune remontée récursive de parent dans ce noyau.
- Octet 255 : l'os conserve encore une contribution de **1/256**.
- Les normales utilisent la même base 3×3, sans translation, sans inverse
  transposée et sans renormalisation dans cette routine.
- Les coordonnées UV ne sont pas écrites ; elles ne sont pas déclarées
  validées par ce calcul de positions et normales.

La référence conserve les stockages intermédiaires float32 observés.
L'identité mathématique n'implique donc pas une identité binaire de chaque
sommet après mélange : le petit arrondi mesuré n'est pas masqué.

## Exécution isolée et résultats

Même bibliothèque personnelle épinglée que le
[banc mathématique](CALCUL_ANIMATION_NATIF.md), SHA-256
`12c61eed2aec0c45700ad0a5ddfd7cbb3cbf0ea15ec67de155790bb24e7756ee`.
Seules les instructions `0x10065c60…0x10065f95` sont admises ; aucun appel
externe, chargeur, GPU, entrée DLL ou jeu. Entrées en lecture seule, écritures
limitées aux 24 octets position/normale de chaque sortie et à la pile.
Les UV/espacements et le reste de la mémoire de sortie sont contrôlés.

Domaine du banc : 0 à 2 048 sommets, 1 à 64 matrices affines fournies,
composantes finies bornées à ±10, parents et paires validés avant émulation.
Budget de `4 096 + 400 × sommets` instructions et cinq secondes par appel.
Le contrôle x87 0x027f est imposé au banc, sans prétendre établir celui de
tous les threads du jeu. Résidu maximal autorisé : 10⁻⁴.

Le rapport privé `ls3d-native-skin-20260927.json` contient **150 cas,
4 376 sommets évalués**, les 256 valeurs de poids, toutes les branches,
64 matrices et le cas limite de 2 048 sommets. **Résidu mesuré nul** face à
la référence indépendante sur ce corpus.

Le rapport `benelli-native-skin-v2-20260927.json` utilise les deux mains
épinglées, en mémoire uniquement :

| Main | Sommets | Palettes de diagnostic | Sommets évalués |
|---|---:|---:|---:|
| fpv_hands | 991 | 39 | 38 649 |
| fpv_hands_r | 1 076 | 39 | 41 964 |

Soit **80 613 déformations** supplémentaires, résidu nul par rapport à la
référence. Par main : identité, repos calculé indépendamment, translation
uniforme et changement synthétique de chacune des 36 matrices. **Ce ne sont
pas des poses Benelli animées.** Écart de position maximal à l'entrée :
3,726 × 10⁻⁹ pour l'identité et 2,385 × 10⁻⁷ pour le repos de référence.
Les rapports ne contiennent ni géométrie, ni matrices, ni clés commerciales.

Quatorze tests nouveaux vérifient les formules, les refus, les frontières
d'écriture/exécution et les rapports ; les cinq tests de repos sont conservés
avec leurs indices corrigés. Aucun ne requiert la bibliothèque commerciale.

## Reproduire et poursuivre

```powershell
.\.venv\Scripts\python.exe tools/ls3d_skin_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/peau-native-nouveau.json'
.\.venv\Scripts\python.exe tools/benelli_skin_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/mains-natives-nouveau.json'
```

Un nom de rapport neuf est obligatoire. L'installation personnelle n'est
jamais écrite. `four_ds_skin.audit_rest` reste un audit de repos : ses
indicateurs de déformation restent faux, car il n'exécute pas ces nouveaux
contrôles. Le rapport dédié qualifie uniquement le noyau CPU sur les entrées
décrites, pas la peau animée complète.

Restent notamment l'assemblage natif des matrices de la hiérarchie, les poses
initiales réellement choisies, les transitions, la liaison caméra, les sons,
les événements et les essais dans le moteur. Aucun prototype n'est activé.
