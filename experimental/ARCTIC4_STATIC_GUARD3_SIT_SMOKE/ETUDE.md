# Arctic 4 — garde 3, assise et cigarette

État du 25 septembre 2026 : **prototype MODERNE désactivé**, construit et
contrôlé hors jeu. Aucun fichier de l'installation n'est modifié. Le profil
commercial reste le défaut; ce laboratoire est distinct de celui du poste
d'alarme et les deux variantes ne s'empilent pas.

## Vestige et ressources

Le script commercial contient une séquence commentée de rotation, assise et
cigarette, puis une animation nommée `%%kourimsed2`. Sa
[transcription historique](SEQUENCE_HISTORIQUE.scr.disabled) reste entièrement
commentée. Aucun usage actif de cette animation n'a été démontré : elle n'est
pas réactivée. Les primitives `HUMAN_ACTIVITY_Sit` et `Smoke` ont en revanche
des précédents actifs dans le corpus, notamment chez les porteurs de Czech 3.

La liaison unique `Static_Guard_3` vers `r_arc3_static_guard_3.scr` et le
propriétaire humain sont vérifiés. Les deux frames sont décodées dans le
`scene2.bin` effectif du Patch, pas seulement retrouvées par recherche de texte.

| Frame | Position initiale (x, y, z) |
|---|---|
| `Static_Guard_3` | −58,356277 ; 11,104563 ; −47,424149 |
| `Dummy_Static_Guard_3_sit` | −61,436405 ; 11,044524 ; −49,417816 |
| `Dummy_Static_Guard_3_see` | −68,314751 ; 8,927683 ; −54,897408 |

Le sous-nœud `__Dummy_Static_Guard_3_sit`, à une autre position, n'est pas
substitué à la frame nommée dans le script. La présence d'une cible ne prouve
ni le trajet depuis les quatre points de ronde, ni l'absence de collision avec
le siège. Ces deux questions demandent un essai en moteur.

## Variante complète

Le profil `arctic4-guard3-sit-smoke` du
[catalogue reproductible](../reconstruction-variants.json) applique huit
modifications bornées, après contrôle de quatre sources commerciales :

- les deux déclarations de frames sont réactivées;
- la séquence utilise l'assise et la cigarette génériques, sans animation au
  nom incertain; une attente réutilise le tirage commercial de 2,5 à 10 secondes;
- un état local `SitActive` est armé avant l'appel d'assise interruptible;
- avant la ronde suivante, la cigarette et l'animation s'arrêtent, puis le
  garde se relève avant tout mouvement; après 650 ms, la cigarette debout reprend;
- l'alarme et le signal 1 quittent l'assise avant leur comportement commercial;
- la mort éteint la cigarette et efface l'état local, sans relever le corps.

L'état est local au script, pas un compteur de sauvegarde global. Les signaux
vers les autres gardes, la conversation, les réglages de combat et le retour
commercial après alarme restent inchangés. Le mouvement vers `StaticGuard3_5`
reste commenté. Le délai d'assise et les protections sont des choix modernes,
pas la prétendue restitution d'un comportement officiel complet.

## Preuves reproductibles

Source : `Scripts.dta`, 2508 octets, SHA-256
`73e72535024bedf65787ae3fda305724ab1386c6941c9809ea786fbe9a41208b`.
Sortie : **3049 octets**, SHA-256
`df4e8fee9961535e4d254162715754ca16dd11609dcd62b07b487b8392d95470`.
Les empreintes du registre, des acteurs et de la scène sont dans le catalogue.

Le laboratoire local contient 115 fichiers par branche, 100 scripts accessibles
et les neuf objectifs commerciaux inchangés. Ses espaces sont
`H2Lab_arctic4_2b56044271d7_B` et `_V`; tous les fichiers et manifestes restent
suffixés `.disabled`. Aucun script commercial complet n'est publié dans Git.
Quatre tests automatisés vérifient le contrat textuel de posture, la protection
avant assise, la mort et l'exclusion de l'animation incertaine. Ils n'émulent
pas le moteur du jeu.

## Essais encore obligatoires

1. Comparer le témoin et la variante sur plusieurs rondes et sur chacun des
   quatre points de départ : déplacement vers le siège, hauteur, orientation,
   cigarette, sortie du siège et absence de téléportation.
2. Déclencher alarme et signal 1 avant, pendant et après chaque délai et
   transition, notamment entre `SitActive = 1` et le retour de `Sit`.
3. Vérifier que la conversation et son signal 2 restent exécutés une seule
   fois et que les trois snipers reçoivent toujours les signaux commerciaux.
4. Tester mort assise et debout, retour après alarme, seconde alarme et reprise
   de sauvegarde dans chaque posture. Aucune animation ni cigarette orpheline.
5. Refuser la variante en cas de clipping, réaction retardée ou déplacement
   cassé; ne pas compenser en inventant un checkpoint historique.

Tous ces essais restent **pending**. Le laboratoire ne peut pas être déclaré
jouable à partir des seuls contrôles de fichiers.
