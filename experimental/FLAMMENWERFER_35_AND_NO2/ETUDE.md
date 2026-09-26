# Flammenwerfer 35 et Flamethrower Portable No. 2

État : **deux reconstructions modernes lourdes**, 15 septembre 2026. Les
ressources commerciales partielles sont des références, pas des armes à
réactiver. Aucun asset n'est recopié et rien n'est compilé.

Contrôle complémentaire du **26 septembre 2026** : le [parseur des tables](../RECONSTRUCTION_BACKLOG/TABLES_EDITEUR.md)
délimite la ligne allemande 44 à **6140–6273** (133 octets, indicateur nul)
et la ligne réemployée 45 à **6273–6406** (`Flak TMP`). Les slots de munition
207/208 sont lus par le parseur natif, sans fenêtres décalées. Les empreintes
et contrôles de l'audit ont été renouvelés, sans toucher aux fichiers du jeu.

## Décision

Les deux identités, leurs icônes et munitions subsistent. L'effet 25
`plamenomet` peut être isolé dans un banc visuel. `flame1.4ds`, 471 octets et un
seul nœud `fire01`, est une amorce d'effet : ce n'est ni un modèle tenu, ni un
modèle posé, ni un réservoir.

Les voix conservées prouvent un contexte narratif autour des lance-flammes,
pas des sons de fonctionnement. Modèles, animations, carburant, jet physique,
dégâts et comportement complet doivent être recréés. Le résultat restera nommé
« reconstruction moderne expérimentale ».

## Chemin borné

1. rejouer le banc désactivé de l'effet 25 sans arme ni dégâts ;
2. créer séparément un mannequin visuel `TEST_FLMWR35` puis `TEST_FLMTHR2` ;
3. ajouter un réservoir et un cycle allumage/jet/extinction sans collision ;
4. tester ensuite un volume de dégâts borné avec occultation par les murs ;
5. seulement après, étudier consommation, rechargement, IA, tiers et réseau.

Les deux armes ne partagent pas automatiquement modèle, capacité ou réglages.
Un socle technique commun est permis comme code moderne, jamais comme preuve
de paramètres historiques identiques.

## Porte de sécurité

Refuser tout prototype qui utilise `flame1.4ds` comme arme complète, attribue
des dégâts au seul effet visuel, confond les voix avec un bruit de jet, traverse
les murs, blesse le tireur sans règle explicite ou diverge entre hôte et client.

Le banc d'effet déjà conservé dans
`experimental/WEAPONS_VEHICLES_TRIAGE/PROTOTYPE_OFFICIEL_EFFECT25.scr.disabled`
reste la première étape ; il n'est pas dupliqué ici.
