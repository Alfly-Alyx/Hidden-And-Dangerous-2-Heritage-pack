# Correction des mains sur des nœuds dispersés

Implémentation originale C du **10 octobre 2026**, désactivée et sans chargement
Windows. Elle lève l'obligation de disposer de nœuds natifs contigus pour appeler
le calculateur, mais ne découvre pas les pointeurs d'un modèle chargé et ne gère
pas encore leur durée de vie.

## Contrat réalisé

`Hd2CorrectScatteredHandPose` reçoit une identité de modèle, onze à 128 vues
de nœuds et les liaisons fournies par l'appelant. Chaque vue contient un pointeur
et une longueur valide garantie par son propriétaire. Les plages doivent être
distinctes, alignées sur quatre octets, sans débordement d'adresse et couvrir
au minimum les `0x10c` premiers octets utilisés. Les parents doivent précéder
leurs enfants ; les pointeurs de parent réellement présents dans les nœuds
sont comparés à la hiérarchie déclarée. Les racines doivent être directement
rattachées à l'identité de modèle fournie.

Le code collecte P/Q/S, indicateurs et types dans un espace privé de **61 808
octets** fourni par l'appelant. Il appelle ensuite le calculateur complet existant.
Avant toute écriture native, il relit les poses, indicateurs, types et parents
de **tous** les nœuds. Un échec, même au dernier nœud ou après calcul des deux bras,
n'applique aucune rotation native. En cas de réussite, seuls les six quaternions
et leurs indicateurs sont recopiés dans les destinations dispersées.

Cette vérification ne constitue pas une synchronisation multithread : les vues,
entrées et destinations doivent rester valides, distinctes et exclusivement
possédées pendant tout l'appel. Le code ne peut pas déterminer si un pointeur
arbitraire est alloué ou si un modèle a été détruit. La détection tardive de
changements est une protection supplémentaire, pas une garantie contre une
libération concurrente.

## Résultats isolés

Le binaire désactivé fait 19 456 octets, sans import système, SHA-256
`b6c39defcef9a92834a507d25650f496bf6fecd13b3719ca2943bbe28d94c958`.
Son point de chargement ordinaire refuse l'activation.

Huit cas valides combinent onze / 128 nœuds, parents droits / tournés et
alignement sur seize / seulement quatre octets. Chaque nœud est placé dans une
page indépendante, dans un ordre non monotone, avec une page non mappée entre
les allocations. Les octets hors des six rotations et indicateurs sont comparés
intégralement, ainsi que les entrées et les gardes de travail.

Dix-neuf refus couvrent tailles, rôle, modèle absent, plage courte, recouvrement,
débordement d'adresse, cycle ou changement de parent, type / callback invalide,
bras hors portée et quaternion nul. Cinq de ces cas injectent explicitement un
changement **après** le retour du calculateur : repère, quaternion, indicateurs,
type ou parent du dernier bras. Aucun de ces refus n'effectue d'écriture native
du correcteur ; la mutation injectée par le banc est comptée séparément.

Écart maximal des huit cas valides par rapport au calcul indépendant :
`4,882828253e-8`. Aucun modèle, animation, code ou processus du jeu n'est utilisé
dans ces contrôles ; seul le programme C original est exécuté en émulation.

## Suite

Le collecteur est désormais [branché sur un contexte enregistré et le relais natif](RELAIS_MAINS_DISPERSE.md),
en complément du banc contigu. Il reste à établir l'identité et la durée de vie
des modèles réels et leurs tailles d'allocation. Le skin, le budget par frame et la validation
en jeu ne sont pas couverts par ce lot. Aucun équipement n'est déclaré jouable.

Reproduction : `tools/build_native_hand_scatter.py --output-name HandScatter_Compiled_v1`,
avec une destination neuve. Le binaire et son manifeste restent dans
`.analysis/modern-assets/`, hors du dépôt et de l'installation du jeu.
