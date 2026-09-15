# Étude expérimentale — signaux redondants vers des détecteurs du Tutoriel

État : probablement redondants, 14 septembre 2026. Aucun delta ni prototype.

## Synthèse

| Émetteur | Récepteur | Signal | État du récepteur | Verdict |
| --- | --- | ---: | --- | --- |
| `TUT_TMODE_Controller` | `dummy_WI` | 1 | proximité 3 active | redondant probable |
| `TUT_Instructor6` | `T_dummy_HR_Check` | 1 | proximité 2 active | redondant probable |

Les deux récepteurs sont correctement liés dans `Scripts.dta`. Ils ne possèdent
aucun handler de signal, mais leur unique Whenever de proximité n'est jamais
désactivé à l'initialisation. Ajouter `OnSignal(1)` pour l'armer reproduirait un
état déjà vrai.

## `dummy_WI`

Après avoir lui-même reçu 1, `TUT_TMODE_Controller` adresse 1 à `dummy_WI`,
attend deux secondes puis envoie 16 à `la_bar_20`. Le commentaire attribue son
entrée au premier instructeur, mais aucun émetteur scripté correspondant n'est
conservé ; une liaison de scène reste possible.

`TUT_dummy_WI.scr` surveille immédiatement le joueur à moins de 3 unités. Après
détection il attend deux secondes, envoie 7 à `dummy_dabing` et 4 à
`TUT_Instructor1_aid`, puis désactive sa proximité. Le signal 1 n'est nécessaire
ni au réveil, ni à cette diffusion.

## `T_dummy_HR_Check`

À la fin de la séquence lourde, `TUT_Instructor6` déverrouille `mesh34` puis
envoie 1 à `T_dummy_HR_Check`. Le script lié `T_HR_Check.scr` possède déjà son
Whenever `odzbroj` à 2 unités. Il retire au joueur bazooka, grenades et munitions
de bazooka. Aucune suspension et aucun `SetWhenever(odzbroj,false)` initial ne
sont présents.

Le corps exécute même `SetWhenever(odzbroj,true)` lorsqu'il se déclenche. Cela
peut être une erreur séparée ou un choix pour répéter le nettoyage ; le signal 1
n'en donne pas l'explication. Le transformer en commande de désactivation ou en
nettoyage immédiat serait une invention.

## Interprétation et tests

Le scénario le plus simple est une diffusion uniforme laissée par une version
où ces détecteurs devaient être armés. Dans la version conservée, la proximité
géométrique suffit et rend l'émission inobservable.

Avant tout reclassement, vérifier sans modification :

1. approcher chaque volume avant l'émission amont et confirmer son déclenchement ;
2. entrer directement dans le volume par téléportation/apparition ;
3. sauvegarder/reprendre à l'intérieur et à l'extérieur ;
4. confirmer que `dummy_WI` se désactive après sa première diffusion ;
5. vérifier si `T_HR_Check` répète volontairement le retrait à chaque passage ;
6. tracer les signaux 1 pour exclure une sémantique moteur implicite.

**Décision : aucun handler.** Une source ancienne montrant un état initial
désactivé autoriserait éventuellement un simple `SetWhenever(...,true)`, mais
ce serait une restauration de cette variante, pas de l'état 1.12 actuel.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_TMODE_Controller.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_WI.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_Instructor6.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/T_HR_Check.scr`
- `.analysis/tutorial/base/MISSIONS/TUTORIAL/Scripts.dta`
- `.analysis/signal-graph-current.json` et `.md`

