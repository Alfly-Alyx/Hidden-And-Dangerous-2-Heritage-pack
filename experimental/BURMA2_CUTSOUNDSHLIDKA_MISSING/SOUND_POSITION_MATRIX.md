# Matrice des porteurs sonores `l_b2str*`

Les couples frame/WAV sont lus dans les records successifs de `sounds.bin` ;
ils ne sont pas déduits de la ressemblance des noms.

| Frame sonore | Position monde `(x, y, z)` | WAV sérialisé | Durée | Groupe spatial |
| --- | --- | --- | ---: | --- |
| `l_b2str_` | `(288.783, 3.768, 12.000)` | `l_b2str2.wav` | 2,307 s | isolé / non attribué |
| `l_b2str_5` | `(1.577, 7.145, -25.026)` | `l_b2str3.wav` | 4,656 s | départ patrouille |
| `l_b2str_2` | `(0.514, 6.806, 26.375)` | `l_b2str5.wav` | 5,201 s | seconde phase |
| `l_b2str_3` | `(5.296, 7.695, 24.661)` | `l_b2str4.wav` | 5,817 s | seconde phase |
| `l_b2str_4` | `(-1.398, 6.820, -26.195)` | `l_b2str1.wav` | 2,955 s | départ, propriétaire du script manquant |

## Proximités utiles

- `_4` est à 1,439 m de `CUThlidka1`, 3,766 m de `CUThlidka2` et
  3,574 m de `CUThlidka3` ;
- `_5` est à 1,708 m de `CUThlidka2` et 3,064 m de `CUThlidka1` ;
- `_2` est à 4,506–6,861 m des trois destinations après 37 s ;
- `_3` est à 3,609 m de `dummy_engvtab`, destination du second garde.

Ces proximités attestent deux groupes de spatialisation. Elles ne donnent pas
l'ordre de lecture, car `sounds.bin` décrit des ressources et transforms, pas
la chronologie du script perdu.
