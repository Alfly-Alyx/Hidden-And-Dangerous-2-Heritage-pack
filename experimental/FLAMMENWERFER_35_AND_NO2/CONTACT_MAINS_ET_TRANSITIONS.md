# Contact des mains et correction après mélange

**27 septembre 2026.** Implémentation d'auteur hors jeu. Aucun raccordement
du correcteur au client, aucune nouvelle banque activée, aucun lancement.

## Défaut localisé

Le banc des [repères FPV](REPERES_VUE_SUBJECTIVE.md) mesurait un écart maximal
de `0,04057576875000862` unité de modèle pendant les mélanges. Le nouveau
traçage conserve maintenant le cas, la variante, l'étape, le côté, les pistes,
leurs poids et **le temps réellement échantillonné avant bouclage**.

Le maximum est reproduit : No. 2, main droite, variante `fpv_hands`, ordre
direct, étape 45 (index zéro). `Daim` occupe la piste 0, poids 0,5, temps
échantillonné 160 ; `Arm` occupe la piste 1, poids 0,5, temps 60. Le pas vaut 20.
Ces temps ne sont pas présentés comme des secondes. Les deux variantes de
mains montrent le même défaut. L'accessibilité de cet ordre dans le client
n'est toujours pas établie : il s'agit d'un scénario de contrainte explicite.

## Correction réalisée et frontière d'intégration

`fpv_contact_constraints.py` recalcule les cibles depuis les poses d'équipement
**déjà mélangées**, puis résout les bras sans étirement. Seules six rotations
locales changent : bras, avant-bras et main de chaque côté. Les positions,
échelles, racine des mains, doigts, pouces, équipement, géométrie, parentés et
transformations de repos restent inchangés. Une source non épinglée, une cible
incomplète, un bras inaccessible ou un déplacement d'os provoque un refus.

Le calcul est du Python d'auteur. Il n'est ni injecté ni appelé par le moteur.
Il fournit une solution mesurée du défaut ; il ne suffit pas à annoncer que
les transitions en jeu sont réparées. Le point d'application après mélange,
les invalidations de matrices, le coût et la conservation du cycle natif
restent du travail d'intégration, pas seulement des tests à cocher.

Le rapport privé `.analysis/fpv-contact-correction-native-20260927.json`
contrôle les quatre banques, en ordres direct et inverse : **8 séquences,
352 instants, 704 observations de poignets et 704 palettes natives**.
Les poses proviennent du véritable attachement/poids/temps/pose LS3DF dans
une mémoire persistante isolée. Les palettes de mains avant/après sont
calculées dans un deuxième émulateur borné. La racine de mains, identité,
est incluse comme nœud diagnostic ; ce n'est pas un modèle chargé en scène.

- Écart avant correction : `0,04057576875000862`.
- Écart après correction : au plus `1,695250813e-7`.
- Différence poses natives/référence : zéro.
- Différence palettes natives/référence : au plus `2,384185791e-7`.

Le seuil de contrôle des poignets reste `5e-6` ; il n'a pas été relâché.
Le skin, le rendu, les événements et le choix réel des transitions ne sont
pas exécutés par ce nouveau banc. Aucune pose dérivée n'est écrite dans son
rapport, seulement empreintes, paramètres de scénario et mesures.

## Pouces : première proposition non retenue comme solution

`modern_thumb_pose.py` permet une opposition et deux flexions modernes pour
chaque pouce. Les quatre rotations seulement sont modifiées ; les bases de
repos commerciales restent privées et inchangées. La conjugaison utilise
leur véritable inverse, car leurs petites erreurs d'arrondi ne doivent pas
introduire deux fois un résidu d'échelle.

La proposition initiale de ±30° d'opposition et ±25°/±20° de flexion est
**un candidat de comparaison, pas une prise validée**. Les répertoires privés
`F35_ThumbGrips_v3` et `F2_ThumbGrips_v3` contiennent chacun 26 PNG et un
manifeste : avant/après, repos/visée, deux variantes de mains, perspectives et
détails orthographiques. Le champ horizontal 65°/40° est un choix de diagnostic
informé par les constantes du client, sans instance de caméra qualifiée.
Aucun nouveau clip de jeu n'est émis ; les banques v1 restent reproductibles.

Les mesures contredisent une validation sur la seule apparence : sur F35,
la pénétration maximale des sommets de pouce gauche dans l'appui passe
d'environ **20,081 mm à 23,310 mm** à l'échelle d'auteur. Sur No. 2,
le pouce droit passe d'environ **17,139 mm à 17,940 mm**. Les doigts ont déjà
des intersections indépendantes des pouces, atteignant environ 19,721 mm
dans l'appui gauche F35. Le premier candidat n'est donc pas promu.

## Mesure de surface, limites explicites

`convex_contact.py` construit les plans de soutien depuis les triangles
**sérialisés et transformés** des poignées modernes. Il vérifie leur fermeture
par les arêtes géométriques, leur convexité, l'absence de faces dégénérées et
la finitude des coordonnées. Il mesure la profondeur d'un sommet intérieur
comme sa distance minimale aux plans ; il ne confond pas cette mesure avec
une distance exacte d'un point extérieur au maillage.

`equipment_hand_contact.py` utilise la référence numérique du skin, sans
exécuter ce noyau natif à nouveau. Les sommets sont classés selon l'influence
dominante réelle : poids secondaire `octet/256`, pouce, autres doigts ou
paume/bras. Le rapport privé `.analysis/hand-grip-penetration-20260927.json`
compare **8 échantillons avant/après**, avec empreintes des sources.

Ce contrôle de sommets ne détecte pas tous les croisements de triangles,
ne vérifie pas les autres pièces de l'arme ni les auto-intersections des mains,
et ne prouve pas qu'une main sans pénétration serre effectivement la poignée.
L'ajustement des paumes, l'orientation par rapport aux poignées inclinées,
la flexion des doigts et l'opposition des pouces restent en cours.

La [suite avec prises ajustées](PRISES_AJUSTEES_MODERNES.md) ajoute maintenant
un profil moderne portable, la recherche guidée par surfaces, trente-six clips
dérivés et des associations natives distinctes. Elle conserve les diagnostics
ci-dessus comme comparaison et ne raccorde pas encore le correcteur au moteur.

```powershell
.\.venv\Scripts\python.exe tools/fpv_transition_contact_audit.py --game 'D:\Games\Hidden and Dangerous 2' --bank-root .analysis/modern-assets --archives-only --native --json-output .analysis/contact-transitions-nouveau.json
.\.venv\Scripts\python.exe tools/equipment_hand_contact.py --game 'D:\Games\Hidden and Dangerous 2' --bank-root .analysis/modern-assets --archives-only --json-output .analysis/contact-doigts-nouveau.json
```

Le mode natif exige les dépendances privées d'émulation. Les noms de rapports
doivent être neufs. Aucun binaire commercial, maillage de main ou pose dérivée
n'est publié ; aucun jeu ou installateur n'est lancé ou modifié.
