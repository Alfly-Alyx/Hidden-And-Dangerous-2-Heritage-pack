# Premier descripteur Benelli assemblé — laboratoire privé

**27 septembre 2026.** Un descripteur binaire Weapon complet de **508 octets**
est maintenant construit par l'outil original `tools/item_weapon_descriptor.py`,
puis raccordé aux ressources préparées par `tools/build_benelli_descriptor_lab.py`.
Il reste **désactivé, non installable et non jouable**. Ce n'est pas encore B2.

## Provenance et choix modernes

Cet assemblage n'est pas une fiche Benelli historique retrouvée. Il combine :

- la projection de tir de la ligne d'éditeur Benelli 9, vérifiée séparément ;
- certains **attributs individuels** de la fiche Sabre Side by Side 23 comme
  référence moderne provisoire : poids 2,48 et membres généraux/de catégorie ;
- une seconde action de même forme que ce témoin, sélecteur 5, mots 0/4/5 et
  scalaire float32 conservé. Le sens gameplay de ces valeurs reste non qualifié ;
- la munition **179**, établie par sa classe et son consommateur ;
- le modèle FPV dérivé du jeu `PROTOTYPE_BenFPV`, l'icône commerciale
  `wi_it-benelli` et le modèle extérieur original `PROTOTYPE_BenM4` ;
- le nom interne **MODERN_Benelli**, explicitement moderne.

Aucun record commercial entier n'est copié. Aucun attribut de boussole n'est
réaffecté. Les données non reliées, anciens suffixes et zones opaques sont
remplies à zéro selon une **politique moderne de sérialisation**, pas une
reconstitution historique. Les symboles de tir non résolus sont refusés.

L'identifiant de texte vaut provisoirement **0xffffffff** : marqueur de travail
non résolu, **pas** une réservation de traduction, **pas** une preuve que le menu
natif accepte cette valeur. Cette limite interdit l'installation du laboratoire.
Le choix de poids et de catégorie ne constitue pas une certification historique
ou une validation d'équilibrage du Benelli.

## Contrôles réellement obtenus

Dans l'émulateur borné, avec l'image 1.12 verrouillée par empreinte :

- le lecteur natif charge les noms, membres et deux actions de ce **nouveau**
  descripteur ; la mesure du sérialiseur concorde avec le décodeur indépendant ;
- le consommateur de munition relie 179 et initialise quantité/max à **7,0**,
  avec les témoins Sabre et PatchX01 ;
- les treize indices d'état FPV se relient au groupe **459** pour l'argument
  synthétique 359.

L'outil prépare un **fragment FPV isolé** contenant ces treize états et leurs
ressources commerciales Benelli. Le groupe 109 d'origine reste intact. Ni
`items.sav` ni `FpvAnims.sav` ne sont produits ou modifiés. L'argument 359 reste
strictement synthétique : il ne devient pas un emplacement globalement réservé.

Les vérifications natives n'appellent ni chargeur de scène, ni API Windows,
ni jeu, ni sauvegarde de partie. Elles ne démontrent ni tir effectif,
rechargement, visée, animation des mains, IA ou synchronisation réseau.

## Exemplaire privé contrôlé

`.analysis/item-descriptor-labs/BenelliDescriptor_v1`, six fichiers :

| Fichier désactivé | Taille | SHA-256 |
|---|---:|---|
| PROTOTYPE_Benelli.item.disabled | 508 | `4ce09f35ef630d59a72a4254aefd53c3d05b95afe447375f029c6f05fbc4f06e` |
| PROTOTYPE_Benelli.fpvgroup.disabled | 790 | `edd79bcc71f40926b559f75f822187c5d2f0695264646e630bf3d9ccce71cf05` |
| PROTOTYPE_BenFPV.4ds.disabled | 61351 | `0c54e499b6b6b434b3bdd02ed78cc2f7f99b304d44e162e11e787d323234300f` |
| PROTOTYPE_BenM4.4ds.disabled | 207614 | `6bc815610019739adc101d3e00319fa7819dd3d436b05e66d0521d258f291c8c` |

Les deux autres fichiers sont le manifeste de provenance/contrôles et les
avertissements. Les sorties dérivées du jeu restent privées et ignorées par Git.
Seuls le code original, les tests synthétiques et la documentation sont publiés.

## Travaux restants avant les seuls essais

1. Réserver et fournir le texte d'inventaire sans collision.
2. Qualifier les consommateurs de paramètres et leurs références sonores.
3. Raccorder la caméra, les mains et les événements FPV.
4. Compléter l'étude des sauvegardes et de liberté globale d'identifiant.
5. Construire la transaction additive réversible des tables dans une copie isolée.

Les essais de comportement en moteur et multijoueur viennent ensuite. Ce lot
ne permet donc pas d'annoncer « il ne reste que les tests ».

```powershell
.\.venv\Scripts\python.exe tools/build_benelli_descriptor_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name BenelliDescriptor_nouveau
```

Sans `--output-name`, tout est construit/contrôlé en mémoire. Un nom existant,
un chemin lié, une source modifiée ou une référence invalide fait refuser l'outil.
Seize tests synthétiques couvrent l'assembleur et ce laboratoire.
