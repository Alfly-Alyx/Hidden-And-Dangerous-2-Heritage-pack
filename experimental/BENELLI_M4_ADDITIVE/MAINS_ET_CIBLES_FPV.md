# Mains commerciales et cibles des animations Benelli

**27 septembre 2026.** Un plan de liaison structurelle relie les deux modèles
de mains commerciaux aux huit nœuds du modèle FPV statique dérivé. Il couvre
les neuf animations Benelli sans modifier leurs clés ni fusionner les modèles.
**Ce plan ne démontre pas encore la déformation du skin ou le rendu en jeu.**

## Ressources retrouvées et verrouillées

| Ressource | Archive | Octets | SHA-256 |
|---|---|---:|---|
| models/fpv_hands.4ds | models.dta | 49154 | `5a418cba65daca969417b0d38e0c467bd8b58f49f12260961dc3ee163afe8678` |
| models/fpv_hands_r.4ds | models.dta | 52813 | `7a81c876cbce814c0a8e3dc7abe3c1fe2887c2e2f3cc3dd520d83c28e1f93555` |
| maps/la_ruka01.bmp | Maps.dta | 66616 | `8275739e06d957e181f9f6f05f12b3a479e3f5515d6feaa8880a7e01cb04e646` |
| maps/la_ruka02.bmp | Maps.dta | 17464 | `87b0ee2bd6dc9bd02bf39a1aa2eff39fad5f80ad05dcbaa95dd5092a9369e7b9` |
| maps_u/e_br_bdarm.bmp | Maps_U.dta | 9272 | `12ce6359c6b07f2c8e12d6ca6e341c8f26f184c11275e7ff8128382617e7c869` |

La texture de manches n'est pas absente : elle se trouve dans **maps_u**, pas
dans maps. Les variantes compressées DX1 présentes dans cette archive ne sont
pas substituées au BMP dans cette preuve. L'ordre effectif de recherche des
textures et le choix de compression restent à qualifier dans le moteur.

Les sources sont lues avec leurs empreintes ; surcharge d'archive, doublon,
ressource modifiée ou texture non résolue font refuser le constructeur. Les
surcharges libres sont refusées par défaut, ou recensées/exclues explicitement
avec `--archives-only`. Les ressources commerciales ne sont pas publiées.

## Correspondance réelle des squelettes

Chaque modèle de mains contient **37 cibles** : un maillage skinné racine `a`
et 36 articulations. Les modèles d'animation Benelli contiennent la même
hiérarchie nommée, avec `a` représenté comme un joint, plus les huit cibles de
l'arme : `fpv_weapon`, `gunlock`, `cock`, `blsdum`, `cardum`, `shdum`, `shell01`
et `magazine`.

Le plan `tools/fpv_rig_binding.py` compare les **noms exacts et les noms des
parents**, pas les indices de fichier : l'ordre des accessoires change entre
certains modèles. Il refuse les noms communs aux mains et à l'arme, les
doublons, les cycles, les parents manquants, les pistes inconnues et les types
de nœuds inattendus. La différence explicite de rôle de `a` est conservée,
pas généralisée à tous les joints.

| Animation | Dernière frame déclarée | Pistes mains | Pistes arme | Total |
|---|---:|---:|---:|---:|
| Aim | 10 | 37 | 8 | 45 |
| AimShot | 15 | 1 | 4 | 5 |
| Arm | 60 | 20 | 1 | 21 |
| Daim | 10 | 37 | 8 | 45 |
| Disarm | 20 | 6 | 1 | 7 |
| Idle1 | 60 | 37 | 8 | 45 |
| Jammed | 20 | 2 | 1 | 3 |
| Rel | 146 | 37 | 8 | 45 |
| Shot | 20 | 6 | 2 | 8 |

Les deux variantes donnent les mêmes correspondances : **224 pistes par
variante, soit 448 correspondances sur 18 paires contrôlées**. Une animation
partielle reste partielle. Aucune pose neutre, interpolation ou remise à zéro
n'est ajoutée aux cibles sans piste ; leur héritage et leur mélange natifs
restent à établir. Une frame terminale n'est pas une durée ni une fréquence.

## Références d'objets et observations du client

Les tables commerciales contiennent 64 références à ces mains dans Base/Patch
et 75 dans Sabre/PatchX01. **Le slot 270 est de classe native 1**, malgré son
nom d'habillement et sa référence `FPV_hands_r`. Cette anomalie est conservée
et signalée ; aucune fiche n'est corrigée ou reclassée.

L'inspection statique du client montre le chargement/nommage `FPV_HANDS` dans
`0x490930`, puis l'association distincte de modèles dans `0x491130`. Le lecteur
de modèle FPV d'objet `0x7df970` recherche notamment les noms **fpv_weapon** et
**magazine**, tous deux conservés dans le modèle dérivé. Ces observations
n'équivalent pas à l'exécution des appels de scène ou à leur validation.

Le [contrôle des demandes de ressources](DEMANDES_RESSOURCES_FPV.md) exécute
désormais la transformation du nom de mains et la préparation des demandes
d'animation, en s'arrêtant avant les chargeurs. Il ne valide toujours pas la
liaison des joints, le skin ou le rendu.

## Livrables et limites

Le [contrôle indépendant des rotations et matrices de repos](../RECONSTRUCTION_BACKLOG/ROTATIONS_NATIVES.md)
est maintenant intégré : **72 os** et **224 rotations initiales** vérifiés.
Il corrige notre calcul hors moteur ; la sémantique des octets de poids et la
déformation native ne sont pas encore établies.

Le [calcul d'animation natif isolé](../RECONSTRUCTION_BACKLOG/CALCUL_ANIMATION_NATIF.md)
recoupe ensuite 20 220 échantillons de rotation sur les 224 canaux Benelli.
Il s'arrête avant les mélanges et ne complète aucune piste absente : cette
preuve ne remplace pas l'héritage des poses partielles ou le skin.

- `tools/benelli_fpv_rig_audit.py` produit le plan privé, les sources et les
  exceptions, sans géométrie ni clés d'animation dans le rapport.
- `.analysis/benelli-fpv-rig-20260927.json` conserve les correspondances exactes.
- Le constructeur de tables ajoute ce plan à ses manifestes privés v3, sans
  remplacer les modèles de mains installés ou copier leurs données dans Git.
- Treize tests synthétiques couvrent le plan, les lectures verrouillées et
  son intégration ; aucune installation n'est autorisée par ce contrôle.

Restent à qualifier : liaison native effective par nom, déformation du skin,
application native des poses de repos et héritage des pistes partielles, caméra, événements et
synchronisation. Les sauvegardes et le déploiement isolé restent des contrats
séparés. Les animations et les mains Benelli n'ont pas à être inventées pour
combler un manque supposé : les ressources vérifiées existent déjà.

```powershell
.\.venv\Scripts\python.exe tools/benelli_fpv_rig_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/benelli-fpv-rig-nouveau.json'
```
