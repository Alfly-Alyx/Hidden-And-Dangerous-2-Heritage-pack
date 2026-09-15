# Étude expérimentale — état détruit des caisses d'Alps3_Obj

État : proposition désactivée, 14 septembre 2026. Aucun fichier commercial,
registre, scène, installateur ou outil n'est modifié. Aucun script n'est
compilé.

Cette étude applique le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md) :
la mission Sabre reste la référence et toute image supplémentaire devient un
ajout moderne, révocable et désactivé par défaut.

## Verdict

Le nom commenté `bedny_crash` ne correspond pas à un élément commercial
intact retrouvé. Il n'existe dans les données inspectées ni frame ni modèle de
ce nom ; le seul témoin est la déclaration commentée de `Alps3_delo.scr`.

En revanche, l'acteur commercial `bedny` contient deux indices adjacents et
cohérents : son modèle placé est `m_l3_bed02` et son enregistrement d'acteur
contient aussi `m_L3_bed01crash`. L'appel actif
`SetActorState(bedny, 1)` peut donc déjà sélectionner l'état détruit intégré de
l'acteur. Cette interprétation est la plus économique, mais doit être confirmée
en jeu : la présence des chaînes dans le binaire ne démontre pas à elle seule
quel rendu persiste après l'état 1.

La variante recevable suit donc un verrou en deux temps :

1. tester d'abord la release sans aucune frame ajoutée ;
2. n'autoriser `bedny_crash_modern` que si l'état 1 commercial ne laisse aucune
   épave de caisses crédible.

Si l'état 1 laisse déjà une épave visible, la branche moderne est rejetée. Elle
produirait une double géométrie et n'apporterait aucune restauration.

## Preuves commerciales

| Source inspectée | Observation | Portée |
| --- | --- | --- |
| `Scripts/Alps3_obj/Alps3_delo.scr` | cherche `bedny`; les lignes qui cherchent `bedny_crash`, l'éteignent et forcent `bedny` visible sont commentées | atteste une idée abandonnée, pas un objet livré |
| même script, logique active | à l'état 2 de `w_explosive_02`, passe `dummy_expl_02` et `bedny` à l'état 1, attend 200 ms, puis passe `dummy_expl01` à l'état 1 et `la_Pak_` à l'état 2 | comportement release à conserver mot pour mot |
| `Missions/Alps3_obj/actors.bin` | contient l'acteur `bedny`, le modèle placé `m_l3_bed02` et, dans l'enregistrement d'acteur, `m_L3_bed01crash` | forte preuve d'un état crash intégré au même acteur |
| `scene2.bin` | aucune chaîne `bedny`, `bedny_crash`, `m_l3_bed02` ou `m_L3_bed01crash` | aucun double décoratif retrouvé dans la scène |
| `check2.bin` | contient `la_Pak_`, mais aucun des quatre noms ci-dessus | aucun checkpoint `bedny_crash` retrouvé |
| `mpscripts.dta` | lie `la_Pak_` à `Alps3_delo.scr`; ne contient pas `bedny_crash` | le déclencheur release est résolu ; aucun binding manquant pour le vestige |

Deux comparaisons commerciales renforcent la prudence sans résoudre la
sémantique exacte des états :

- `Co_Libye3/actors.bin` contient un acteur `bedny` associé à
  `m_L3_bed02crash` ; son script d'objectif agit aussi sur cet acteur après une
  explosion, mais avec une autre valeur d'état ;
- `Ardens1_delo2.scr` et `Ardens1_delo3.scr` passent leurs ensembles de caisses
  à l'état 1 dans une séquence d'explosion analogue.

Ces parallèles attestent des variantes commerciales de caisses destructibles.
Ils ne prouvent ni un frame `bedny_crash` dans Alps3, ni la valeur d'état à
appliquer à un acteur nouvellement créé.

## Baseline intangible

La séquence suivante reste autoritaire, y compris son délai de 200 ms :

1. `w_explosive_02` atteint l'état 2 ;
2. `dummy_expl_02` et `bedny` passent à l'état 1 dans le même bloc ;
3. après 200 ms, `dummy_expl01` passe à l'état 1 ;
4. `la_Pak_` passe à l'état 2.

Le prototype ne déplace aucune de ces opérations, ne remplace pas `bedny`, ne
change pas le porteur de script et n'intercepte pas la condition d'explosion.
L'éventuel affichage moderne vient seulement après la dernière opération.

## Ajout moderne conditionnel

Le fragment
[`PROTOTYPE_ADDITIF_VISUEL.scr.disabled`](PROTOTYPE_ADDITIF_VISUEL.scr.disabled)
documente une variante non compilable en l'état. Elle attend une frame nouvelle
nommée `bedny_crash_modern`, initialement cachée, sans script propre ni rôle
d'objectif. Cette frame doit être un décor statique représentant des caisses
détruites, à la transformation exacte de `bedny`.

La fiche
[`ACTEUR_BEDNY_CRASH_MODERN.plan.disabled`](ACTEUR_BEDNY_CRASH_MODERN.plan.disabled)
définit les contraintes de création. Les modèles commerciaux
`m_L3_bed01crash` et `m_L3_bed02crash` servent de références de silhouette et
d'échelle. Leur présence ne donne pas le droit de redistribuer une extraction.
Un prototype local peut les référencer depuis une installation légalement
possédée ; un paquet distribuable doit employer un asset original ou autrement
redistribuable et documenter sa provenance.

L'ajout est purement visuel : pas de collision, pas de dommage, pas de binding,
pas de changement de navigation. Il est affiché après la destruction release,
et uniquement si le test préalable a démontré l'absence d'épave persistante.

## Protocole de test

### Porte A — release seule

1. Lancer une copie de test inchangée d'Alps3_Obj et capturer `bedny` avant
   pose de l'explosif.
2. Déclencher `w_explosive_02` et capturer à T+0, T+200 ms, T+1 s et T+10 s.
3. Vérifier que le canon, les deux dummies et les objectifs suivent la release.
4. Inspecter visuellement et, si possible, dans l'éditeur l'état courant de
   `bedny` et le modèle rendu après `SetActorState(bedny, 1)`.

Résultat A1 : une épave de caisses persiste. La proposition moderne est
**REFUSÉE** ; la release contient déjà l'état crédible.

Résultat A2 : `bedny` disparaît sans épave, ou son état détruit est visuellement
inexploitable. La porte B peut être ouverte, sans conclure que le fragment
commenté a été restauré.

### Porte B — variante additive isolée

1. Créer `bedny_crash_modern` conformément à la fiche, dans une copie de
   mission distincte et désactivée par défaut.
2. Vérifier qu'il est invisible au chargement, après sauvegarde/chargement et
   pour chaque client multijoueur.
3. Déclencher l'explosion dix fois côté hôte et client : l'ajout doit apparaître
   une fois, après la séquence commerciale, sans clignotement ni doublon.
4. Tester les distances proches et lointaines, les LOD, les ombres, la pluie,
   la collision, le passage de l'IA et la sauvegarde après explosion.
5. Comparer captures et positions avec `bedny` ; aucune translation, rotation
   ou variation d'échelle non documentée n'est admise.
6. Rejouer l'objectif complet : réussite, échec, son, particules, canon et
   progression doivent rester identiques à la release.

Un doublon avec l'état 1, une collision nouvelle, une différence réseau ou une
régression d'objectif invalide immédiatement la variante.

## Retour arrière

Le retour arrière consiste à supprimer de la copie expérimentale :

- la recherche et l'affichage de `bedny_crash_modern` ;
- la frame moderne et son asset redistribuable éventuel.

La ligne commerciale `SetActorState(bedny, 1)` n'est jamais retirée. Aucun
fichier release ne doit avoir besoin d'être restauré, puisque l'essai se fait
dans une copie de mission. Le dossier présent peut lui-même être supprimé sans
effet sur le jeu : il ne contient que documentation et fragments désactivés.

## Statut historique

`bedny_crash_modern` est un nom volontairement nouveau. La proposition n'est
pas un contenu officiel intact, pas une récupération du frame commenté et pas
une preuve que ce frame a existé dans une version publiée. Elle est au mieux
une solution visuelle moderne guidée par un vestige de script et par deux
modèles commerciaux de caisses destructibles.

## Sources internes

- `.analysis/scripts/sabre/Scripts/Alps3_obj/Alps3_delo.scr` ;
- `.analysis/alps3-obj/Missions/Alps3_obj/actors.bin` ;
- `.analysis/alps3-obj/Missions/Alps3_obj/scene2.bin` ;
- `.analysis/alps3-obj/Missions/Alps3_obj/check2.bin` ;
- `.analysis/alps3-obj/Missions/Alps3_obj/mpscripts.dta` ;
- `.analysis/co-libye3-opel/Missions/Co_Libye3/actors.bin` ;
- `.analysis/scripts/sabre/Scripts/Co_Libye3/Objective1.scr` ;
- `.analysis/scripts/sabre/Scripts/Ardens1_obj/Ardens1_delo2.scr` ;
- `.analysis/scripts/sabre/Scripts/Ardens1_obj/Ardens1_delo3.scr`.
