# Remplacements de clips pendant une lecture native persistante

**27 septembre 2026.** Attachement, réglage des poids, progression du temps et
calcul des poses s'enchaînent désormais dans **une même mémoire native**. Ce
raccordement ne charge pas une scène et ne rend pas les armes jouables.

## Ce qui s'exécute

`ls3d_animation_stream_oracle.py` réutilise les chemins épinglés de
`SetAnimation` (`0x100342f0`), du contrôleur (`0x10020150`) et des poses, et
exécute `SetWeight` (`0x10034460..0x100344dd`). Après une préparation vide,
les transformations de repos sont fournies **une seule fois**. Le même
contrôleur, ses huit pistes, les cibles et leurs transformations subsistent
pendant tous les changements de clip et les avancées de temps.

- Un autre clip peut être attaché pendant qu'une piste conserve son temps.
- Un même clip peut être redémarré après une lecture ou une fin non bouclée.
- Les poids sont modifiés par le code natif, avec ses bornes 0 et 1.
- Le retrait exécute réellement le nettoyage des descripteurs et des références.
- Une cible sans canal actif conserve sa dernière pose ; elle n'est pas
  artificiellement remise au repos entre deux étapes.

Chaque opération contrôle tous les descripteurs, références, temps, états,
allocations/libérations et drapeaux de cibles contre une référence indépendante.
Les transformations sont lues dans la mémoire native, et toute modification
hors des zones attendues est refusée. Les noms et corps de clips sont immuables.
Les instructions autorisées excluent événements, callbacks, poses supplémentaires,
chargeurs, système d'exploitation et rendu. Allocation de cibles bornée par des
doubles ; limite de 512 opérations et 128 cibles par scénario.

## Résultats privés

Rapport : `.analysis/animation-stream-native-20260927.json`.

Les **24 scénarios synthétiques** couvrent les huit pistes, quatre modes,
deux types de conteneurs, noms manquants et dupliqués, bornes de poids,
arrêt/reprise et libération/recréation des cibles : **512 opérations**,
192 avancées, 208 calculs de pose, écart nul.

Les quatre banques F35/No. 2 × deux modèles de mains passent chacune dans
l'ordre des neuf clips puis en sens inverse : **8 scénarios**, **1 152 opérations**,
**352 avancées**, **25 456 calculs de pose**, 73 616 canaux écrits. Les 592
structures de cible créées sont toutes libérées à la fin de ces scénarios.
Écart maximal observé : **zéro**. Les 36 empreintes de clips correspondent aux
fichiers privés désactivés de `F35_FlatFPV_Motion_v2`/`F2_FlatFPV_Motion_v2`.

Douze tests synthétiques supplémentaires protègent ces transitions de référence,
les refus et les limites. La référence d'attachement existante est extraite en
une étape réutilisable pour conserver les horloges ; ses quinze tests antérieurs
restent inchangés. Les anciens contrôles natifs sont également rejoués :
304 opérations d'attachement et 22 séquences de lecture (168 avancées,
144 calculs de pose), écart nul. Suite locale : 977 réussites sur 978 ; copie
de publication : 973 sur 974, chacune avec un test de lien symbolique non
exécuté. La copie utilise les dépendances privées déjà présentes dans
`.research/binary-patch-deps`, exposées au processus de test par `PYTHONPATH`.

## Séparation explicite des preuves

Le [banc de décision client](SELECTION_PISTE_FPV.md#décision-amont-et-copie-de-la-piste-précédente)
vérifie séparément le choix immédiat/mélangé et la copie de la piste précédente.
Ici, le calendrier des poids est un **scénario de diagnostic explicite**, pas
celui calculé par le client dans la même instance. La lecture native des fichiers
5DS reste également séparée : ce banc prépare ses propres corps relocalisés.

Les poses de squelette sont privées ; le rapport n'exporte pas leur géométrie.
Ni contact des doigts, continuité des poignets pendant les mélanges, caméra,
skin, rendu, événements, sons ou mécanismes d'arme ne sont qualifiés ici. Le
chargement/copie du modèle et l'intégration réelle restent à traiter. Aucun jeu,
installateur, archive commerciale ou table active n'est modifié ou lancé.

```powershell
.\.venv\Scripts\python.exe tools/animation_stream_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/animation-stream-nouveau.json'
```
