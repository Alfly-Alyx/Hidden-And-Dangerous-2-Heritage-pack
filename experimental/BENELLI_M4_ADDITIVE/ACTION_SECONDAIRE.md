# Action secondaire — branchements et paramètre caméra

**27 septembre 2026.** Le choix moderne du Benelli, sélecteur 5, type interne 4,
mode 5 et scalaire voisin de 55° en radians, est maintenant relié à des
consommateurs natifs précis. **La visée complète n'est pas exécutée ni validée
en jeu.** Aucun paramètre binaire du laboratoire n'a changé.

## Méthode et résultat

`tools/item_secondary_oracle.py` utilise la même image 1.12 privée verrouillée
que le [contrat natif](CONTRAT_NATIF.md). Chaque phase possède sa propre liste
de blocs autorisés, un budget de 512 instructions et une seconde maximum.
Les appels de gameplay, gestionnaire global, animation, scène et rendu sont
arrêtés **avant leur exécution**. Les objets acteur/caméra et pas de temps sont
explicitement synthétiques. Les routines de lecture des fiches sont celles
déjà contrôlées, dans leur arène bornée distincte.

L'audit `tools/item_secondary_audit.py` compare :

- **182 fiches commerciales** : 44 Base, 44 Patch, 47 Sabre, 47 PatchX01 ;
- le descripteur moderne Benelli v3, inchangé ;
- quatre modes de contrôle **inventés**, 4, 6, 7 et `0xffffffff`, jamais installés ;
- quatre états initiaux d'acteur par fiche, soit **748 arguments de transition** ;
- **48 cas caméra** : huit cibles commerciales, dans les deux sens, avec
  pas nul, pas intermédiaire, dépassement borné et cible déjà atteinte.

Les huit valeurs correspondent approximativement à 17, 18, 20, 25, 48, 50,
55 et 60 degrés après conversion radians → degrés. Cette présentation ne
constitue pas une mesure du champ de vision effectivement rendu à l'écran.

## Circulation des données établie

| Donnée / chemin | Observation bornée |
|---|---|
| Action secondaire, descripteur `+0x4c` | Le test à `0x5458b3` exige une action présente et son type interne `+8 == 4` |
| Mode, action `+0xc` | Depuis l'état acteur 0, le bloc `0x54592a` demande l'état 2 pour le mode 5, l'état 3 sinon |
| État acteur déjà non nul | Pour les états synthétiques 1/2/3, le même bloc demande 0 ; la fonction de transition n'est pas appelée |
| Mode envoyé à l'affichage | `0x49dc9c` transmet le mode à `0x4a8cc0` ; modes 0–3 : branche à deux cadres, 4 : un cadre, 6 : masquage, 5 et hors plage : aucun appel de cadre dans cette fonction |
| Scalaire, action `+0x10` | `0x546d76` / `0x546d87` transmettent `(activation=1, scalaire)` à la fonction FPV `0x492130`, sans l'appeler |
| Paramètre FPV `+0x30` | Le bloc `0x49217e` y conserve le scalaire et prépare l'état d'animation 11 à l'activation, 12 à la désactivation |
| Transition vers la cible | `0x491b63` rapproche la valeur courante de `FPV+0x30` et borne le dépassement ; la constante float32 native vaut environ `0,003141592955` par unité du pas fourni |
| Caméra | Le getter `0x465e80` lit le membre `+0x120` d'une caméra synthétique ; le setter `0x465e50` prépare la nouvelle valeur pour sa méthode de scène `+0x74`, sans l'exécuter |

Le module caméra est identifié statiquement par son initialisation
`CameraModule` et sa table de méthodes. Le rapprochement entre le mode 5 et
une visée simple, et entre les modes 0–3 et les armes à lunette, est cohérent
avec les fiches commerciales contrôlées. Il ne remplace pas une validation
de la caméra, du viseur, des mains ou de leurs transitions réelles.

Le test de désactivation injecte un paramètre fictif pour vérifier le choix de
l'état 12. Il **ne prétend pas** que l'angle de retour provient de la seconde
action : un appelant observé le lit dans le gestionnaire du jeu. Cette source,
les options de caméra et le pas de temps réel restent hors preuve exécutée.
L'absence d'appel de cadre pour le mode 5 dans cette fonction ne garantit pas
l'absence d'autres éléments d'interface à l'écran.

## Raccord au laboratoire

Le constructeur de tables inclut désormais une preuve
`native_secondary_action_arguments` pour le descripteur exact assemblé.
Une preuve incomplète, d'une autre fiche, ou prétendant avoir exécuté le jeu
est refusée. Le manifeste conserve explicitement le travail de visée complète
et de rendu : les vérifications d'arguments ne valent pas validation moteur.

Le laboratoire privé `.analysis/item-table-labs/BenelliTables_Personal_v2`
reprend les quatorze fichiers désactivés de v1, octet pour octet. Il conserve
les dix fiches et six groupes personnels déjà modifiés. Seul le manifeste
ajoute ce contrôle ; les historiques de déploiement v1 restent inchangés.

Les sorties commerciales ou dérivées restent privées et ignorées par Git.
Seuls le code original, les tests synthétiques et cette étude sont publiés.

```powershell
.\.venv\Scripts\python.exe tools/item_secondary_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output .analysis/action-secondaire-nouveau.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_item_secondary_oracle.py
```

## Limites restantes

Les contrôles d'entrée, délais et posture, la fonction complète de changement
d'état, l'animation effective Aim/Daim, le rendu caméra, le tir pendant la
visée, le retour de zoom, les sauvegardes et le réseau restent non qualifiés.
Il ne s'agit donc ni d'une arme jouable annoncée, ni de la fin du projet.
