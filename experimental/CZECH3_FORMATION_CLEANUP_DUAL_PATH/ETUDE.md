# Czech 3 — dissolution de la formation de zlesa1

État du 25 septembre 2026 : **variante MODERNE conditionnelle désactivée**,
construite et contrôlée hors jeu. La nécessité en jeu reste à démontrer : la
présence de deux lignes commentées n'est pas une preuve de bug commercial.

## Contrat commercial et différence entre les deux voies

Deux détecteurs liés utilisent `detector_zlesa1.scr`, chacun avec une proximité
de 40 m. Ils envoient le signal 1 à `zlesa1`. Le chef réveille `zlesa2`, attend
500 ms, crée une formation, ajoute ce second acteur, impose une ligne, puis
lui envoie le signal 2. Il part ensuite sur sa route commerciale.

À l'alarme de `zlesa1`, deux vestiges sont commentés : signal 1 au coordinateur
`zlesa_zrusformaci`, puis `FORMATION_Destroy(me)`. Le coordinateur existe, est
lié et contient bien `FORMATION_Destroy(zles1)` à la réception du signal 1,
mais aucun émetteur actif vers ce coordinateur n'a été trouvé dans les scripts
locaux inspectés.

`zlesa2` se retire déjà lui-même dans son `OnAlarm` avec
`FORMATION_DelMember(me)`, puis éventuellement une seconde fois sous sa garde
locale `form`. Ce retrait d'un membre n'est pas textuellement la destruction
du groupe par son chef. Il peut suffire dans certains scénarios, mais ne permet
pas de classer l'ensemble comme faux positif sans observer l'alarme du chef
seul, celle du membre seul et les morts.

## Choix expérimental

Le profil `czech3-leader-formation-cleanup` du
[catalogue](../reconstruction-variants.json) retient **un seul responsable de
la dissolution : le chef**, sans réveiller en plus le coordinateur historique.
Il modifie uniquement `zlesa1.scr` :

1. L'entier local `form`, déjà déclaré à zéro et inutilisé dans ce script,
   devient 1 après `FORMATION_SetTypeLine(me)` dans le bloc de création.
2. À la place du `Destroy` commenté, un test `form == 1` remet d'abord l'état
   à zéro puis appelle `FORMATION_Destroy(me)`.

Le signal vers le coordinateur reste commenté. Le membre, les détecteurs, les
routes, les délais, les alarmes et les signaux de renfort ne changent pas.
L'alarme précédant la création ne doit donc pas demander la destruction d'une
formation encore inexistante; une nouvelle alarme après dissolution ne doit
pas relancer l'appel. Ce sont des propriétés de la garde ajoutée, pas une
preuve de la durée de vie moteur d'une formation.

Ce choix est moderne : la primitive de destruction est historique, mais sa
condition et l'armement de `form` ne sont pas des lignes commerciales. Il ne
répare ni une éventuelle double création préexistante via les deux détecteurs,
ni la gestion de mort du chef. Ces scénarios restent dans le protocole A/B.

## Preuves et résultats

Huit sources sont épinglées : quatre scripts de la chaîne, registre, acteurs,
scène et checkpoints. Les deux humains sont sérialisés dans `actors.bin`;
les deux détecteurs et le coordinateur dans `scene2.bin`. Les noms du fichier
de checkpoints sont `Zlesa_01` à `Zlesa_11`, avec une majuscule initiale;
les appels minuscules commerciaux restent inchangés. `Zlesa_12/13` existent
aussi mais aucun nouveau segment n'est ajouté.

Source : 2775 octets, SHA-256
`5d13ac28fb56796d48467853ac3a312b99f945bc6afcc865313bd70de9b08be7`.
Sortie : **2817 octets**, SHA-256
`072bf39ada1e412789b8777168a7e3001bcf49b85622b07dd7526d0d8efaa67c`.
Le laboratoire conserve 99 fichiers, 76 scripts accessibles et quatre
objectifs par branche. Trois tests vérifient l'armement après création,
l'effacement avant destruction et les séquences répétées du modèle local.

## Protocole encore requis

1. Comparer le témoin et la variante avant les détecteurs, pendant les 500 ms,
   pendant la création et sur les onze segments de route.
2. Alarmer chef seul, membre seul, puis les deux dans les deux ordres. Relever
   appartenance effective, ordre des appels et autonomie de combat.
3. Répéter l'alarme et les deux détecteurs : pas de nouvelle dissolution à tort,
   pas de formation vide persistante ni de réadhésion involontaire.
4. Tester mort du membre avant création, mort du chef en route, retrait déjà
   effectué et destruction d'un groupe vide. Ne pas supposer l'API idempotente.
5. Sauvegarder/reprendre avant création, en formation et après dissolution;
   contrôler la garde locale, le renfort, les objectifs et la fin de mission.

Si le moteur libère déjà correctement le groupe dans le témoin, conserver le
commercial et classer la variante non nécessaire. Aucun essai de cette liste
n'a encore été effectué en jeu.
