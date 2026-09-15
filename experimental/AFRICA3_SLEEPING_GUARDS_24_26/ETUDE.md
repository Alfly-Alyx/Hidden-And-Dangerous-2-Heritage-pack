# Étude expérimentale — sommeil réel des gardes AF3a_24 et AF3a_26

État : **API sommeil non éprouvée, variantes désactivées**, 15 septembre 2026.
L'assise stable d'AF3a_24 reste la baseline et n'est pas modifiée.

## Correction de l'inventaire

La vérification directe de `missions.dta` donne deux résultats différents :

- `some_bed`, référencé par AF3a_24, est absent ;
- `m_postel_a7`, référencé par AF3a_26, est présent exactement dans
  `MISSIONS/AFRICA3/scene2.bin`.

Le second lit n'est donc pas à recréer d'office. Sa présence ne prouve toutefois
ni un point d'activité sommeil valide, ni l'alignement d'AF3a_26. L'API
`HUMAN_ACTIVITY_Sleep` ne possède aucun appel actif dans le corpus Base/Patch.

## Baseline protégée

Le lot stable restaure seulement AF3a_24 assis : `dummy_24_sit`, le déplacement
de retour `AF3a_24_sit` et les deux appels `HUMAN_ACTIVITY_Sit(sit)`. Cette
branche est complète, attestée par des usages actifs de `Sit` et réversible.

Le profil sommeil AF3a_24 est **alternatif**, jamais superposé : il part d'une
copie expérimentale et désactive seulement les deux activités assises dans cette
copie. Il ne change pas l'installateur stable, les alarmes, le détecteur de mort
ou la conversation des autres acteurs.

## Deux essais séparés

### AF3a_24 — lit moderne requis

Créer `bed_af3a24_sleep_modern` dans la maison proche de l'entrée principale,
avec transform, pivot et provenance documentés. Le nom `some_bed` est un
placeholder, pas une position historique. Le lit peut réutiliser un asset
redistribuable ou référencer localement un modèle commercial, mais son placement
reste **CRÉATION MODERNE**.

### AF3a_26 — lit commercial à valider

Tester `m_postel_a7` en éditeur : position relative à AF3a_26, orientation,
collision, place disponible et compatibilité avec l'activité. Aucun clone n'est
nécessaire si le frame est utilisable. S'il ne l'est pas, une ancre moderne
distincte doit être créée sans renommer le lit commercial.

[`PROTOTYPES_SLEEP_WAKE.scr.disabled`](PROTOTYPES_SLEEP_WAKE.scr.disabled)
documente les points d'insertion et les réveils. Un seul acteur est testé à la
fois.

## Réveil propre

Les `OnAlarm()` commerciaux commencent déjà par effacer l'animation, arrêter
l'humain et le remettre debout/réactif. Ils restent autoritaires. La variante
ajoute le même triplet minimal `HUMAN_Stop`, station debout, suspension levée
aux activations de proximité/signal susceptibles de réveiller sans passer par
`OnAlarm()`.

Aucun appel « Sleep off » n'est inventé : seule la signature commentée
`HUMAN_ACTIVITY_Sleep(bed)` est attestée. Si `HUMAN_Stop()` et le changement de
mode ne détachent pas immédiatement l'acteur, l'API est rejetée.

Après une alarme, AF3a_24 reste sur le chemin assis dans le profil stable. Dans
son profil sommeil séparé, il ne se recouche pas automatiquement avant preuve
d'une reprise sûre. AF3a_26 conserve son retour accroupi commercial.

## Tests

1. Baseline stable : assise initiale et retour assis AF3a_24, toutes alarmes.
2. Vérifier chaque lit/ancre en éditeur, sans collision ni téléportation.
3. Charger l'essai d'un seul garde. Tout symbole refusé bloque le profil.
4. Réveiller par proximité, alarme, blessure, signal 20, friendly fire et mort ;
   mesurer délai, détachement, arme, posture et reprise de route.
5. Sauvegarder/reprendre pendant le sommeil, pendant le réveil et après alarme.
6. Tester AF3a_24 sans activité assise uniquement dans sa copie sommeil, puis
   rétablir le profil stable et comparer exactement.

Critères d'arrêt : acteur attaché au lit, alarme retardée, réveil sans arme,
collision, duplication, téléport visible ou altération de la branche assise.

## Retour arrière

Supprimer l'ancre moderne éventuelle et restaurer les scripts Patch. Pour
AF3a_24, réactiver la variante assise stable inchangée. Aucun binding ou acteur
commercial n'est remplacé.

## Sources internes

- scripts Base/Patch `AFRICA3/AF3a_24.scr`, `AF3a_26.scr` ;
- `missions.dta : MISSIONS/AFRICA3/scene2.bin`, `check2.bin`, `actors.bin`,
  `scripts.dta` ;
- `installer/Africa3Guard24SittingInstaller.cs` consulté comme baseline, non
  modifié ;
- `experimental/AFRICA3_SLEEP_AND_STATIC_WEAPON/`.
