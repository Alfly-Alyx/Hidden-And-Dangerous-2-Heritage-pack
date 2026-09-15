# Arctic 2 — étude des anciennes portes de bunker indépendantes

État : **reconstruction bloquée, aucun script activable**, 14 septembre 2026.
La mission commerciale reste la référence et aucun ancien émetteur n'est remis
en service isolément.

## Verdict

Les couples `m_d_po10`/`m_d_po11` et `m_d_po12`/`m_d_po13` conservent une
ancienne logique complète de combinaison de lightmaps. Ils ne conservent pas
la séparation physique qui donnait un sens à cette logique : les commentaires
commerciaux indiquent que les deux portes ont été jointes afin de fermer les
portails. Un mode LEGACY indépendant ne doit donc pas être produit avant
d'avoir identifié ou recréé deux géométries de portail, leurs propriétaires et
leurs collisions.

Les couples `m_d_po01`/`m_d_po02` et `m_d_po26`/`m_d_po27` sont encore moins
complets. Leurs anciens émetteurs existent, mais les contrôleurs courants ne
portent pas un protocole indépendant symétrique. Les réactiver seuls doublerait
ou détournerait le basculement groupé de la release.

## Inventaire attesté

L'audit du registre Sabre trouve 172 liaisons, 143 scripts et six scripts
orphelins directement concernés :

| Script orphelin | Signal envoyé | Destinataire | État du protocole actuel |
| --- | ---: | --- | --- |
| `1s_m_d_po02.scr` | 1 | `p1s01` | bascule déjà `po01` et `po02` ensemble |
| `1s_m_d_po11.scr` | 2 | `p1s59` | ancien handler indépendant commenté |
| `1s_m_d_po13.scr` | 2 | `p1s40` | ancien handler indépendant commenté |
| `1s_m_d_po26.scr` | 2 | `p1s97` | aucun handler 2 conservé |
| `1s_d_po01.scr` | protocole ancien | `p1s01` | remplacé par `1s_d_po09.scr` enrichi |
| `R_Arc1B_DvereOdHajzlu.scr` | aucun | lui-même | simple déverrouillage au premier usage |

Les frames `m_d_po01`, `02`, `09`, `10`, `11`, `12`, `13`, `26`, `27`,
`m_d_po02a`, `m_dv_m01`, `p1s01`, `p1s40`, `p1s59`, `p1s97` et `Static_4`
sont présentes dans les données de scène. Cette présence ne prouve ni deux
portails indépendants ni un propriétaire par battant.

## Ce que montrent les contrôleurs

### Couples 10/11 et 12/13

Le signal 1 de `p1s59` applique le même état aux portes 10 et 11 et choisit la
lightmap de groupe 0 ou 3. Son ancien signal 2, commenté, retardait la porte 11
de 800 ms puis recalculait les quatre états 0, 1, 2 et 3. Le commentaire source
dit en substance : « c'était pour deux portes, mais elles sont maintenant
jointes et ferment les portails ».

`p1s40` possède la même structure pour les portes 12 et 13. Les émetteurs
release des portes 10 et 12 mettent en outre les **deux** battants en lightmap 5
pendant l'usage. Un futur mode indépendant devra remplacer cette phase, pas
seulement décommenter le signal 2.

### Couples 01/02 et 26/27

Le signal 1 de `p1s01` bascule ensemble `m_d_po01` et `m_d_po02`. L'ancien
émetteur de `po02` envoie justement ce même signal : il reproduirait le
basculement du couple au lieu de rendre `po02` indépendant. Le script actif de
`m_d_po01` participe aussi à `Static_4` ; le substituer par l'ancien
`1s_d_po01.scr` perdrait ce raccord.

Le contrôleur `p1s97` ne possède que le signal 1, qui bascule ensemble les
portes 26 et 27. Aucun ancien handler de signal 2 n'est conservé. Ici, le
simple émetteur `po26` ne suffit même pas à reconstituer le récepteur.

`1s_d_po09.scr`, actif, est une version enrichie : déverrouillage, acteur
`m_d_po02a`, lightmaps, signal 2 de `p1s01`, `m_dv_m01` et `Static_4`. L'ancien
`1s_d_po01.scr` simplifié n'est donc pas un remplaçant sûr.

## Contrat d'une future variante

Nom proposé : `Arctic 2 [Reconstruction — portes séparées]`.

Cette entrée additive devrait :

1. cloner la mission, sans remplacer Arctic2 ;
2. fournir deux géométries et deux portails réellement distincts par couple ;
3. attribuer un propriétaire, une collision et un état de sauvegarde à chaque
   battant ;
4. reprendre les tables de combinaison 0/1/2/3 attestées pour 10/11 et 12/13 ;
5. créer et étiqueter `MODERNE` les protocoles manquants de 01/02 et 26/27 ;
6. conserver les raccords enrichis de `1s_d_po09.scr` ;
7. rendre chaque émission monostable pendant l'animation.

## Porte de preuve et tests

Aucun `.scr.disabled` n'est fourni tant que les portails ne sont pas séparés.
La première maquette devra vérifier, pour chaque battant : ouverture seule,
fermeture seule, quatre combinaisons, collision joueur/IA, occlusion, fermeture
de portail, répétition rapide, deux usages simultanés et sauvegarde/reprise.
La variante est rejetée si une porte invisible bloque encore, si un portail
reste ouvert à travers une porte fermée ou si l'émetteur d'un battant modifie la
lightmap de l'autre.

