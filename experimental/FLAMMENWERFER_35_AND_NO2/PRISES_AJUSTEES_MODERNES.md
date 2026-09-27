# Prises ajustées : paramètres modernes, animations dérivées privées

**27 septembre 2026.** Suite du [contrôle de contact](CONTACT_MAINS_ET_TRANSITIONS.md).
Les banques antérieures restent intactes. Les deux géométries d'équipement et
les deux modèles commerciaux de mains ne sont pas modifiés.

## Ce qui est maintenant implémenté

`fit_modern_grip_candidates.py` ajuste neuf paramètres artistiques par main :
deux déplacements de prise, une inclinaison, trois flexions de doigts et trois
paramètres de pouce. Les os gardent leurs positions, échelles et longueurs de
repos. Le solveur refuse une source inconnue, une base impropre ou une cible
inaccessible. Il ne récupère aucune animation commerciale pour inventer la prise.

La recherche commence par des sommets et des sondes de faces, puis ajoute des
témoins issus de l'intersection exacte des triangles avec les volumes convexes
des pièces tenues. Ces témoins et les géométries commerciales restent en mémoire.
Le résultat de recherche conserve seulement paramètres modernes et mesures ;
la minimisation n'est jamais une promotion automatique.

`modern-fitted-hand-grips.json` est un profil portable : uniquement ces choix
modernes et les empreintes de référence, aucune pose d'os commerciale. L'empreinte
de la recette de base emploie le JSON canonique et ne dépend donc pas des fins
de ligne Windows. Le profil est revérifié et les transformations recalculées
avant chaque génération ; une transformation fournie sans preuve est refusée.

`build_fitted_fpv_bank.py` produit **36 clips** : neuf séquences, deux variantes
de mains, deux ensembles. Les clés de bras, doigts et pouces sont recalculées ;
les canaux d'équipement sérialisés sont conservés à l'identique. Les sources,
la géométrie et les banques `CorrectedFPV_v1` restent intactes. Les préfixes
`PROTOTYPE_F35GH`, `F35GR`, `F2GH` et `F2GR` distinguent les nouvelles animations
des alias précédents, sous la limite native de dix-neuf caractères.

Chaque dossier privé `F35_FittedGrips_v6` / `F2_FittedGrips_v6` contient cinquante
fichiers avec les aperçus : un modèle moderne inchangé, dix-huit clips dérivés
désactivés, trente PNG et un manifeste. Les vues de détail repos des deux
ensembles ont été inspectées pendant l'ajustement, puis leurs vues de visée
avec la variante R en v6 ; elles ne constituent pas
une qualification esthétique exhaustive des mains.

## Mesure de surface, pas seulement des sommets

`convex_contact.surface_measure` découpe les triangles contre les plans d'un
volume convexe fermé. Il détecte aussi un triangle traversant une pièce lorsque
**ses trois sommets sont extérieurs**. Le rejet rapide par boîte englobante
utilise les limites exactes de la même pièce sérialisée.

La tolérance de pénétration est `1e-5` unité, soit 0,01 mm à l'échelle d'auteur.
Le seuil d'aire est `1e-14` ; la recherche de profondeur s'arrête à une largeur
d'intervalle de `1e-7`. La profondeur annoncée est une borne inférieure : ce
dernier nombre n'est pas une garantie absolue pour une surface arbitrairement
fine. Les contrôles synthétiques couvrent intérieur, extérieur, tangence,
triangles traversants et conservation du résultat après rejet par boîte.

L'ajustement fondé uniquement sur les sommets laissait encore des triangles
traverser d'autres pièces. Le contrôle dense v4 trouvait 98 poses concernées
sur 2 244 ; v5 en conservait six, maximum 0,03813 mm. Les témoins ont localisé
les derniers écarts sur les appuis gauches pendant `Shot` F35 et `Idle1` No. 2.
Le profil v6 ajoute des marges ciblées, sans augmenter la tolérance de mesure.

L'audit dense comprend toutes les clés et demi-clés des neuf clips et des
quatre banques, plus quatre poses de référence anciennes : **2 248 échantillons**.
Il reste un échantillonnage temporel, pas une preuve sur tout instant continu
ou sur tout mélange de pistes.

Résultat v6 terminé : **zéro triangle pénétrant au seuil indiqué** pour les
2 244 poses ajustées, soit 32 538 comparaisons mains/pièce convexe. Le rapport
privé est `.analysis/fitted-grip-surfaces-v6-dense-20260927.json`. Les quatre
références anciennes ne sont pas incluses dans ce zéro ; les exclusions de
pièces non convexes demeurent listées pour chaque pose.

## Associations de ressources et contrôles natifs

Le laboratoire `build_equipment_fpv_resource_lab.py --view-axes --fitted-profile`
utilise le nouveau profil et les alias `G`. Treize états sont associés à neuf
ressources distinctes par variante. Les identifiants 360/361 et groupes 460/461
restent des **candidats de laboratoire**, pas des réservations globales.
Les variantes H/R sont mutuellement exclusives, selon les mains du personnage.

Les routines natives isolées vérifient la lecture des 5DS, l'attachement, les
temps, les poses et les palettes. Les racines de mains identités restent des
nœuds diagnostiques ; les sous-systèmes emploient des émulateurs séparés.
Le contrôle des surfaces, lui, utilise la référence numérique du skin.
Ni chargeur/copie du modèle en scène, ni rendu, événements ou jeu ne sont exécutés.

Rapport `.analysis/fitted-grips-native-v6-20260927.json` terminé :

| Contrôle | Mesure |
| --- | --- |
| Lectures natives / séquences | 36 / 36 |
| Instants / observations de poignets / palettes de mains | 2 316 / 4 632 / 2 316 |
| Écart de poses natives/référence | 0 |
| Écart maximal de palette | `2,682209015e-7` |
| Poignets aux clés / entre les clés | `1,689756173e-7` / `0,000161905568` |

Les seuils restent `5e-6` aux clés et `0,0002` entre les clés. Le résidu
intermédiaire n'est pas présenté comme nul et explique les marges d'auteur.
Les quatre laboratoires `F35H`, `F35R`, `F2H`, `F2R` suffixés
`_FittedFPVResources_v6` ont aussi terminé **156 demandes natives et 36 lectures
de 5DS**. Leurs clips ont exactement les mêmes empreintes que les banques v6
contrôlées. Ni table centrale ni modèle commercial de mains n'est émis.

## Limites qui restent du travail d'implémentation

- Le [correcteur après mélange](CONTACT_MAINS_ET_TRANSITIONS.md) est toujours
  un outil d'auteur, non raccordé au moteur ; les clips recalculés ne le remplacent pas.
- Les pièces non convexes sont **explicitement exclues** : bandes, sangles,
  poignée de sac et tuyau F35 ; anneau de sac, sangles, poignée et tuyau No. 2.
  L'absence d'intersection avec les seules pièces contrôlées ne couvre pas tout l'équipement.
- Ni les auto-intersections de mains, ni le contact naturel de chaque doigt,
  ni le cadrage FPV, ni l'attache dorsale ne sont qualifiés.
- Sons, événements, effet, comportement d'arme, entrée additive et sauvegarde
  restent distincts de la réalisation de ces animations.

Les données commerciales et les sorties dérivées restent privées et ignorées
par Git. Seuls outils, paramètres originaux, tests synthétiques et documentation
sont publiés. Aucun installateur ni jeu n'est lancé.

```powershell
.\.venv\Scripts\python.exe tools/build_fitted_fpv_bank.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --case F35 --bank .analysis/modern-assets/F35_CorrectedFPV_v1 --fitting experimental/FLAMMENWERFER_35_AND_NO2/modern-fitted-hand-grips.json --output-name F35_FittedGrips_v7 --previews
.\.venv\Scripts\python.exe tools/build_fitted_fpv_bank.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --case F2 --bank .analysis/modern-assets/F2_CorrectedFPV_v1 --fitting experimental/FLAMMENWERFER_35_AND_NO2/modern-fitted-hand-grips.json --output-name F2_FittedGrips_v7 --previews
.\.venv\Scripts\python.exe tools/fitted_grip_surface_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank-root .analysis/modern-assets --bank-suffix FittedGrips_v7 --dense --json-output .analysis/contact-surfaces-nouveau.json
.\.venv\Scripts\python.exe tools/fitted_grip_native_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank-root .analysis/modern-assets --bank-suffix FittedGrips_v7 --fitting experimental/FLAMMENWERFER_35_AND_NO2/modern-fitted-hand-grips.json --json-output .analysis/contact-natif-nouveau.json
```

Les banques corrigées de base doivent déjà exister ; les noms de sortie doivent
être neufs. L'audit natif exige les dépendances privées d'émulation.
