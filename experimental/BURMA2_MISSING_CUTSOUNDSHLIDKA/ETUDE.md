# Étude expérimentale — `CUTSOUNDSHLIDKA.scr` manquant de Burma 2

> Étude préliminaire conservée pour traçabilité. Le dossier canonique corrigé
> est [`BURMA2_CUTSOUNDSHLIDKA_MISSING`](../BURMA2_CUTSOUNDSHLIDKA_MISSING/ETUDE.md).
> Il établit notamment que `l_b2str_4` référence `l_b2str1.wav`, et non le WAV
> homonyme supposé ici, puis bloque toute reconstruction faute de séquençage.

État : étude seule, 14 septembre 2026. Aucun script substitut n'est produit,
aucun son n'est extrait dans le dépôt et aucune archive du jeu n'est modifiée.

## Verdict

La liaison commerciale est réelle et cassée :

```text
l_b2str_4 -> CUTSOUNDSHLIDKA.scr
```

Le porteur sonore `l_b2str_4` existe et référence `SOUNDS/l_b2str1.wav`, mais le
script cible est absent de toutes les couches inventoriées. La cinématique 1,
ses onze plans, ses acteurs et ses dix-sept répliques sont par ailleurs actifs.

Le WAV propre à ce porteur dure **2,955 s** et pourrait tenir avant la première
réplique à 5,0 s. Cela ne suffit pas : les quatre autres porteurs `l_b2str*`
forment deux groupes autour des positions de patrouille avant et après 37 s,
et le nom pluriel du script suggère un séquenceur. La liste des cues, leur ordre
et leurs timecodes restent inconnus. **Ne pas créer de prototype à ce stade.**

## Ce qui est attesté

L'audit du registre effectif trouve 227 bindings et un seul script attaché
manquant dans Burma 2 : celui de `l_b2str_4`. Les autres propriétaires de la
cinématique sont présents :

| Frame | Script | Rôle |
| --- | --- | --- |
| `CUTcamera01` | `CUTSCENE.scr` | caméra et durée globale |
| `CUThlidka1/2/3` | `CUTHLIDKA1/2/3.scr` | patrouille, armes et déplacements |
| `CUTvelitel` | `CUTVELITEL V TABORE.scr` | officier du camp |
| `CUTbackman1/2/3/5/6` | scripts `CUTBACKMAN*` | figurants |
| `CUTDABING` | `CUTDABING.scr` | voix et sous-titres |
| `l_b2str_4` | `CUTSOUNDSHLIDKA.scr` | propriétaire sonore absent |

Aucun autre script commercial extrait ne référence `l_b2str_4`. Aucun fichier
dont le nom associe `CUT`, `SOUND`/`SND` ou `SHLIDKA` ne fournit un équivalent
réutilisable. Dans les autres cinématiques examinées, les sons sont le plus
souvent déclenchés directement par le contrôleur de caméra avec
`FRM_SetOn(frame, true)` ; cette convention explique le mode de lecture
probable, mais pas l'instant prévu ici.

Le nom `SHLIDKA` paraît désigner le son de la patrouille — `hlídka` dans les
noms de travail tchèques/slovaques — mais cette interprétation reste une
inférence. Elle ne permet pas de choisir entre bruit de pas, manipulation
d'arme, ambiance ou autre bruitage, ni d'en déduire un timecode.

## Mesure des WAV voisins

`Sounds.dta` utilise pour ces fichiers le DPCM historique des archives ISD0.
Les cinq WAV ont été décodés uniquement en mémoire avec la table de deltas et
la routine documentées par le projet public
[HD2unpacker](https://github.com/M3tox/HD2unpacker/blob/master/ISDM.cpp#L337-L375).
La taille ci-dessous est la taille WAV décompressée déclarée par l'archive.

| Ressource | Taille | Format | Durée | Fenêtre de signal mesurée |
| --- | ---: | --- | ---: | ---: |
| `l_b2str1.wav` | 130 346 octets | mono, 22 050 Hz, 16 bits | 2,955 s | 0,00–2,95 s |
| `l_b2str2.wav` | 101 804 octets | mono, 22 050 Hz, 16 bits | 2,307 s | 0,10–1,90 s |
| `l_b2str3.wav` | 205 356 octets | mono, 22 050 Hz, 16 bits | 4,656 s | 0,60–4,20 s |
| `l_b2str4.wav` | 256 556 octets | mono, 22 050 Hz, 16 bits | 5,817 s | 0,50–5,30 s |
| `l_b2str5.wav` | 229 422 octets | mono, 22 050 Hz, 16 bits | 5,201 s | 0,00–5,10 s |

La « fenêtre de signal » est un repère d'enveloppe, pas un jugement auditif :
elle ne dit ni le contenu ni le niveau perçu dans le mix du jeu.

## Chronologie active

`CUTSCENE.scr` lance la cinématique après 500 ms et la termine vers 59,4 s.
Les changements de plan surviennent approximativement à 0, 3,9, 7,1, 11,3,
20,2, 32,5, 37,7, 40,8, 45,6, 50,4 et 54,4 s. Une transition fondue occupe
environ 35,7–37,7 s.

`CUTDABING.scr` commence à 5,0 s, puis déclenche ses répliques vers 8, 9, 10,
11,5, 16,5, 21,5, 25,5, 29,5, 31, 37,5, 41,5, 46, 47,5, 50,5, 51,5 et
53,5 s. Ces appels indiquent leur début, pas leur durée de lecture. La marge
avant la première voix est de 5,0 s, suffisante pour `l_b2str1.wav` seul mais
insuffisante pour déduire la séquence plurielle perdue.

## Recherche publique

Les recherches exactes sur `CUTSOUNDSHLIDKA.scr`, `l_b2str_4` et
`l_b2str4.wav` n'ont livré aucune copie indexée. La conversion publique
[had2-cmp, commit `793d979`](https://github.com/ehylla93/had2-cmp/tree/793d979748b27a9924fccc30fa0fba6edb7cd70f)
contient une mission `co_burma2`, mais aucun fichier ni contenu portant ces
noms. Elle ne fournit donc pas le timecode perdu.

[HD2unpacker](https://github.com/M3tox/HD2unpacker) documente la lecture des
archives du jeu et de ses trois familles de démos. Il a permis de valider le
format DPCM et la durée, mais son dépôt ne contient naturellement ni les
archives commerciales ni ce script de mission. Aucun exemplaire public de
démo ou d'archive accessible pendant cet audit n'a fourni la ressource.

## Porte de réouverture

Un prototype ne devient recevable qu'avec au moins l'un des éléments suivants :

1. une copie du script commercial ou un registre de timecodes contemporain ;
2. une autre édition de Burma 2 contenant un propriétaire équivalent ;
3. un test en jeu enregistrant séparément voix, musique et frame sonore, puis
   démontrant une fenêtre de lecture complète sans masquage ni doublage.

Même alors, la maquette devra rester `.disabled`, s'arrêter explicitement dans
`OnCutsceneDone(1)`, respecter le skip et ne jouer chaque cue qu'aux instants
prouvés. Un démarrage de `_4` à 0 s reste seulement plausible ; il ne révèle ni
les autres porteurs pilotés ni la seconde phase après 37 s.

## Sources internes

- registre effectif `missions/burma2/scripts.dta` ;
- scripts Base `CUTSCENE.scr`, `CUTDABING.scr`, `CUTHLIDKA1/2/3.scr` et les
  autres acteurs de la cinématique ;
- `scene2.bin`, `actors.bin` et `sounds.bin` de Burma 2 ;
- `Sounds.dta`, analysé en mémoire sans export persistant.
