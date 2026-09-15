# Étude expérimentale — objectif 4 de survie de Co_Libye2

État : **blocage documenté, aucun prototype `.scr.disabled`**, 14 septembre
2026. Cette étude ne modifie aucun script actif, aucune métadonnée de carte et
aucune installation du jeu.

## Verdict

L'intention historique est solide, mais sa reconstruction coop fidèle ne l'est
pas encore. Les sources de Libye2 décrivent l'objectif 4 comme « tous doivent
survivre » et le texte de réussite comme « personne n'est mort ». En solo, le
contrôleur vérifie `_IsTeamMemberDead()` à l'extraction, quand les équipiers ne
réapparaissent pas : état final et absence de mort au cours de la mission y sont
donc équivalents.

Cette équivalence disparaît en coopération. Co_Libye2 active quatre nouvelles
zones de réapparition, tandis que les scripts coop officiels inspectés ne
fournissent aucun événement de mort/réapparition de joueur et n'emploient jamais
activement `_IsTeamMemberDead()`. Un test effectué seulement à l'extraction
pourrait récompenser une équipe après une ou plusieurs morts effacées par le
respawn. Un test continu avec la même primitive resterait une supposition sur
son fonctionnement réseau et pourrait manquer l'intervalle mort.

Le sens le plus fidèle est donc :

> Dès qu'un joueur appartenant à la cohorte évaluée meurt, l'objectif facultatif
> est définitivement perdu pour cette tentative ; une réapparition ne répare
> pas cette mort.

C'est une **inférence forte** à partir du solo et des commentaires, pas un
contrat coop exécutable avec les seules primitives attestées. La définition de
la cohorte — joueurs présents au départ, tous les participants successifs ou
membres connectés à l'extraction — reste elle aussi absente des sources.

## Chaîne conservée et chaîne manquante

### Co_Libye2

`AF2_objective.scr` conserve :

- l'initialisation commentée `SetObjectiveStatus(4, 4)` avec le commentaire
  `optional - vsetci musia prezit` ;
- la validation finale de l'objectif 2 sous
  `_MP_AllTeamMembersAreInRange(1, 80)` ;
- le signal 1 reçu d'`AF2_obj3.scr`, qui valide l'objectif 3 de dégâts aux
  véhicules. Cet objectif 3 est hors du périmètre de la présente étude.

Il ne contient en revanche aucun test ni mise à jour de l'objectif 4.

`AF2_texty.scr` conserve un `OnSignal(4)` complet. Son commentaire dit
`nikto ti neumrel` (« personne n'est mort ») et il affiche le texte `53999802`.
Le retour utilisateur de réussite a donc survécu, mais son émetteur coop a
disparu.

Enfin, `AF2_zone2enable.scr` à `AF2_zone5enable.scr` appellent
`MP_EnableSpawnZone(...)`. Le signal 7 associé affiche « NEW RESPAWN ZONE
AVAILABLE! ». Le respawn n'est donc pas un cas théorique extérieur à cette
mission : sa progression ouvre explicitement des zones destinées à cela.

### Variante solo

Dans `Libye2/AF2_objective.scr`, la réussite de l'objectif 4 se trouve dans le
label final `dalej`, juste avant la réussite de l'objectif 2 :

```text
If(!_IsTeamMemberDead())
{
    If(gametype==2) { GoTo pokracuj; }
    SetObjectiveStatus(4, 1);
    SendSignal(texty, 4);
    Delay(3000);
}
```

La version `AF2_objective2.scr` reproduit le même principe. Ce code prouve le
moment de validation et le message à émettre. Il ne prouve pas comment
`_IsTeamMemberDead()` traite un avatar réseau remplacé après une mort.

Un précédent renforce cette réserve : dans
`Co_Burgundy1/bur1_maquis01.scr`, la branche de survie copiée du solo existe
encore, mais elle est entièrement commentée. C'est l'unique occurrence de
`_IsTeamMemberDead()` trouvée dans un répertoire coop Sabre ; aucune occurrence
coop active n'a été trouvée.

## Déclaration d'objectif incomplète

La carte `Co_Libye2` de `mpmaplist.txt` ne déclare que deux objectifs :
`15520` et `15521`. La copie de carte du Coop Map Package consultée confirme le
même couple pour la variante originale.

Par conséquent, même une détection parfaite des morts ne suffirait pas : le
comportement de `SetObjectiveStatus(4, ...)` face à seulement deux entrées de
carte n'est pas établi. Il pourrait être invisible, ignoré ou dépendre d'une
convention non documentée. Le handler de sous-titre 4 peut afficher une réussite,
mais il ne crée pas à lui seul une quatrième ligne d'objectif.

L'objectif 3 de dégâts, déjà conservé par `AF2_obj3.scr` et traité par le
contrôleur principal, n'est ni dupliqué ni réévalué ici. Son existence ne
constitue pas une preuve que le slot 4 et son libellé sont sûrs.

## Primitives coop réellement observées

L'inventaire textuel de tous les scripts Sabre fait apparaître seulement quatre
primitives explicitement multijoueurs :

| Primitive | Usage officiel observé | Ce qu'elle ne prouve pas |
| --- | --- | --- |
| `_MP_AllTeamMembersAreInRange` | barrière spatiale de groupe, dont les deux étapes de Co_Libye2 | aucune mémoire d'une mort antérieure |
| `_MP_IsTeamMemberInRange` | présence d'au moins un membre près d'un acteur ou d'une zone | identité, décès ou historique de la cohorte |
| `_MP_IsItemInTeamInventory` | suivi d'un objet possédé par l'équipe | état vital des porteurs successifs |
| `MP_EnableSpawnZone` | ouverture d'une zone de réapparition | événement indiquant qu'un joueur vient réellement de réapparaître |

Deux autres mécanismes ne comblent pas la lacune :

- `OnDeath()` est largement utilisé dans les scripts coop des PNJ et véhicules
  nommés. Il est attaché au script de l'acteur fixe ; aucune liaison officielle
  équivalente aux avatars de joueurs sélectionnés dynamiquement n'a été trouvée.
- `_ACTOR_GetState(frame)` permet de compter les morts d'acteurs connus. Le
  `AF2_deadcounter.scr` de Co_Libye2 l'emploie pour huit soldats ennemis de la
  colonne, pas pour l'équipe des joueurs.

La recherche globale ne trouve ni `OnPlayerDeath`, ni `OnRespawn`, ni
`OnConnect`, ni `OnDisconnect`, ni `TeamMemberDeath`. `_AllPlayersDead()`
n'apparaît que dans un script solo de Libye2 : même disponible, un test de mort
simultanée de tous les joueurs ne mémoriserait pas la première perte individuelle.

`SaveGameValue` ou un entier local pourraient rendre un drapeau de perte
irréversible **après** une détection. Ils ne fournissent pas la détection qui
manque.

## Sens possibles avec respawn

| Règle | Mort puis respawn avant extraction | Fidélité | Problème |
| --- | --- | --- | --- |
| aucune mort pendant la tentative | échec définitif | la plus proche du solo et de « personne n'est mort » | événement de mort fiable absent |
| tous vivants à l'extraction | réussite possible | faible | transforme « survivre » en simple état instantané |
| personne en attente de respawn à l'extraction | réussite possible | faible | dépend du minutage du respawn |
| tous les membres actuels dans la zone | déjà exigé par l'objectif 2 | nulle comme objectif distinct | devient redondant et ne suit aucune perte |

La configuration serveur confirme que la réapparition est optionnelle et
temporisée : le Lisez-moi officiel de Sabre Squadron documente `allowrespawn`,
`respawntime` et `spawnprotection`, avec réapparitions groupées hors deathmatch.
Une règle valable uniquement lorsque `allowrespawn=0` ne serait donc pas une
reconstruction générale de la mission coop.

## Prototypes envisagés puis rejetés

### Copier le test solo à l'extraction

```text
If(!_IsTeamMemberDead())
{
    SetObjectiveStatus(4, 1);
    SendSignal(texty, 4);
}
```

Rejet : la primitive n'a aucun précédent coop actif, son résultat après respawn
est inconnu et cette variante ne conserve aucun historique. Elle peut produire
un faux succès précisément dans le cas demandé.

### Échantillonner en continu et mémoriser

```text
Whenever casualty(_IsTeamMemberDead())
{
    casualty_seen = 1;
    SetWhenever(casualty, false);
}
```

Rejet : le drapeau est correct, mais son déclencheur n'est pas démontré. On ne
sait pas si la condition observe tous les clients, si elle est évaluée pendant
l'attente de respawn, ni si une réapparition rapide remplace l'acteur avant
l'évaluation. Un `Whenever` non déclenché une seule fois donnerait un faux
succès irréversible.

### Ajouter `OnDeath()` aux joueurs

Rejet : aucun mécanisme officiel observé ne permet au contrôleur de mission
découvrir les frames des avatars, d'y attacher ce handler ou de suivre leur
remplacement lors d'une réapparition. Cela inventerait une architecture plus
large qu'un correctif d'objectif.

### Déduire une mort de l'usage des zones de respawn

Rejet : `MP_EnableSpawnZone` signale seulement qu'une zone devient disponible.
Son appel dépend de la progression et des ennemis éliminés, pas d'une mort ni de
l'apparition effective d'un joueur.

Aucun de ces candidats n'est assez justifié pour produire un fichier
`.scr.disabled` aujourd'hui.

## Risques d'une implémentation prématurée

- **Faux succès après respawn** : le cas central serait évalué comme si personne
  n'était mort.
- **Faux échec de réseau** : un client déconnecté, un spectateur ou un joueur en
  changement d'avatar pourrait être interprété comme mort.
- **Course temporelle** : un intervalle mort très court pourrait échapper au
  polling du script.
- **Autorité hôte/client** : un état local non répliqué pourrait diverger selon
  le poste qui évalue le `Whenever`.
- **Cohorte mouvante** : arrivée tardive, départ volontaire et reconnexion n'ont
  aucune règle historique attestée.
- **Interface orpheline** : le signal de réussite peut s'afficher sans objectif
  4 visible ou sans état partagé valable.
- **Sauvegarde/reprise** : un entier local ou une valeur mal choisie peut perdre
  ou écraser l'historique de mortalité.

## Preuves nécessaires pour lever le blocage

Une copie laboratoire de la mission devrait d'abord tracer, sans attribuer
l'objectif :

1. `_IsTeamMemberDead()` côté hôte et côté client avant la mort, pendant
   l'attente, à la frame de réapparition et après le retour en jeu ;
2. le déclenchement d'un `Whenever` basé sur cette primitive pour une mort très
   courte et pour plusieurs morts successives ;
3. les cas `allowrespawn 0` et `allowrespawn 1`, avec plusieurs valeurs de
   `respawntime` ;
4. un, deux et quatre joueurs, mort de l'hôte puis d'un client ;
5. arrivée tardive, déconnexion, reconnexion, changement d'équipe et spectateur ;
6. activation de chacune des zones 2 à 5 avant et après une mort ;
7. comportement réseau et visuel d'un quatrième objectif déclaré dans une
   métadonnée expérimentale, avec un libellé attesté dans toutes les langues.

La promotion ne devient raisonnable que si l'un des deux faits suivants est
obtenu : un événement joueur officiel fiable, ou la preuve expérimentale que
`_IsTeamMemberDead()` reste vrai assez longtemps et voit toutes les morts de la
cohorte depuis l'hôte. Il faudra ensuite figer explicitement la règle d'adhésion
à cette cohorte et vérifier que le drapeau persiste correctement.

## Décision de périmètre

`docs/CREATIONS_EXPERIMENTALES.md` n'est pas modifié : la consigne impose des
écritures sous `experimental/` uniquement, et le verdict ne produit encore
qu'une étude bloquée sans prototype testable.

## Sources internes

- `.analysis/scripts/sabre/Scripts/Co_Libye2/AF2_objective.scr`
- `.analysis/scripts/sabre/Scripts/Co_Libye2/AF2_obj3.scr`
- `.analysis/scripts/sabre/Scripts/Co_Libye2/AF2_texty.scr`
- `.analysis/scripts/sabre/Scripts/Co_Libye2/AF2_deadcounter.scr`
- `.analysis/scripts/sabre/Scripts/Co_Libye2/AF2_zone2enable.scr` à
  `AF2_zone5enable.scr`
- `.analysis/scripts/sabre/Scripts/Libye2/AF2_objective.scr`
- `.analysis/scripts/sabre/Scripts/Libye2/AF2_objective2.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bur1_maquis01.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy1/bur1_maquisend.scr`
- `.analysis/metadata/sabre/GameData/mpmaplist.txt`
- `.analysis/cmp-normandy/.../cmp_info/cmp_Maplist.txt`

## Source externe primaire

- [Lisez-moi officiel de Hidden & Dangerous 2: Sabre Squadron, copie
  archivée](https://hidden-and-dangerous.net/junk/ss_readme.htm) — commandes
  serveur `allowrespawn`, `respawntime` et `spawnprotection`.
