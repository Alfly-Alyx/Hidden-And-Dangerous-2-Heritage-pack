# Africa4 oasis legacy — éléments à recréer ou spéculatifs

État au 14 septembre 2026. Aucun des éléments ci-dessous n'est créé dans ce
lot ; la liste fixe seulement leur statut avant une future maquette.

| Élément futur | Nécessité | Preuve disponible | Statut |
| --- | --- | --- | --- |
| caméra legacy 01 | éviter le binding release sur `camera_cut01` | transformation de `camera_cut01` présente | copie moderne dérivée |
| caméra legacy 02 | deuxième plan actif | nom `camera_cut02`, durée ~2 s | transformation et animation spéculatives |
| caméra legacy 03 | troisième plan actif | nom `camera_cut03`, durée ~2 s | transformation et animation spéculatives |
| caméra legacy 04 | ancienne cinématique 2 | nom présent dans le script | optionnelle ; plan entier spéculatif |
| caméra de regard | bloc de glissement commenté | trois points de regard encore présents | optionnelle ; trajectoire spéculative |
| contrôleur legacy | démarrage exclusif | aucun porteur libre conservé | moderne, nouvel acteur |
| identifiant de cutscene | isoler la release 1 | aucun numéro legacy sûr attesté | moderne, réservé après audit global |
| choix de menu/préchargement | sélectionner une seule intro | aucune option commerciale conservée | moderne |
| mapping des quatre joueurs | remplacer les assignations incomplètes | quatre Spawnsingle et huit scripts orphelins | moderne/reconstruit |
| fusion d'`AF3b_01` | conserver l'IA et ajouter geste/dialogue visuel | acteur actuel occupé | moderne, sans remplacement fonctionnel |
| règle Tiger/Opel | état visible pendant/après l'intro | frames présentes, masquage Tiger commenté | spéculative |
| sous-titre `08011601` | texte de l'intro | identifiant attesté | commercial, contenu à vérifier par langue |
| checkpoint `AF3b_pl04_01` | destination du joueur 04 en scène 2 | nom attesté dans l'inventaire | commercial, accessibilité à tester |
| caméra `camera_legacy_cut04_modern` | remplacer la caméra 04 perdue sans toucher à la scène 1 | seul le nom historique `camera_cut04` subsiste | moderne ; transformation, FOV et durée à créer |
| fusion joueur 04 pour scène 2 | conserver le handler après la scène 1 | réactions commentées mais script orphelin | reconstruite ; cycle EndScript à prouver |

Toute caméra ou animation nouvellement dessinée portera l'étiquette `MODERNE`.
La présence d'un nom dans un script ne prouve ni sa transformation, ni son
champ de vision, ni son mouvement.

La caméra moderne de la scène 2 ne doit jamais reprendre le nom
`camera_cut04` comme si sa transformation historique était connue. Elle reste
réservée à l’entrée legacy et ne remplace ni `camera_cut01`, ni le contrôleur
commercial de la cinématique 1.
