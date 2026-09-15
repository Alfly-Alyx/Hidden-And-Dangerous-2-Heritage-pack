# Audit du menu et du catalogue solo

Audit statique en lecture seule de l'installation locale. Les ressources commerciales ne sont pas reproduites.

## Catalogues effectifs

| Catalogue | Campagnes | Missions |
|---|---:|---:|
| SabreSquadron.dta:GameData\Gamedata00.gdt | 8 | 24 |
| SabreSquadron.dta:GameData\Gamedata01.gdt | 4 | 9 |

## Écrans et contrôles

- `models/main_menu.4ds` (SabreSquadron.dta) : `bresume game`, `text_date01`, `text_date00`, `text_profile00`, `text_profile01`, `text_last save00`, `text_last save01`, `actived00`, `normal00`, `bchange profile`, `actived01`, `normal01`, `bsingleplayer`, `actived02`, `normal02`, `bmultiplayerlan`, `actived03`, `normal03`, `bcinematics`, `actived04`, `normal04`, `boptions`, `actived05`, `normal05`, `bcredits`, `actived06`, `normal06`, `bexit`, `actived07`, `normal07`, `text_h&dversion`, `text_screen`, `bmultiplayernet`, `normal08`, `actived08`
- `models/selection screen.4ds` (SabreSquadron.dta) : `table`, `button01`, `actived02`, `normal02`, `button00`, `actived01`, `normal01`, `text_select one soldier`, `table15`, `table14`, `table13`, `table11`
- `models/single mission 2.4ds` (SabreSquadron.dta) : `bload mission`, `normal03`, `actived03`, `bexit`, `normal04`, `actived04`, `bshort`, `normal06`, `actived06`, `blong`, `normal05`, `actived05`, `text_screen`, `text_h&dversion`, `table01`, `scroll00`, `barrow down`, `normaldown`, `activeddown`, `inactiveddown`, `barrow up`, `normalup`, `activedup`, `inactivedup`, `slider`, `normal09`, `actived09`, `sliderbase`, `text_list of profiles`, `screen_shot`, `panel`, `video`, `bload lastsave`, `actived07`, `normal07`, `bexit01`, `normal10`, `actived10`
- `models/singleplayer.4ds` (SabreSquadron.dta) : `bcampaign`, `actived00`, `normal00`, `blone wolf`, `actived01`, `normal01`, `actived02`, `normal02`, `bsingle mission`, `actived03`, `normal03`, `bsingle mission- carnage`, `actived04`, `normal04`, `bback`, `actived06`, `normal06`, `text_h&dversion`, `text_screen`, `text_HD2original`, `text_HD2datadisk`, `normal09`, `actived09`, `blone wolf01`, `normal08`, `actived07`, `bcampaign01`, `normal07`, `actived08`

## Architecture visée

```text
Solo
├── Missions du jeu original          (inchangé : Gamedata00.gdt)
├── Missions Sabre Squadron           (inchangé : Gamedata01.gdt)
└── Missions personnalisées           (cible : Gamedata02.gdt)
    ├── Adaptations multijoueur
    ├── Créations originales
    └── Exploration libre
```

Boutons racine actuellement reconnus dans l’écran Solo : `bcampaign`, `blone wolf`, `bsingle mission`, `bsingle mission- carnage`, `bback`, `blone wolf01`, `bcampaign01`.

## Conclusion technique

- Le catalogue solo est piloté par `Gamedata00.gdt` et `Gamedata01.gdt`, qui contiennent une hiérarchie campagnes → missions.
- Les écrans du menu sont des scènes `.4ds` avec des contrôles nommés, mais leur action est prise en charge par l'exécutable.
- La séparation demandée impose de ne modifier ni `Gamedata00.gdt` ni `Gamedata01.gdt` : les contenus personnalisés doivent vivre dans un troisième catalogue.
- La scène peut recevoir visuellement une troisième commande `bcampaign02`, mais l'essai en jeu a confirmé que ce bouton n'est pas enregistré par le moteur.
- La première sonde a aussi provoqué un chevauchement de contrôles ; elle a été retirée et ne doit pas entrer dans l'installateur stable.
- Si le moteur ignore ce troisième suffixe, il faudra alors ajouter le gestionnaire dans l'exécutable ou employer un lanceur/catalogue séparé ; mélanger les missions avec celles d'origine n'est pas retenu comme solution.
- La piste d'un lanceur modifiant la mémoire a été abandonnée après détection antivirus ; aucune exclusion de sécurité ne doit être utilisée.

## Prototype statique préparé

Une copie de test séparée reçoit désormais un exécutable reconstruit hors
ligne. Le correctif enregistre `bcampaign02`, route son événement vers le
sélecteur de catalogue 2 puis vers le navigateur natif des missions solo, et
attribue au bouton l'identifiant de texte libre 20402.
Le premier routage de test empruntait la commande Campagne et lançait donc une
mission directement ; il a été remplacé. Les huit tables installées traduisent
le libellé selon la langue active. Le correctif ne contient aucune fonction de
modification d'un autre processus.

Le premier affichage du navigateur conservait la liste commerciale, car sa
boucle démarrait systématiquement au catalogue 0 et le suivi de progression ne
connaissait que les index 0 et 1. Le branchement personnalisé démarre maintenant
la boucle à l'index 2, rend toutes ses entrées visibles localement sans modifier
le profil, puis conserve l'index 2 lors du choix d'une mission. Les commandes
Single Mission officielles remettent le sélecteur à 0 avant d'ouvrir leur liste.

La scène finale compte 45 nœuds. Les 42 nœuds officiels conservent leurs
coordonnées exactes ; le contrôle personnalisé et ses deux états sont placés
au milieu de l'espace libre entre `SINGLE MISSION - CARNAGE` et `BACK`. Le nouveau
`Gamedata02.gdt` contient trois rubriques de validation et trois emplacements
techniques basés sur Brest, Libye1 et Sicily1. Ces entrées servent uniquement à
tester la navigation ; elles ne sont pas classées comme conversions solo.

Le jeu n'a pas été lancé après cette préparation. Une sauvegarde de
l'exécutable original et un script de restauration sont inclus dans la copie de
test.
