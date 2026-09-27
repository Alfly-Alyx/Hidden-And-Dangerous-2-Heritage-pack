# Demandes natives de ressources FPV — arguments, pas chargement

**27 septembre 2026.** Deux chemins supplémentaires du client 1.12 sont
exécutés dans l'émulateur privé borné. Ils s'arrêtent **avant** les appels de
chargement de modèles et d'animations. Aucune scène, aucun moteur de rendu,
processus de jeu ou appel système n'est exécuté.

## Nom du modèle de mains

Le chemin `0x492338…0x4923c0` reçoit un objet d'inventaire synthétique et lit
son descripteur, membre `+0x24`. Les routines originales de recherche de
sous-chaîne et de dernier point sont exécutées, pas remplacées par des doubles.

- Objet absent : demande `FPV_hands`.
- Sous-chaîne exacte et sensible à la casse `w_default` : même repli.
- Sinon : retrait du dernier point et de ce qui le suit, ou nom inchangé.
- Une chaîne présente mais vide reste vide. Le contrôle ne lui invente pas
  de repli. `W_DEFAULT.4ds` devient `W_DEFAULT`, pas `FPV_hands`.

Treize cas couvrent les deux références réellement présentes, le repli,
l'absence d'objet, la casse, les points multiples, la limite de 19 octets,
l'encodage CP1252 et la chaîne vide. Les tables contiennent **64/64/75/75**
références aux mains ; les noms distincts sont exécutés une fois chacun.
L'anomalie de classe du slot 270 reste inchangée.

Le contrôle vérifie le nom, l'argument sur la pile, le destinataire de l'appel
et l'intégrité de la source. Il ne démontre pas **quel objet l'inventaire de
l'acteur choisit**, ni que le modèle se charge ou se déforme correctement.

## Noms d'animation réellement chargés depuis les tables

`FpvResourceOracle` prolonge le [parcours natif des tables FPV](PARCOURS_NATIF_FPV.md).
Il consomme les chaînes à compteur de références produites par ce parcours,
et non des pointeurs ou noms de substitution.

1. `0x492e21…0x492e69` cherche un canal positif, renseigné et non vide.
2. Le générateur aléatoire n'est pas exécuté. Les tirages **0, 50 et 100** sont
   fournis explicitement ; `0x492e79…0x492eab` sélectionne le premier seuil
   signé supérieur ou égal au tirage.
3. Avec quatre caches temporairement vides, `0x492ecd…0x492f15` prépare les
   quatre arguments : nom chargé, adresse du cache sélectionné, zéro, zéro.
4. L'émulation s'arrête avant `0x41fc10`. Toutes les cellules sont contrôlées,
   puis le sélecteur et les caches synthétiques sont restaurés, même en échec.

**156 demandes contrôlées** : treize états × trois tirages × quatre cas
(Base, Sabre, fragment moderne 459, table Sabre avec le groupe 459 ajouté).
Le canal zéro de chaque état Benelli couvre les trois tirages avec son seuil
100 ; les treize états demandent les neuf alias commerciaux attendus.

Les cellules vides conservent un témoin propre au laboratoire, qui **n'est pas
une valeur par défaut native**. Une demande dont le choix dépendrait de cette
valeur est refusée. Les tests synthétiques couvrent aussi les autres canaux,
les seuils signés, les égalités et les tirages non couverts.

## Raccordement au laboratoire désactivé

- Outil : `tools/fpv_resource_oracle.py` ; rapport privé
  `.analysis/fpv-resource-arguments-20260927.json`.
- `build_benelli_table_lab.py` vérifie désormais **39 demandes** après le
  chargement de chaque table complète qu'il vient de construire.
- Les exemplaires privés `BenelliTables_Sabre_v4` et `BenelliTables_PatchX01_v4`
  ajoutent les preuves au manifeste ; les quatorze contenus désactivés restent
  identiques à ceux de leurs versions v3.
- Quinze tests synthétiques supplémentaires couvrent les règles, les refus,
  la restauration après erreur et le raccordement au constructeur.

Les noms sont donc transmis jusqu'aux portes des chargeurs. Restent distincts :
résolution I3D/4DS/5DS, liaison effective des joints, skin, poses partielles,
caméra, événements et synchronisation. Aucune de ces obligations n'est retirée
de la liste restante et aucune arme n'est déclarée jouable.

```powershell
.\.venv\Scripts\python.exe tools/fpv_resource_oracle.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/fpv-resource-arguments-nouveau.json'
```
