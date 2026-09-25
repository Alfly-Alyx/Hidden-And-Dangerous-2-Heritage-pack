# Sicily 1 — deux comportements de portes pour IT_40

État : **prototype reproductible désactivé**, 25 septembre 2026.

## Preuves

`SabreSquadron.dta` fournit le registre `missions/sicily1/scripts.dta` et
`scripts/sicily1/sic1_it_40.scr`. Le propriétaire unique `IT_40` est sérialisé
dans `actors.bin`, à `(-17.461864, 6.243365, 7.522636)`.

Au premier `OnAlarm`, le script arme `FirstAlarm`, joue l'animation, attend
2700 ms, envoie le signal 2 à IT_49/50/51, déverrouille `d_dvere_10` et
`d_dvere_09`, puis transmet l'alarme globale. Deux appels commentés
`SetActorState(..., 1)` se trouvent juste après les déverrouillages.

Les deux portes sont présentes dans `scene.4ds` et `scene2.bin`. Attention :
elles ne sont pas des frames humaines du champ `0x10` dans `actors.bin`; un
audit limité à ce champ les manquerait. Dans `scene.4ds`, leurs noms commencent
aux offsets 1838986 et 1838921; les références existent aussi dans les
enregistrements de scène. Le générateur vérifie les empreintes complètes des
deux fichiers et leurs chaînes terminées par zéro, sans prétendre simuler les
articulations ni le sens d'ouverture.

## Deux profils

- `commercial` : déverrouillage seulement, comportement par défaut.
- `sicily1-it40-open-doors` : réactivation des deux appels historiques, sans
  changer `FirstAlarm`, les signaux, les délais ni la logique de combat.

Le code commenté est **OFFICIEL**. Le résultat attendu « ouvrir immédiatement
les deux portes » reste à observer en moteur. Le choix se fait sur une seule
copie du script avant chargement, pas sur deux propriétaires concurrents.

Le [catalogue](../reconstruction-variants.json) fixe cinq empreintes et deux
modifications. La [procédure commune](../RECONSTRUCTION_BACKLOG/VARIANTES_REPRODUCTIBLES.md)
produit une copie désactivée de 2464 octets; son diff a été vérifié.

## Tests et retrait

Comparer portes fermées, déjà ouvertes, occupées par un soldat et actionnées par
le joueur. Répéter l'alarme et vérifier un seul signal vers les renforts et le
contrôleur global. Tester mort de IT_40 avant/après les 2700 ms et
sauvegarde/reprise aux mêmes frontières. Contrôler collisions, animation,
navigation des renforts et progression vers la sortie du souterrain.

Le commentaire commercial avertit que le verrouillage n'est pas supporté en
coopération : cette variante vise **Sicily1 solo uniquement**. Elle ne doit pas
être copiée dans Co_Sicily1 sans étude séparée. Retrait : copie commerciale et
nouvelle partie laboratoire. Aucune modification de la mission installée.
