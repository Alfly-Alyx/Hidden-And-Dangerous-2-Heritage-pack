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

Dans les versions v1/v2, l'identifiant de texte vaut **0xffffffff**, marqueur
non résolu et non installable. La version **v3**, construite avec
`--inventory-texts`, le remplace par **21500** et joint les
[huit libellés modernes additifs](../RECONSTRUCTION_BACKLOG/TEXTES_INVENTAIRE_MODERNES.md).
Cette réservation reste limitée au laboratoire ; le rendu natif n'est pas validé.
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
`items.sav` ni `FpvAnims.sav` ne sont produits par ce constructeur de descripteur.
Le [constructeur de tables distinct](TRANSACTION_TABLES.md) les prépare désormais
en copies complètes désactivées, avec retrait exact vérifié. Le candidat 359 ne
devient pas pour autant un emplacement globalement réservé ou installé.

Les vérifications natives n'appellent ni chargeur de scène, ni API Windows,
ni jeu, ni sauvegarde de partie. Elles ne démontrent ni tir effectif,
rechargement, visée, animation des mains, IA ou synchronisation réseau.

## Exemplaire privé contrôlé

`.analysis/item-descriptor-labs/BenelliDescriptor_v3`, quatorze fichiers. Les
versions v1/v2 sont conservées. Le manifeste v2 avait ajouté les
[références sonores qualifiées](../RECONSTRUCTION_BACKLOG/REFERENCES_SONORES.md)
36/54. La version v3 ajoute les textes 21500, sans modifier les autres membres,
les modèles ou le fragment FPV :

| Fichier désactivé | Taille | SHA-256 |
|---|---:|---|
| PROTOTYPE_Benelli.item.disabled | 508 | `6b03354261405a6e30c2225c65c23a7eed7349653828a4444ba3c10da90a251c` |
| PROTOTYPE_Benelli.fpvgroup.disabled | 790 | `edd79bcc71f40926b559f75f822187c5d2f0695264646e630bf3d9ccce71cf05` |
| PROTOTYPE_BenFPV.4ds.disabled | 61351 | `0c54e499b6b6b434b3bdd02ed78cc2f7f99b304d44e162e11e787d323234300f` |
| PROTOTYPE_BenM4.4ds.disabled | 207614 | `6bc815610019739adc101d3e00319fa7819dd3d436b05e66d0521d258f291c8c` |

Les dix autres fichiers sont les huit tables de texte désactivées, le manifeste
de provenance/contrôles et les avertissements. Les sorties dérivées du jeu restent privées et ignorées par Git.
Seuls le code original, les tests synthétiques et la documentation sont publiés.

## Travaux restants avant les seuls essais

1. Valider le rendu du texte d'inventaire maintenant préparé, lors des essais natifs.
2. Qualifier les autres consommateurs de paramètres et la synchronisation sonore ;
   les références Benelli aux banques 2/3 sont maintenant établies séparément.
3. Qualifier la liaison native, le skin, la caméra et les événements FPV ;
   le [plan structurel mains/arme](MAINS_ET_CIBLES_FPV.md) relie maintenant
   les deux mains commerciales aux neuf animations, sans inventer de poses.
4. Compléter l'étude des sauvegardes et de liberté globale d'identifiant.
5. Préparer le déploiement isolé et la gestion des surcharges ; la construction
   binaire réversible des deux tables est maintenant réalisée séparément.

Les essais de comportement en moteur et multijoueur viennent ensuite. Ce lot
ne permet donc pas d'annoncer « il ne reste que les tests ».

```powershell
.\.venv\Scripts\python.exe tools/build_benelli_descriptor_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --inventory-texts --output-name BenelliDescriptor_nouveau
```

Sans `--output-name`, tout est construit/contrôlé en mémoire. Un nom existant,
un chemin lié, une source modifiée ou une référence invalide fait refuser l'outil.
Vingt tests synthétiques couvrent l'assembleur et ce laboratoire, en plus des
douze tests du préparateur multilingue.
