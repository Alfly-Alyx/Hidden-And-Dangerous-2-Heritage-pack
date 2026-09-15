# Arctic 2 — second émetteur du premier poste radio

État : **création d'émetteur bloquée**, 15 septembre 2026. Aucun fichier de
mission, d'installation ou de son n'est modifié.

## Verdict

Le poste `m_radiog_1` est lié à `R_Arc1B_Radio.scr` et son bouton
`m_radiog_1.tlac_hide` au contrôleur d'interaction actif. Les deux scripts
résolvent `S_Radio` comme premier son. Le script du poste déclare explicitement
un `Radio_sound_2` avec un nom vide et `DOPLNIT zvuk`; le bouton dit que le
second son « n'existe pas » et laisse toutes ses bascules commentées.

L'analyse du `sounds.bin` commercial installé apporte la réponse manquante :
`S_radio` est l'unique frame qui utilise l'asset `l_ar2radio`. Aucun partenaire
extérieur n'est sérialisé. Il est donc impossible de « retrouver » un second
émetteur par simple renommage.

## Positions et topologie

| Élément | Position monde `(x, y, z)` | Secteur | Distance au poste 1 |
| --- | --- | --- | ---: |
| `m_radiog_1` | `(16.316, -7.565, 56.466)` | `p1s01` | 0 m |
| `S_radio` | `(16.240, -7.306, 56.508)` | `p1s01` | 0,273 m |
| `m_radiog_` | `(33.308, -7.244, 47.079)` | `p1s84` | 19,415 m |

`S_radio` se trouve à 19,499 m du second poste. Cette distance et les secteurs
différents excluent son emploi comme émetteur partagé.

Le record sonore de `S_radio` atteste : asset `l_ar2radio`, gain brut `1`,
boucle activée et tuple spatial brut `[1, 10, 0.4, 0.4]`. La sémantique exacte
des quatre scalaires doit rester celle du format moteur ; ils ne sont pas
réétiquetés arbitrairement en rayons.

## Précédent Arctic 1/3

Les scripts radio Arctic 1 et 3 pilotent deux frames du même WAV
`l_haydn.wav` :

| Frame | Distance au poste | Secteur | Gain brut | Tuple spatial brut |
| --- | ---: | --- | ---: | --- |
| `l_haydn_` | 0,171 m | `tv5s01` | 1,0 | `[1, 10, 1, 0]` |
| `l_haydn_2` | 1,926 m | `Primary sector` | 0,2 | `[0.1, 3, 1, 0]` |

Le précédent démontre une paire **intérieur/extérieur distinctement placée et
mixée**, pas la possibilité de dupliquer `S_radio` à l'identique. Arctic 2
exige un nouveau record sonore explicitement moderne ou une source historique
retrouvée.

## Contrat futur

[`SECOND_EMITTER_GATE.plan.disabled`](SECOND_EMITTER_GATE.plan.disabled)
interdit toute bascule avant définition du nouveau frame, de son transform, de
ses secteurs et de ses paramètres. Le même asset `l_ar2radio` peut être étudié
car le précédent 1/3 réutilise un WAV commun, mais le gain et le tuple ne doivent
pas être copiés sans test d'occlusion dans la géométrie Arctic 2.

Le bouton devra commander les deux frames dans un seul état `hraje`, et la mort
du poste les couper une fois. La baseline à un son reste le profil par défaut.

## Exclusions

- `m_radiog_` et `R_Arc1B_Radio2.scr` : second poste distinct, déjà réactivé
  par le principal ; ne fournit aucun asset sonore à réutiliser ;
- `R_Arc1B_AlarmButon_.scr` : doublon exact du script déjà lié à `m_alarm_` ;
- `R_Arc1B_DvereOdHajzlu.scr` : remplacé par `R_Arc1B_S9_sender.scr`, qui
  déverrouille la porte et envoie aussi le signal 5 à `Static_9` ;
- `SLEDOVAC.scr` : imprime seulement les valeurs 72/73 ;
- cinq anciens émetteurs de portes : réservés au dossier
  [`ARCTIC2_SEPARATE_BUNKER_DOORS`](../ARCTIC2_SEPARATE_BUNKER_DOORS/ETUDE.md).

## Sources internes

- `Missions.dta`, `MISSIONS/ARCTIC2/sounds.bin` lu sans modification ;
- `.analysis/arctic2-light/base/MISSIONS/ARCTIC2/scene2.bin` ;
- `.analysis/arctic2-light/base/MISSIONS/ARCTIC2/scripts.dta` ;
- scripts Base `R_Arc1B_Radio.scr`, `R_Arc1B_Radio_cudlik.scr` et
  `R_Arc1B_Radio2.scr` ;
- `sounds.bin` et scripts radio Arctic 1/3.
