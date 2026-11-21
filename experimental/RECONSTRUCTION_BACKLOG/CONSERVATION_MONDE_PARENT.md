# Changement de parent avec conservation de la transformation mondiale

Raccordement privé du **10 octobre 2026**, désactivé. La
[protection du changement de parent](CHANGEMENT_PARENT_NATIF.md) est conservée
sans modifier son binaire ; le banc exécute maintenant les chemins natifs avec
les indicateurs **1 et 3**, qui préservent la transformation mondiale.

## Chemin exécuté

Le moteur construit les caches mondiaux nécessaires, inverse la transformation
du nouveau parent, calcule la transformation locale de remplacement, en extrait
l'échelle et reconstruit l'orientation. Aucun de ces calculs n'est remplacé par
un résultat Python. La référence indépendante sert uniquement à comparer les
sorties, jamais à réinjecter une pose après l'appel.

Trente-deux scénarios utilisent un arbre frais chacun : transfert d'une feuille,
détachement, déplacement du modèle et demande sans changement ; deux orientations,
avec / sans interception, indicateurs 1 / 3. Les onze nœuds surveillés et les
deux modèles sont des objets diagnostiques possédés. Les échelles sont positives
et uniformes ; les transformations cisaillées ou réfléchies sont hors périmètre.

- **24 changements effectifs, huit demandes sans effet, seize notifications
  compilées** retirant le registre avant le prologue natif.
- **104 constructions de cache mondial**, 104 constructions de rotation,
  80 produits matriciels, seize inversions, 24 extractions d'échelle et 24
  reconstructions d'orientation exécutés par le code d'origine.
- Écart maximal des transformations mondiales recomposées après changement :
  **`1,789e-7`**, pour une tolérance de `5e-5`. Les caches natifs antérieurs et
  les transformations locales sont contrôlés séparément.
- Liens et indicateurs contrôlés ; vecteurs d'appartenance, références, noms,
  champs sans rapport et gardes mémoire conservés. Image native restaurée.
- Neuf tests publics couvrent les calculs inventés, les périmètres exclus et
  les rapports incomplets ou excessivement affirmatifs.

## Deux détails importants pour le réarmement

Après le chemin matriciel, le moteur laisse le quaternion `+c0` inchangé et
désactive son indicateur de validité. La matrice d'orientation, elle, est mise à
jour. **Relire directement cet ancien quaternion comme une pose courante serait
incorrect.** Le banc vérifie cette distinction ; sa régénération native et le
réarmement après régénération ne sont pas encore qualifiés ici.

L'extraction d'échelle produit trois composantes. Le code appelant copie aussi
un quatrième emplacement temporaire vers `+dc`. Ce mot est un remplissage non
sémantique, pas une quatrième échelle ni une valeur supposée nulle. Le banc
contrôle sa copie exacte depuis la pile, sans l'utiliser dans les calculs.

## Limites et reproduction

La recomposition mondiale **après** changement est une référence indépendante,
pas un rendu ni un second rafraîchissement natif. Aucun rafraîchissement immédiat,
notification de scène, cas de type scène cinq, allocateur ou destructeur n'est
exécuté. Le client complet, les refus de production et la durée de vie réelle
restent à traiter. Aucune correction de pose n'est exécutée dans ce banc.

`tools/audit_native_parent_world.py --output-name NativeParentWorld_v1`, destination
neuve, avec `--library`, `--compiled-collection`, `--compiled-hook`,
`--compiled-lifecycle` et `--compiled-parent` vérifiés. Rapport privé sous
`.analysis/modern-assets/NativeParentWorld_v1/`. Aucun jeu lancé ou modifié.
