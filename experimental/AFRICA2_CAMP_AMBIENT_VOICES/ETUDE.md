# Africa 2 — voix d'ambiance retirées

État : sept contrôleurs étudiés, conflit de source identifié, 26 septembre 2026.
Aucun propriétaire ni son ajouté; aucune voix commerciale redistribuée.

## Sept scripts ne signifient pas dix-sept voix indépendantes

Tous les scripts `V_Af2snd_sypek*.scr` sont présents dans Patch.dta, non liés
et non atteints par les dépendances littérales. Aucun autre script Africa2
consulté ne référence littéralement leurs sources `S_sypek*`.

| Suffixe du script | Sources sonores visées | Attente après activation, ms |
|---|---|---|
| A1 | m02, w02 | random(9000)+4000 |
| A2 | m01, m03, w01 | random(8500)+5500 |
| B1 | m05, m06, m12 | random(13000)+3500 |
| B2 | **m03**, m04 | random(9500)+4500 |
| B3 | m07, w03, w04 | random(14000)+4000 |
| C1 | w05, m10 | random(10000)+6000 |
| C2 | m08, m09 | random(8700)+5000 |

Préfixe commun des frames : `S_sypek_`. Il y a **17 références mais 16 sources
distinctes**, toutes présentes. m03 est partagée par A2 et B2. Le sounds.bin
contient une dix-septième source, m11, que ces sept scripts ne commandent pas.
Le constat initial « sept scripts / dix-sept frames pilotées » est corrigé.

Chaque boucle choisit et active une voix **avant** sa première attente. Relier
les sept fichiers au démarrage pourrait donc lancer sept voix immédiatement,
et pas sept émissions déjà espacées. Deux instances peuvent agir sur m03; la
réaction exacte à un second SetOn pendant la lecture doit être mesurée.

## Ressources décodées et durées mesurées hors moteur

Les seize sources utilisent six ressources indexées dans Sounds.dta :

| WAV, préfixe `l_Af2pour` | Octets décodés | Trames à 22050 Hz | Durée, s |
|---|---:|---:|---:|
| m1 | 292410 | 146183 | 6,629615 |
| m2 | 194092 | 97024 | 4,400181 |
| m3 | 143660 | 71808 | 3,256599 |
| m4 | 192426 | 96191 | 4,362404 |
| w1 | 166956 | 83456 | 3,784853 |
| w2 | 149676 | 74816 | 3,393016 |

Les noms des ressources sont lus dans 0x4060/0x10 des sources sonores, avec
extension WAV résolue dans l'index. Le blocage DPCM initial a été levé dans
le lecteur Python : les six fichiers ont été décodés **en mémoire**, avec
validation de l'en-tête, du nombre d'échantillons et de la taille totale.
Ils sont mono PCM16. Méthode et empreintes dans le
[registre audio](../RECONSTRUCTION_BACKLOG/AUDIO_RESSOURCES.md).
Ces mesures ne constituent pas une écoute ni un essai de lecture dans le jeu.
Certaines attentes minimales sont inférieures à la durée du clip choisi,
par exemple 3500 ms dans B1 face à m1 de 6,63 s : tester aussi le rejeu local.

## Variante moderne à préparer

Les positions des **sons** sont officielles et dispersées dans trois zones;
le propriétaire d'exécution des sept scripts n'est pas établi. Conserver les
sons existants et choisir un seul contrôle pour m03. Pour un premier essai,
activer un seul groupe, puis A2 et B2 sous arbitrage commun, avec délai initial
explicite et annulation; ne pas renommer ou dupliquer m03 pour cacher le conflit.
Une régulation spatiale, un verrou ou une nouvelle cadence sont MODERNES.

Vérifier les durées effectives et portées, les entrées/sorties de zone, l'alarme, la mort
des personnages visibles et la sauvegarde. Les sources sont des frames audio,
pas des acteurs identifiés : aucune synchronisation labiale ou identité de
locuteur n'est démontrée. Garder vents et bruits de ferraille actifs séparés.

Le registre actuel comporte 72 liaisons, 63 scripts racines, 85 fichiers
disponibles; la fermeture atteint 67 noms dont un absent,
`af2_particle_junkers.scr`. Le problème est déjà
[étudié](../AFRICA2_JUNKERS_PARTICLE_OWNER/ETUDE.md) : pas de script substitut
ni de seconde fumée pour fabriquer un laboratoire « complet ».

## Provenance

sounds.bin : missions.dta, 13432 octets, SHA-256
`392bd8d75340c152782c7e4a83638efecff44b29869a581e3241cbc03a0d6175`.
scripts.dta : missions.dta, 2993 octets, SHA-256
`25b04862dcd9d7c1d0485b913e67579b3f91dc1f7c47bf731fa394dfc279af9d`.
Scripts A1/A2/B1/B2/B3/C1/C2 : 329/419/420/331/420/332/331 octets.
Empreintes respectives :

```text
484c70f39c4891c7f7851f19214535c39600ebae2df79c2fe18c4d6e7f20a8be
2940825341b1ada7263d3b1b2605c699289f74b5922a8dc26ab85c1acde4f809
eff98b99eea61350b67daabaabfdf92d2feb7aa2c5471cb40c0bf64101bf080f
15b237d11556efbc39e3db9778591cd527f5b6d09a8227676034eb11770ae2b9
13075131194653c225877e02041b7ef9a8fadd69af4cb35b8c941fcff80ad165
db7372641508432f95821854ed6102a7b9be9e2fbba65e0f93be9ce85720906b
55b6ead6f9d7f9a51f6b2edfa3990be6d67369f021dbdfb2e3b1127e26fc6d25
```
