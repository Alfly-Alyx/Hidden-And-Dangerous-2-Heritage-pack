# Registre maître des reconstructions expérimentales

Inventaire initial : **2026-09-19**. Dernière mise à jour : **2026-09-27**.

Branche de travail actuelle : `codex/reconstruction-phase-1`.
La préparation de `codex/experimental-reconstruction-inventory` a été intégrée
à `master` avant la création de cette branche; sa photo historique est conservée.

Ce dossier réunit l'état des connaissances disponible pour la restauration et la
reconstruction additive de contenu de *Hidden & Dangerous 2*. La branche part de
`master` et contient donc tous les fichiers déjà versionnés du projet. Le présent
registre complète ces fichiers sans activer de script expérimental dans
l'installation personnelle. Les déploiements privés de test sont isolés et journalisés.

## Principes

- La version commerciale reste le comportement par défaut.
- Une ligne commentée, un script libre ou un nom de checkpoint est une preuve de
  vestige, pas une preuve suffisante du comportement final.
- Les éléments officiels, les inférences et les créations modernes sont toujours
  distingués.
- Aucun binaire commercial extrait n'est ajouté au dépôt.
- Les prototypes restent en `.disabled` tant que leurs propriétaires, liaisons,
  positions et conditions de fin ne sont pas démontrés puis testés en jeu.
  Seuls les essais explicitement préparés dans une copie isolée peuvent utiliser
  des fichiers actifs, avec empreintes et restauration; aucune promotion n'en découle.
- Une reconstruction ne doit jamais doubler un signal, un objectif, une voix, un
  effet ou un acteur déjà pris en charge par la version commerciale.

## Légende d'état

### Avancement vérifié le 27 septembre 2026

- **47 profils / 55 scripts dérivés** reconstruits depuis les archives, avec
  157 sources de mission, trois preuves de campagne Africa 3, deux ressources de dialogue et trois modèles
  d'accessoires supplémentaires;
  les archives de prototypes restent désactivées et aucune
  variante n'est validée en jeu.
- **20 laboratoires A/B / 40 entrées** contrôlés hors moteur, objectifs
  commerciaux conservés. Sept profils Africa 5 restent sans laboratoire renommé :
  leur détecteur de piste commercial absent empêche la copie complète.
- **1 113 tests Python réussis sur 1 114 dans la copie de publication**; un test de lien symbolique non exécuté
  faute de privilège Windows. Compilation console et auto-tests de sécurité C#
  précédemment réussis, sans nouvelle modification C# dans ce lot.
- Lecteur audio DPCM complété : vingt WAV de missions décodés et mesurés en mémoire,
  sans export ; deux sons Benelli supplémentaires sont mesurés et incorporés
  uniquement au banc privé, sans modification du jeu. [Méthode](AUDIO_RESSOURCES.md).
- [Banc Benelli FPV](../BENELLI_M4_ADDITIVE/BANC_FPV.md) : 28 sources verrouillées,
  neuf animations décodées, modèle FPV statique dérivé, inspecteur de poses/clés/sons.
  Trois tests JavaScript synthétiques réussis ; affichage navigateur et moteur
  non validés. Le modèle extérieur moderne demeure distinct.
- [Tables Benelli](../BENELLI_M4_ADDITIVE/TABLES_ADDITIVES.md) : lecteurs centraux
  et associations FPV structurées réalisés, 359 vide dans Sabre/PatchX01 mais
  hors capacité Base/Patch. Les modèles ont maintenant des alias courts natifs.
  Le [contrat natif 1.12](../BENELLI_M4_ADDITIVE/CONTRAT_NATIF.md) compare 1 036
  descripteurs au lecteur d'origine en émulation isolée et établit la liaison
  objet → groupe FPV. Quatorze tests supplémentaires couvrent ces calculs et
  leurs refus. Ni sauvegarde de partie ni animation en jeu qualifiée : aucune
  entrée n'est allouée.
- [État d'objet et munition](../BENELLI_M4_ADDITIVE/ETAT_ET_MUNITION.md) :
  208 associations commerciales contrôlées, codec d'enveloppe isolée réalisé,
  identifiants supérieurs à 255 conservés. Quatorze tests supplémentaires ;
  deux tags communs écrits mais ignorés par le lecteur natif sont explicités.
  Pas de migration ni de compatibilité de sauvegarde complète annoncée.
- [Tables d'éditeur](TABLES_EDITEUR.md) : 755 lignes et leurs colonnes décodées.
  Onze tests synthétiques supplémentaires empêchent les anciennes fenêtres de
  recherche d'empiéter sur une fiche voisine. Preuves Benelli, FG42, MG34 et
  lance-flammes recalées ; banc privé BenelliFPV_v5 reconstruit sans changer
  les géométries. Aucune arme activée.
- Deux modèles extérieurs originaux supplémentaires :
  [FG42](../FG42/MODELE_MODERNE.md), 876/564 triangles, et
  [MG34 portative](../MG34_PORTABLE/MODELE_MODERNE.md), 1536/960 triangles.
  Géométrie, LOD et trois vues contrôlés ; huit tests nouveaux. Ce sont des
  créations modernes statiques, muettes, sans slot alloué ni validation moteur.
- [Flammenwerfer 35 et No. 2](../FLAMMENWERFER_35_AND_NO2/MODELES_MODERNES.md) :
  deux ensembles extérieurs originaux fabriqués, sacs et tuyaux compris,
  21/19 pièces et deux LOD chacun. Huit tests supplémentaires et trois vues
  contrôlées ; ni animation, effet, son, comportement ou tenue en jeu validée.
- [Composants modernes des lance-flammes](../FLAMMENWERFER_35_AND_NO2/COMPOSANTS_MODERNES.md) :
  six modèles séparés, pièce tenue/sac/tuyau, géométrie et deux LOD conservés.
  Origines et raccords au repos vérifiés ; six planches inspectées et douze
  tests nouveaux. Ni attache au personnage ni déformation du tuyau réalisées.
- [Animations modernes de pièces](ANIMATIONS_MODERNES.md) : 18 séquences
  FG42/MG34 et leurs compagnons natifs construits, pivots et raccords contrôlés.
  514 poses entières évaluées hors moteur ; deux planches de rechargement
  inspectées avec un rendu de profondeur corrigé. Vingt nouveaux tests.
  Ni mains, événements, sons, caméra FPV ou comportement d'arme réalisés.
- [Mouvements des pièces tenues lance-flammes](../FLAMMENWERFER_35_AND_NO2/ANIMATIONS_PIECES_TENUES.md) :
  dix-huit séquences originales, 570 poses entières et deux planches contrôlées.
  Audit natif : 932 opérations d'attachement, 360 mises à jour et 568 appels
  de pose, résidu nul ; dix tests nouveaux. Mains, tuyau déformable, caméra et
  mécanique fonctionnelle restent à réaliser ; les sorties sont désactivées.
- [Tuyaux modernes déformables](../FLAMMENWERFER_35_AND_NO2/TUYAUX_ANIMES_MODERNES.md) :
  deux skins à deux LOD et dix-huit clips synchronisés aux pièces tenues.
  Huit os de tuyau par modèle, raccord fixe côté sac, mobile côté tenue ;
  1 122 poses intermédiaires et deux planches inspectées. Audit natif des deux
  LOD : 969 408 sommets, raccord tenu à moins de 1,99 × 10⁻⁸. Quatorze tests nouveaux.
  Ni physique, attache joueur/IA ou chargement conjoint des modèles qualifiés.
- [Assemblages modernes unifiés](../FLAMMENWERFER_35_AND_NO2/ASSEMBLAGES_ANIMES.md) :
  deux modèles sac/tenue/tuyau, neuf clips de onze pistes par ensemble ;
  géométries et clés conservées, douze aperçus identiques. 1 158 mises à jour
  natives persistantes et 1 000 512 sommets contrôlés ; treize tests nouveaux.
  Mains, attaches joueur/IA, caméra et fonctionnement d'arme restent à réaliser.
- [Prises modernes sur mains commerciales](../FLAMMENWERFER_35_AND_NO2/PRISES_MAINS_DERIVEES.md) :
  1 140 poses calculées sur les deux variantes de mains, longueurs conservées,
  prises distinctes et quatre planches privées inspectées. Palette et skin
  natifs contrôlés sur 1 178 190 sommets, poignet à moins de 1,15 × 10⁻⁷.
  Quatorze tests nouveaux ; géométrie commerciale intacte. Les clips sont
  traités ci-dessous ; pouces, contacts et caméra restent à réaliser ou qualifier.
- [Clips natifs de mains dérivés](../FLAMMENWERFER_35_AND_NO2/ANIMATIONS_MAINS_DERIVEES.md) :
  36 clips de 49 pistes construits pour les deux équipements et les deux
  variantes commerciales. Petites rotations natives prises en compte ;
  dix tests nouveaux et quatre planches inspectées. 2 316 mises à jour natives
  persistantes et 4 394 610 sommets contrôlés ; chargement et caméra non qualifiés.
- [Montages FPV aplatis](../FLAMMENWERFER_35_AND_NO2/MONTAGE_FPV_MODERNE.md) :
  deux modèles de 38/36 nœuds, 36 clips de 75/73 pistes et quatre planches
  privées construits ; sélection native du visuel et enfants directs contrôlés.
  Seize tests nouveaux ; chargement/copie de scène et caméra non qualifiés.
- [Association des os au skin racine](../FLAMMENWERFER_35_AND_NO2/MONTAGE_FPV_MODERNE.md#association-native-des-os-au-skin-racine) :
  les huit os de chaque tuyau sont découverts, triés et rattachés par le code
  natif, avec 77 arbres témoins. Calcul des limites et chargement/copie non exécutés.
- [Limites natives des tuyaux animés](../FLAMMENWERFER_35_AND_NO2/LIMITES_TUYAUX_ANIMEES.md) :
  enveloppes calculées à partir des boîtes sérialisées, comparées aux deux LOD
  déformés pendant les changements de clips : 352 instants, 304 128 sommets,
  aucun dépassement. Visibilité de scène et rendu non qualifiés.
- [Associations et lectures natives d'animations](../FLAMMENWERFER_35_AND_NO2/RESOLUTION_ANIMATIONS_FPV.md) :
  quatre laboratoires privés exclusifs, treize états chacun ; 156 demandes
  et 36 lectures/relocalisations natives vérifiées. Six tests nouveaux ; fichiers
  et allocations simulés en mémoire, aucune arme activée ou déclarée jouable.
- [Repères de vue subjective corrigés](../FLAMMENWERFER_35_AND_NO2/REPERES_VUE_SUBJECTIVE.md) :
  deux modèles modernes convertis intégralement, 36 clips de mains recalculés,
  quatre planches privées et associations distinctes. Conversion binaire
  réversible ; sources commerciales inchangées. Cadrage et prises fines non validés.
  Contrôle natif terminé : 2 668 instants et 5 062 530 sommets, limites respectées.
  Un écart de prise jusqu'à 0,040576 lors des mélanges reste à corriger ; il n'est
  pas masqué par la réussite des vérifications de calcul.
- [Contraintes de mains après mélange](../FLAMMENWERFER_35_AND_NO2/CONTACT_MAINS_ET_TRANSITIONS.md) :
  défaut localisé, correcteur de six rotations réalisé hors jeu. Sur 704
  observations, l'écart est ramené sous `1,696e-7`, palettes natives contrôlées.
  Le raccordement du correcteur au moteur reste à réaliser. Mesure de pénétration
  des doigts ajoutée ; première proposition de pouces non promue, car elle
  aggrave certaines intersections. Les banques v1 ne sont pas modifiées.
- [Prises ajustées modernes](../FLAMMENWERFER_35_AND_NO2/PRISES_AJUSTEES_MODERNES.md) :
  profil portable sans poses commerciales, flexions et pouces recalculés,
  36 clips dérivés privés et associations distinctes. Contrôle des triangles
  traversants ajouté, même lorsque tous leurs sommets sont extérieurs.
  En v6 : zéro pénétration au seuil de 0,01 mm sur 2 244 poses échantillonnées
  contre les pièces convexes ; 2 316 instants natifs et 156 demandes de ressources
  contrôlés. Les pièces non convexes restent explicitement exclues.
  Les contacts complets et le raccordement du correcteur au moteur restent à réaliser.
- [Matrices natives de caméra](PROJECTION_CAMERA_NATIVE.md) : setters des deux
  angles et trois matrices de perspective exécutés sur un objet fourni.
  352 cas, dont 88 ultra-larges, écart nul ; sélection réelle du rendu FPV,
  viewport et effets du correctif écran large non qualifiés.
- [Garota et ZK-383 modernes](../GAROTA_AND_ZK383/MODELES_MODERNES.md) :
  deux extérieurs distincts créés sans archive commerciale, 7/33 pièces et
  deux LOD chacun. Six tests nouveaux, empreintes et trois vues contrôlées.
  Référence muséale textuelle attribuée pour le ZK-383 ; Garota explicitement
  interprétative. Mains, animations, comportement et intégration restent à réaliser.
- [Animations modernes ZK-383](../GAROTA_AND_ZK383/ANIMATIONS_ZK383_MODERNES.md) :
  neuf clips de pièces, deux pivots et 537 poses d'auteur contrôlées ; huit tests
  nouveaux. Neuf lectures natives, 466 opérations d'attachement et 180 instants
  vérifiés, écart de poses nul. Mains, événements et comportement restent à réaliser.
- [Banques FPV rigides FG42/MG34/ZK-383](BANQUES_FPV_RIGIDES.md) : trois modèles
  avec racine visuelle et enfants directs, 27 clips recalculés, axes convertis
  de manière réversible. Comparaison de 1 547 clés/demi-clés, résidu MG34
  intermédiaire explicitement conservé ; sept tests nouveaux. Mains, cadrage,
  associations et comportement restent à implémenter ou qualifier.
  Lecture native des 27 clips et 1 601 instants/palettes diagnostiques contrôlés ;
  aucun chargement/copie de modèle en scène ou rendu qualifié.
- [Mains FG42/MG34/ZK-383](MAINS_ARMES_RIGIDES.md) : 54 clips dérivés privés,
  1 574 poses d'auteur, prises/pouces/coudes modernes paramétrés et six groupes
  de ressources construits. 234 demandes et 54 lectures natives effectuées.
  Contrôle natif v2 : 3 202 instants et 6 404 palettes ; 104 dépassements de
  seuil bruts entre clés, corrigés hors jeu mais sans raccordement client.
  Les collisions de surfaces sont mesurées, y compris sur les pièces creuses ;
  prise droite ZK-383, gestes, cadrage et comportement restent à réaliser/qualifier.
- [Paramètres de tir](PARAMETRES_TIR.md) : 18 colonnes rapprochées des données
  natives de 40 armes dans quatre couches. Onze différences de paramètres
  conservées sur six fiches, deux symboles FG42 explicitement non résolus.
  Huit tests nouveaux ; aucune entrée Weapon ni allocation créée.
- [Fiches générales d'objets](PARAMETRES_OBJETS.md) : 500 emplacements comparés
  dans chacune des deux couches Sabre/PatchX01 ; 272 objets présents, treize
  exceptions de munition/quantité conservées par couche. Onze tests nouveaux.
- [Descripteur moderne Benelli](../BENELLI_M4_ADDITIVE/DESCRIPTEUR_MODERNE.md) :
  premier record Weapon de 508 octets assemblé sans copie intégrale d'un donneur,
  relu par les routines natives isolées, munition 179 initialisée à 7 et treize
  liaisons FPV contrôlées. Seize tests nouveaux ; aucune insertion dans les
  tables et comportement moteur non validé. Les textes sont préparés séparément ci-dessous.
- [Descripteur et tables MG34](../MG34_PORTABLE/DESCRIPTEUR_ET_TABLES.md) : fiche
  moderne de 508 octets, munition portative 201 initialisée à 75, sons 34/38,
  libellé 21501 dans huit langues ; deux variantes de mains et cinq laboratoires
  complets construits. Dans chacun, 273 descripteurs et 500 emplacements parcourus,
  retrait exact, 272 objets et 277 groupes existants préservés. Les dix objets
  et six groupes modifiés des tables personnelles sont conservés. Seize tests
  synthétiques nouveaux ; fichiers désactivés, contacts et gameplay non qualifiés.
- [Action secondaire Benelli](../BENELLI_M4_ADDITIVE/ACTION_SECONDAIRE.md) :
  182 fiches commerciales, le descripteur moderne et quatre contrôles synthétiques
  vérifiés sur leurs branchements natifs isolés ; 48 transitions de paramètre caméra.
  Le manifeste personnel v2 intègre ce contrôle sans changer ses quatorze fichiers
  désactivés. Ni opération complète de visée, ni scène ou rendu exécutés.
- [Références sonores](REFERENCES_SONORES.md) : 14 banques/539 entrées décodées,
  indices de tir/rechargement contrôlés sur 168 fiches commerciales et le
  descripteur moderne Benelli. Benelli 36/54 et MG34 34/38 identifiés, FG42
  toujours symbolique. Dix tests nouveaux ; aucune lecture audio ni synchronisation
  moteur validée. Le banc Benelli v2 conserve les mêmes binaires et ajoute ces contrôles.
- [Textes d'inventaire modernes](TEXTES_INVENTAIRE_MODERNES.md) : libellé Benelli
  21500 préparé dans huit langues après contrôle de quinze tables et des références
  d'objets. La plage des missions personnalisées 22000–65000 est protégée ; les
  anciens textes restent intégralement conservés. Quinze tests nouveaux, retrait
  exact en mémoire et raccordement au descripteur v3 ; affichage moteur non validé.
- [Tables complètes Benelli](../BENELLI_M4_ADDITIVE/TRANSACTION_TABLES.md) :
  deux variantes Sabre/PatchX01 désactivées construites ; 273 descripteurs relus
  par variante, 272 objets commerciaux et 277 groupes FPV conservés à l'identique.
  Ajout puis retrait exact des deux tables en mémoire, sans agrandir la capacité.
  Dix-huit tests nouveaux ; ni installation, fusion de surcharges ou validation jeu.
- [Parcours natif des tables](../BENELLI_M4_ADDITIVE/PARCOURS_NATIF_TABLE.md) :
  boucle originale de 500 emplacements exécutée sur les deux sources et les deux
  ajouts désactivés, soit 2 000 passages et 1 090 objets contrôlés ; curseurs et
  pointeurs vides concordants. Huit tests nouveaux ; aucun appel système ou jeu.
- [Parcours natif FPV](../BENELLI_M4_ADDITIVE/PARCOURS_NATIF_FPV.md) : boucles
  imbriquées et chaînes originales contrôlées ; 278 groupes/614 références dans
  la table Benelli désactivée, cellules inoccupées préservées. Onze tests nouveaux,
  deux laboratoires v2 avec les mêmes contenus ; ni scène ni animation exécutée.
- [Mains et cibles FPV](../BENELLI_M4_ADDITIVE/MAINS_ET_CIBLES_FPV.md) : deux
  modèles de mains et trois textures verrouillés, 448 correspondances de pistes
  sur les neuf animations et deux variantes ; plan joint aux laboratoires v3.
  Treize tests nouveaux ; skin, héritage des poses partielles et caméra non validés.
- [Rotations natives corrigées](ROTATIONS_NATIVES.md) : 72 matrices de repos
  et 224 rotations initiales recoupées indépendamment. Modèle Benelli et
  18 animations modernes reconstruits ; géométrie, tables et textes préservés.
  Seize tests nouveaux et voie sûre de renouvellement des préparations inactives.
  Trois nouveaux cycles Benelli de pose/retrait retrouvent les 24 385 fichiers
  initiaux de chaque copie ; les anciennes préparations restent récupérables.
  La déformation des mains et le comportement moteur ne sont pas encore qualifiés.
- [Calcul d'animation natif](CALCUL_ANIMATION_NATIF.md) : matrices, interpolation
  et échantillonnage des canaux examinés en émulation bornée, sans chargement
  de bibliothèque Windows. 20 220 échantillons sur 224 canaux de rotation
  Benelli concordent, ainsi que 5 124 positions et 66 échelles ; 29 tests
  synthétiques nouveaux. Non-normalisation et facteur temporel explicités.
  L'héritage réel, le skin et les unités de temps restent distincts.
- [Poses partielles natives](POSES_PARTIELLES_NATIVES.md) : 586 poses sur un
  objet synthétique recoupent les huit emplacements, l'ordre des mélanges,
  les canaux absents et la normalisation finale. Douze tests nouveaux ;
  chargement réel du modèle et pilotage Benelli non qualifiés.
- [Sélection native des cibles](LIAISON_ANIMATION_NATIVE.md) : 1 022 recherches
  exactes et 4 088 préparations de canaux contrôlées sur Benelli/deux mains et
  FG42/MG34 modernes ; 22 témoins natifs et neuf tests nouveaux. L'attachement
  effectif, l'allocation et le chargement de scène ne sont pas exécutés.
- [Temps d'animation natif](TEMPS_ANIMATION_NATIF.md) : durée et progression
  des huit pistes recoupées sur 774 cas sans objet cible. Fin, lecture inverse,
  boucle à correction unique et conservation des pistes inactives explicitées.
  Douze tests nouveaux ; horloge en secondes et callbacks non qualifiés.
- [Déformation native des mains](DEFORMATION_MAINS_NATIVE.md) : noyau CPU
  recoupé sur 4 376 sommets synthétiques et 80 613 déformations des mains
  commerciales avec matrices de diagnostic. Indices de sommets base un et
  poids parental octet/256 établis ; quatorze tests nouveaux. Construction
  des matrices depuis une animation et fonctionnement en jeu encore distincts.
- [Matrices natives des mains](PALETTE_MAINS_NATIVE.md) : hiérarchie, cache
  parental, rotations/échelles et inverse de repos recoupés sur 748 joints
  synthétiques, puis 74 poses de diagnostic des mains / 76 479 sommets.
  Quatorze tests nouveaux ; aucune sélection de pose commerciale ou scène chargée.
- [Chaîne d'animation des mains](CHAINE_ANIMATION_MAINS.md) : neuf clips
  commerciaux × deux mains, 90 mesures de frontières puis 1 462 mesures
  denses ; ces dernières couvrent 54 094 poses et 1 510 977 sommets.
  Pose, matrices et peau raccordées avec départ explicite au repos ; dix tests
  nouveaux. Initialisation réellement choisie et transitions en jeu non qualifiées.
- [Transitions de poids FPV](TRANSITIONS_POIDS_FPV.md) : 393 cas de mélange,
  350 retraits de la liste cliente et 698 réglages natifs de poids sur un
  contrôleur synthétique. Treize tests nouveaux ; détachement réel et
  rafraîchissement de scène non exécutés, transitions visuelles non qualifiées.
- [Attachement natif des animations](ATTACHEMENT_ANIMATION_NATIF.md) :
  1 864 opérations sur les deux mains Benelli et les banques FG42/MG34,
  8 370 structures de cible créées puis libérées ; 304 opérations synthétiques
  supplémentaires. Quinze tests nouveaux. Allocation bornée simulée,
  chargement réel, pose et scène non exécutés par ce banc.
- [Préparation des transitions FPV](SELECTION_PISTE_FPV.md) : 848 cas de
  sélection du cache et des emplacements, paramètres initiaux et arguments
  d'attachement contrôlés. Douze tests nouveaux. La sélection de 3 après
  occupation de 0/1/2 est conservée, sans preuve d'une collision en jeu.
- [Contrôleur et poses unifiés](CONTROLEUR_POSES_UNIFIE.md) : attachement,
  progression du temps et calcul des poses raccordés dans la même mémoire
  native. 720 mises à jour / 8 706 appels de pose sur les quatre banques,
  résidu nul ; treize tests nouveaux. Poses persistantes et ordre des fins
  contrôlés, condition initiale explicite ; chargeur, événements et rendu exclus.
- [Décision de transition](SELECTION_PISTE_FPV.md#décision-amont-et-copie-de-la-piste-précédente) :
  3 112 cas, 2 852 consultations natives d'activité et 1 308 copies de piste
  précédente. Capacité de liste préparée ; attachement/rafraîchissement simulés.
- [Enchaînements en mémoire persistante](ENCHAINEMENT_ANIMATIONS_NATIF.md) :
  attachement, poids, lecture et remplacement de clips sans réinitialisation des
  poses. Huit scénarios sur quatre banques de lance-flammes : 1 152 opérations,
  352 avancées et 25 456 calculs de pose, écart nul. Décision cliente et chargeur
  encore séparés ; contacts pendant les mélanges, scène et rendu non qualifiés.
- [Demandes de ressources FPV](../BENELLI_M4_ADDITIVE/DEMANDES_RESSOURCES_FPV.md) :
  treize cas de noms de mains et 156 demandes d'animation contrôlés jusqu'aux
  arguments des chargeurs, sans les appeler. Quinze tests nouveaux ; laboratoires
  v4 avec 39 demandes supplémentaires chacun et contenus désactivés inchangés.
- [Surcharges centrales](../BENELLI_M4_ADDITIVE/SURCHARGES_CENTRALES.md) : ajout
  désactivé composé sur les tables personnelles, dix fiches et six groupes
  personnalisés conservés intégralement. 273 objets/632 références relus par
  les routines natives et retrait exact en mémoire. Douze tests nouveaux ;
  déploiement et compatibilité des autres surcharges restent distincts.
- [Contrôle des ressources](../BENELLI_M4_ADDITIVE/CONTROLE_RESSOURCES.md) :
  onze archives, 52 entrées pertinentes dont 18 variantes de textures ; aucun
  conflit d'alias moderne ni surcharge libre candidate dans les espaces
  examinés. Huit tests nouveaux ; choix réel des formats/compressions non validé.
- [Déploiement Benelli isolé](../BENELLI_M4_ADDITIVE/DEPLOIEMENT_ISOLE.md) :
  douze cibles strictes préparées dans les trois copies ; pose/relecture/retrait
  vérifiés sur l'hôte, 24 385 fichiers initiaux retrouvés. Les deux nouveaux
  modèles retirés restent récupérables dans l'historique. Vingt et un tests nouveaux ;
  aucune partie lancée et aucun résultat moteur acquis.
- Trois comparaisons binaires Co_Burgundy1/2/3 supplémentaires reconstruisent
  respectivement douze/deux/dix porteurs et leurs liaisons sans modifier les scripts
  ou sons. Elles restent inertes, hors compte des laboratoires de mission.
- **180 dossiers** recensés. Les études continuent : certains vestiges exigent
  encore une cible, un propriétaire, une ressource ou une observation préalable.
- L'installation actuelle n'est pas modifiée. Cinq profils refusent ses
  surcharges pertinentes en mode strict; les exclusions et empreintes sont
  consignées pour Africa 1, Normandy 1 et Africa 5.
- **Trois copies indépendantes** pour hôte/deux clients : 24 385 fichiers et
  6 508 813 370 octets chacune, même manifeste initial, aucun lien partagé.
  La [voie d'essai native](../../validation/ESSAIS_NATIFS.md) prépare les
  **50 configurations** dans chacune, sans nouveau menu ni lancement du jeu.
  La transition Africa 4 sur témoin radio Heritage a été ajoutée le 27 septembre,
  après fermeture indépendante du client externe ; aucun processus fermé par
  l'agent et aucune protection contournée.
- **92 cycles réels de fichiers**, en quatre rapports conservés : 49 pour la
  première série, 28 pour les quatorze ajouts, 13 pour les huit profils suivants,
  puis deux pour la composition Africa 4.
  La comparaison globale finale
  retrouve tous les fichiers initiaux dans les trois copies. Ces cycles ne sont pas des essais en jeu.

Ces nombres ne signifient pas que la reconstruction globale est terminée :
le registre du paquet stable reste à **56 cas pending**, et les 21 candidates
multijoueur vers solo n'ont toujours aucune validation de jeu. Le nouveau
[registre expérimental](../../validation/RECONSTRUCTION.md) suit séparément
**50 profils et 304 contrôles pending**, sans inventer de résultats moteur.
Un [préparateur de fiches](../../validation/RECONSTRUCTION.md#préparer-les-fiches-sans-rien-lancer)
réunit désormais les protocoles, manifestes exacts, incompatibilités et consignes
de retour arrière. Les nouveaux outils d'essais natifs prennent maintenant en
charge la copie indépendante et le déploiement réversible. Les sept variantes
Africa 5 et l'ambiance Co-Burgundy 1 exigent d'abord une preuve réelle du témoin
natif : leurs références commerciales absentes sont préservées, pas remplacées
par des scripts inventés. Aucun jeu ni installateur n'a été lancé par ces outils.

| État | Sens |
|---|---|
| Documenté | Une étude existe déjà dans `experimental/`. |
| À documenter | Les faits sont inventoriés ici, mais aucun dossier dédié n'existe encore. |
| Bloqué preuve | Un propriétaire, une position, une ressource ou un contrat manque. |
| Prototype désactivé | Une proposition existe mais ne peut pas être distribuée active. |
| Faux positif | La fonctionnalité est déjà remplacée ou la restauration serait trompeuse. |
| Validation jeu | La preuve statique existe, mais les essais en moteur restent obligatoires. |

## Carte du registre

- [Missions et scripts](MISSIONS.md) : toutes les missions et chaînes de signaux
  connues, y compris les éléments encore sans dossier dédié.
- [Armes, véhicules, avions et conversion solo](SYSTEMES_ET_ASSETS.md) : ressources
  transversales, collisions d'identifiants et limites techniques.
- [Validation et critères de promotion](VALIDATION.md) : contrôles à appliquer
  avant toute activation ou intégration dans les outils publics.
- [Catalogue physique](CATALOGUE_DOSSIERS.md) : liste exhaustive des dossiers
  expérimentaux présents sur cette branche et de leurs fichiers directs.
- [Outils et démarrage](OUTILS_ET_DEMARRAGE.md) : installation isolée,
  commandes d'audit, construction et checklist avant la première modification.
- [Références et provenance](REFERENCES.md) : hiérarchie des preuves, archives,
  rapports internes, sources externes et règles de conservation.
- [État de préparation](ETAT_PREPARATION.md) : photo vérifiée de la branche et
  de l'environnement juste avant le début des travaux.
- [Variantes reproductibles](VARIANTES_REPRODUCTIBLES.md) : quarante-sept profils et cinquante-cinq scripts
  expérimentaux générés localement, contrôles automatisés, provenance,
  conflit de surcharge Africa 1 et validations en moteur encore en attente.
- [Laboratoires désactivés](LABORATOIRES_DESACTIVES.md) : copies A/B complètes,
  fermeture des scripts et préservation des objectifs Base/Sabre, sans installation.
- [Ressources modernes](RESSOURCES_MODERNES.md) : autorisation utilisateur,
  provenance séparée et premier modèle extérieur original Benelli. Un modèle
  statique ne constitue ni une arme jouable ni une animation FPV compatible.

## Travaux immédiatement recommandés

1. Poursuivre les contrats encore incomplets : synchronisations coop, positions
   réellement absentes et autorité des événements réseau. Les lignes de missions
   auparavant « À documenter » ont désormais une étude ou un renvoi précis.
2. Conserver fermés les faux positifs prouvés; ne pas recréer les six barils du
   dépôt Co_Burgundy3 ni réactiver le signal maquis remplacé par l'alarme.
3. Utiliser les trois copies de test isolées déjà préparées et observer les signaux
   ambigus avant de proposer une réaction inventée; aucun résultat moteur n'est
   encore acquis.
4. Tester les variantes en solo, Carnage et coopération quand la mission existe
   dans plusieurs modes.
5. Ne promouvoir un prototype qu'après réussite des contrôles décrits dans
   [VALIDATION.md](VALIDATION.md).

## Limites de cet inventaire

Ce registre décrit les preuves actuellement accessibles dans le dépôt et dans les
archives commerciales examinées. Il ne prétend pas que chaque intention originale
est récupérable. Les points explicitement marqués « moderne » sont des créations
compatibles avec les vestiges, pas des contenus historiques authentifiés.
