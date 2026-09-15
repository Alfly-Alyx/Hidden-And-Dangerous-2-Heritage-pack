# Matrice — basse priorité Alps 2

| Profil | Ligne | Ressource attestée | Défaut | Promotion |
| --- | --- | --- | --- | --- |
| `AL2_05_TELEPORT_TEST` | téléport 03 -> 04 | deux endpoints utilisés activement | OFF | seulement si blocage reproductible |
| `AL2_07_WALK_TEST` | setter Walk initial | API + ronde actives | OFF | comparaison de rythme |
| `AL2_22_TURN_CUML_TEST` | tour vers `cuml` | `cumzadl` résolu et actif | OFF | normal/Carnage séparés |
| `AL2_22_TURN_STORE_TEST` | tour vers le point du stock | frame résolue et active | OFF | normal/Carnage séparés |
| `AL2_40_SEATED_ANIM_TEST` | `%%sedimtak` après Sit | siège local + animation globale | OFF | résolution runtime Alps 2 |

`DEFAULT=RELEASE` : les cinq profils restent OFF. Ils sont mutuellement
indépendants et ne doivent pas être regroupés sous une option générique.
