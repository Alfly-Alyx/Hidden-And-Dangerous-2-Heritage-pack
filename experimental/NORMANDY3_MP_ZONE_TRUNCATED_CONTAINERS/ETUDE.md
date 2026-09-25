# Normandy 3 Zone — conteneurs incomplets et hypothèse de fusion

État : comparaison reproductible en lecture seule, fusion automatique refusée,
25 septembre 2026. Aucun binaire commercial n'est ajouté à Git ou installé.

## Résultat mesuré

Les trois conteneurs propres à `NORMANDY3_MP_ZONE` dans `missions.dta` déclarent
des longueurs supérieures aux données stockées. Les conteneurs complets de
`NORMANDY3_MP` ont des longueurs et des contenus différents : même en ignorant
les six octets d'en-tête extérieur, aucun fragment Zone n'est un préfixe exact
de sa référence MP.

| Fichier | Zone stocké | Zone déclaré | MP complet | Première différence après l'en-tête |
|---|---:|---:|---:|---:|
| `actors.bin` | 3768 | 21970 | 22628 | offset 8 |
| `scene2.bin` | 2814 | 6309393 | 6272077 | offset 128 |
| `sounds.bin` | 70 | 8603 | 8735 | offset 8 |

Les offsets sont indexés depuis zéro. Certains écarts se trouvent eux-mêmes
dans des longueurs de sous-conteneurs : ils ne constituent pas, à eux seuls,
une preuve de déplacement d'acteur. En revanche, ils invalident le raccourci
« ajouter simplement la fin du fichier MP ». La scène Zone déclare même une
taille supérieure au fichier MP complet disponible.

Le parseur de blocs refuse la structure complète des trois fragments et accepte
les trois références MP. Des noms détectables dans un fragment abîmé ne sont
pas autant d'acteurs complets importables : chaque record doit d'abord être
validé dans sa hiérarchie, avec limites et champs entiers.

## Vérification automatisée

[`prototype_deployment_audit.py`](../../tools/prototype_deployment_audit.py)
consigne maintenant pour chaque paire : tailles stockées/déclarées, égalité du
type, première différence du préfixe après l'en-tête et validité structurelle.
La fonction `prefix_comparison` n'émet aucun fichier et conserve toujours
`automatic_splice_authorized: false`, même pour un préfixe qui correspondrait.
Une correspondance binaire seule ne prouverait ni l'intention historique ni le
chargement en jeu.

Les six SHA-256 sont déjà épinglés dans
`NORMANDY_CONTAINER_SIGNATURES`; ils ont été vérifiés de nouveau. Cinq tests sur
fixtures inventées couvrent identité complète, vraie coupure de fin, longueur
différente avec préfixe identique, octet divergent, fragment trop long et en-tête
trop court. Le plan des archives commerciales réussit sans modifier l'installation.

## Correction du nombre de compléments

La fiche solo mentionnait encore **cinq** bases. Le plan de prototype actuel en
exige **huit** : `map.4ds`, `tree.klz`, `scene.4ds`, `loader.4ds`, `volumy.bin`,
puis les trois conteneurs ci-dessus. Le dossier Zone possède treize fichiers,
dont quatre marqueurs minuscules et trois conteneurs dégradés. Six fichiers
propres sont conservés; les huit références MP forment le complément du plan
à quatorze fichiers.

Ce remplacement intégral est déjà la stratégie du prototype existant. Il reste
un **repli de reconstruction**, pas une récupération fidèle de la carte Zone
perdue, et ne crée aucun scénario solo. Ne pas dupliquer ce plan sous un nouveau
nom en le présentant comme une autre mission restaurée.

## Étape restante pour une fusion fidèle

Isoler les seuls records Zone entièrement délimités, rechercher leurs identités
dans le MP complet puis comparer transform, parent, item, collisions et relations.
Tout record partiel, doublon ou différence sans résolution reste une preuve
archivée, pas un remplacement activable. Une fusion par records serait une
nouvelle reconstruction moderne, avec sa propre baseline et ses essais.

La [fiche de wrapper solo](../MP_ONLY_TO_SOLO_MATRIX/NORMANDY3_MP_ZONE/FICHE.md)
conserve sa barrière : collision/volumes et chargement du prototype d'abord;
point de départ, contrôleur, objectifs et fin solo seulement ensuite. Aucun
résultat moteur ni statut de conversion validée n'est ajouté.
