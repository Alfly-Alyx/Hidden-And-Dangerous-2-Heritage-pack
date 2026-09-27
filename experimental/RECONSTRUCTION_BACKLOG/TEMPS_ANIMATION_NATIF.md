# Durée et progression natives des huit pistes

**27 septembre 2026.** Le contrôleur temporel est examiné indépendamment
du [calcul de canaux](CALCUL_ANIMATION_NATIF.md), de la
[sélection des cibles](LIAISON_ANIMATION_NATIVE.md) et des
[poses partielles](POSES_PARTIELLES_NATIVES.md).

## Exécution bornée

Le banc émule `0x10020150…0x10020256` dans la même `LS3DF.dll` épinglée.
Son contrôleur inventé possède huit pistes et **zéro objet cible** : les
chemins d'application de pose et de callback sont exclus de la liste
d'instructions permises. Aucune scène, allocation, entrée DLL ou API Windows.

La méthode de durée `0x10004e80`, appelée via la table native `0x1009b400`,
lit le dernier repère 16 bits de l'en-tête fourni et renvoie **repère × 40**.
Les en-têtes sont inventés. Les données de clips sont en lecture seule ;
seuls le drapeau de mise à jour et les champs temporels/activité autorisés
du contrôleur peuvent être écrits. Budget de 4 096 instructions et une seconde.

Les entrées bornées comportent : activité booléenne, modes bruts 0 à 3,
repère terminal 1 à 65 535, temps/pas/états antérieurs signés dans ±2²⁷.
Les additions sortant de ce domaine sont refusées. Ce sont les bornes du
banc, pas une affirmation sur les capacités maximales du moteur.

## Comportement établi

- Un pas non nul marque le contrôleur à recalculer. Pour chaque piste active,
  il ajoute ce pas au temps courant et l'enregistre comme dernier pas.
  Une piste inactive conserve tous ces champs.
- Pas nul et contrôleur propre : aucune actualisation, même si un temps se
  trouve déjà hors limites. Pas nul et contrôleur marqué : les limites sont
  traitées, sans remplacer le dernier pas mémorisé.
- Lors du traitement, le champ de temps précédent reçoit le temps courant
  **avant** correction éventuelle de boucle.
- Le domaine normal est `0 <= temps < durée` : l'égalité avec la durée est
  déjà une fin de lecture pour ce contrôleur.
- Le **mode brut 2** conserve l'activité et ajoute une durée si le temps est
  négatif, ou en retranche une si le temps atteint/dépasse la durée.
  **Une seule correction est faite par mise à jour, pas un modulo.** Un saut
  de plusieurs durées peut donc laisser le temps hors domaine.
- Les modes bruts 0, 1 et 3 désactivent la piste hors domaine, mais ne ramènent
  pas son temps à zéro ou à la dernière clé. Aucun nom d'énumération historique
  supplémentaire n'est inventé pour ces trois valeurs.

La fonction réelle place l'application des poses avant son traitement de fin
de lecture. Le banc n'exécute pas cette application puisqu'il n'a aucune cible.
Cette observation de l'ordre ne remplace pas une validation des événements
ou des transitions visuelles en jeu.

## Corpus et portée

`ls3d-native-time-20260927.json` : **774 cas**, dont **677 traitements effectifs**
et **2 837 désactivations de pistes** sur les cas concernés. Temps nuls,
négatifs, aux frontières et dépassant plusieurs durées ; repères terminaux
1, 10, 146 et 65 535 ; pistes actives/inactives et modes indépendants.
Chaque état natif correspond exactement à la référence indépendante.

Douze tests synthétiques supplémentaires couvrent ces règles, la préservation
des données, les refus d'entrée et l'interdiction des appels de pose/callback.
Ils ne lisent aucune bibliothèque commerciale.

## Unités et raccordement au client : encore partiels

La table de méthodes de modèle `0x1009ba50` place le relais `0x10034ba0`
à l'offset `0x20`. Ce relais transmet le pas au contrôleur. Le client épinglé
appelle cet offset depuis `0x491fba` ; son entier provient de l'argument de
`0x491e90`, lui-même transmis par `0x69b500` à `0x69babd`.
Ce parcours est observé statiquement, pas exécuté par le banc.

Le point d'origine horloge/conversion n'est pas encore qualifié : **ni
millisecondes, ni secondes, ni 25 images/seconde ne sont revendiquées**.
Les choix de vitesse, pauses, modes hérités, création/retrait de pistes et
callbacks restent des contrats distincts. Aucun indicateur de jouabilité
ou de validation moteur n'est promu.

```powershell
.\.venv\Scripts\python.exe tools/ls3d_time_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/temps-natif-nouveau.json'
```

Rapport neuf obligatoire ; aucun jeu lancé ou modifié.
