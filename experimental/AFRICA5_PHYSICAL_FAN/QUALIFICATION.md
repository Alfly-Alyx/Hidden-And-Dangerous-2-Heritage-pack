# Africa 5 — ventilateur physique : paire native reproductible

26 septembre 2026. **MODERNE, désactivé, validation moteur en attente.**

Les profils `africa5-fan-onuse-oneshot` et `africa5-fan-proximity-oneshot`
reconstruisent chacun le script Patch à partir de la copie sous licence. Ils
sont exclusifs, conservent la rotation Y 108000/360 et le délai de 8000 du premier
ventilateur et ne modifient jamais `AF4_vetrak02.scr`, sa rotation 90 ou son binding.
Le profil d'utilisation est un choix moderne ; le profil de proximité conserve
le rayon dormant de trois unités avec un verrou moderne à usage unique.

## Propriété du modèle vérifiée, physique non vérifiée

Le contrôle ne se contente plus de trouver des noms dans plusieurs fichiers :
il décode le record 0x4010, son type modèle 9 et sa référence 0x2012, puis le nœud
typé du fichier 4DS effectivement prioritaire. Toute ambiguïté, substitution
locale différente, modèle masqué par un Patch ou sous-hiérarchie non examinée
est refusée. Le modèle est lu et épinglé, jamais inclus dans le dépôt ou le delta.

| Preuve | Valeur |
| --- | --- |
| Instance de scène | `m_AF5_vetrak`, record 5056846 de `scene2.bin` |
| Ressource référencée | `models.dta::models/m_af5_vetrak01.4ds`, 8201 octets |
| SHA-256 du modèle | `6f59be2dfa737efed850c1e16494f9288dc33b4519df9305622c882692665a63` |
| Propriétaire exact lié | `m_AF5_vetrak.Rectangle07` → `AF4_vetrak.scr` |
| Nœud | index 2, parent 0, visuel simple, aucun enfant rattaché |
| Géométrie | 126 sommets, 42 triangles, un niveau de détail, matériau 2 |
| Bornes locales du maillage | min (-0.727101, -0.018956, -0.465256), max (0.728552, 0.010675, 0.796633) |
| Position locale du nœud | (-0.000026, -0.009770, -0.000925), échelle (1,1,1) |
| Position monde de l'instance | (64.373993, 11.024630, 90.641525) |

`Rectangle05` et les quatre dummies sont des racines séparées, pas des enfants
de `Rectangle07`. Leur présence ne prouve **aucun volume de collision**. Les
transformations sont enregistrées telles que sérialisées ; aucune position monde
du nœud ni convention commune de quaternion scène/modèle n'est supposée.

## Delta et interruption

Deux ancres uniques seulement : déclarer le verrou et remplacer le bloc dormant.
Le verrou est posé **avant** `FRM_CreatePhysicalObject(this, 5)`, puis le script
se termine. La proximité désarme en plus son `Whenever` avant la conversion.
L'utilisation vérifie elle aussi le rayon de trois unités. Les autres octets du
script sont conservés, y compris les fins de ligne.

| Paire | Script témoin | Script variante | SHA-256 variante |
| --- | --- | --- | --- |
| Utilisation | 475 octets | 672 octets | `350451208bbded8f8dd07264566e9c68ffb124f667a4e8f03995760b1901a1ee` |
| Proximité | 475 octets | 753 octets | `8dc268caf2b2096f648f727782120d34e5af94329de6d0b8cce97dd0cb7b6149` |

La présence d'un handler ne prouve ni qu'`OnUse` sera proposé au joueur sur ce
frame, ni que la rotation en cours est annulée par la conversion. Ces deux points
font partie des essais, sans ajout d'API moteur supposée.

## Essais obligatoires

Le registre et les étapes détaillées sont dans `validation/reconstruction-runtime.json`.
Commencer par le témoin Africa 5 : son ancien `af4_runway01_detector.scr` manque
dans les archives commerciales. L'outil conserve cette absence exacte et interdit
la variante tant que le fonctionnement du témoin n'a pas été attesté. Il ne crée
pas un faux détecteur et ne supprime pas son binding.

Après ce préalable : vérifier pivot, collision, plafond, chute/rebonds, contacts,
tirs/grenade, spam d'utilisation, séjour prolongé dans le rayon, sauvegarde/reprise,
navigation, objectifs et retour au témoin. Arrêter l'essai si une autre géométrie
est entraînée, si la conversion se répète ou si les dégâts deviennent imprévisibles.
Le jumeau doit tourner sans aucune différence pendant toute la comparaison.

Les anciens fichiers `PROTOTYPE_*.disabled` restent des esquisses historiques ;
seules les recettes épinglées constituent les profils reproductibles actuels.
