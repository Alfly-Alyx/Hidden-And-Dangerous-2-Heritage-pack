# Conserver les tables personnalisées dans l'ajout désactivé

**27 septembre 2026.** L'ajout Benelli peut désormais être composé sur un
instantané des tables centrales libres de l'installation. Il reste privé,
désactivé et non installable : cette étape n'est pas un déploiement en jeu.

## Personnalisations réellement présentes

La lecture locale trouve deux tables différentes des archives :

- `Tables/items.sav` : 252 000 octets,
  `c98f6670be9a16c5ddfb406014c76fb5f9da74b6564b7d9d8662971105f4d9c6`.
  Par rapport à PatchX01, **dix fiches modifiées** : slots
  0, 1, 2, 3, 5, 15, 17, 26, 28 et 260.
- `Tables/FpvAnims.sav` : 127 725 octets,
  `c7c6b35a600815a3a6e1f32ff9475c9006eec0c48309051f994be87923b5d28e`.
  Par rapport à Sabre, **six groupes modifiés** :
  100, 101, 102, 103, 105 et 360 ; aucun groupe supprimé ou déplacé.

Le slot candidat 359 et le groupe 459 sont absents ; la munition 179 reste
identique à l'archive. Ces constats portent sur cet instantané, pas sur tout
mod possible ni sur la liberté globale de l'identifiant.

## Composition sans écrasement des différences

`tools/item_table_overlay.py` travaille entièrement en mémoire. Pour chacune
des deux tables, il prend la surcharge présente, sinon la source d'archive
explicitement choisie. Il consigne les fiches ajoutées, retirées ou modifiées,
ainsi que les changements d'ordre des groupes FPV.

L'insertion est ensuite calculée **sur ces contenus courants**. Toutes les
autres fiches, tous les groupes et leur ordre restent inchangés. Un retrait
exact restitue les tables personnalisées, et non les versions commerciales.

Sont refusés : slot ou groupe déjà occupé, nom interne ou texte en collision,
munition référencée modifiée/supprimée/reclassée, format natif non qualifié,
capacité différente, source liée ou ambiguë, et changement du contenu entre
sa capture et la fin de préparation. Un retrait refuse aussi toute modification
survenue après l'ajout. Aucune différence n'est corrigée automatiquement.

## Laboratoire personnel obtenu

`.analysis/item-table-labs/BenelliTables_Personal_v1` contient quatorze
charges désactivées, un manifeste et ses avertissements. Les deux nouvelles
tables sont :

| Contenu désactivé | Octets | SHA-256 |
|---|---:|---|
| Tables/items.sav.disabled | 252000 | `805ba689d9e0657e609f0ee97a71eb9ff0fad9ae3a752992e6a605c7914651be` |
| Tables/FpvAnims.sav.disabled | 128509 | `4b463990cfc2d2dd773cde73d2d7b391e4db900fdf28603e5680e5e9e984e61a` |

Les routines natives isolées vérifient 500 slots, 273 objets, 278 groupes,
**632 références d'animation**, et 39 demandes d'animation Benelli. Les dix
fiches et six groupes personnels sont conservés octet pour octet. Le retrait
des deux tables est vérifié intégralement en mémoire.

Douze tests synthétiques supplémentaires couvrent la composition, les
conflits, la lecture des instantanés et le raccordement au constructeur.

```powershell
.\.venv\Scripts\python.exe tools/build_benelli_table_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --preserve-central-overrides --item-layer PatchX01.dta --output-name BenelliTables_Personal_nouveau
```

L'option est explicite ; les laboratoires purement commerciaux restent
disponibles. Sans nom de sortie, seule une construction en mémoire a lieu.
Les textes conservent déjà leur propre instantané multilingue. Les surcharges
de **modèles, textures, sons et autres ressources** restent un autre contrat :
elles ne sont ni fusionnées ni considérées compatibles par cette option.
La transaction de fichiers dans une copie isolée reste à réaliser séparément.
