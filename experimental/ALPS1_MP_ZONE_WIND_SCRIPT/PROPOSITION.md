# Proposition expérimentale — ambiance de vent d'Alps1_MP_ZONE

État : reconstruction documentaire avec deux branches désactivées, 14 septembre
2026. Aucun script actif, registre ou fichier binaire de mission n'est modifié.

## Classification

**Variante officielle adaptée, expérimentale seulement.** Le registre de la
mission lie déjà l'acteur `zvuk1` à `V_a1_vitr_stromy.scr`, mais aucun script de
ce nom n'est conservé sous `Scripts/ALPS1_MP_ZONE`. La version solo fournit un
modèle presque complet ; elle ne peut cependant pas être copiée telle quelle,
car elle exige une frame sonore `S_poryv` absente de la carte Zone.

| Élément | Niveau | Motif |
| --- | ---: | --- |
| Binding `zvuk1` → script | 4/4 | liaison officielle déjà présente |
| Séquence des arbres | 4/4 | script solo et six frames Zone concordants |
| Rafale `S_poryv` | 0/4 | objet absent de la carte Zone |
| Fidélité d'une variante sans rafale | 3/4 | adaptation minimale d'un script officiel |
| Ajout dans `sounds.bin` | 1/4 | édition binaire et paramètres exacts non démontrés |

Il ne s'agit donc ni d'un simple oubli de registre, ni d'une restauration
octet pour octet. Le registre pointe vers un comportement perdu dont une
dépendance n'a jamais été portée dans la variante Zone.

## Preuves officielles

### Registre et absence du script

Le registre officiel d'`ALPS1_MP_ZONE` contient la liaison :

```text
zvuk1 -> V_a1_vitr_stromy.scr
```

En revanche, aucun fichier correspondant n'existe dans le répertoire de
scripts `ALPS1_MP_ZONE` des couches examinées. Le binding seul ne peut donc pas
faire vivre l'ambiance.

### Script solo conservé

`Scripts/ALPS1/V_a1_vitr_stromy.scr` recherche sept frames :

```text
S_poryv
S_stromy1
S_stromy2
S_stromy3
S_stromy4
S_stromy5
S_stromy6
```

Sa boucle attend `_RandomInt(18000) + 25000`, active `S_poryv`, attend encore
3 secondes, puis active simultanément les six sons d'arbres avant de
recommencer. La cadence officielle est donc une rafale toutes les 25 à 43
secondes, suivie des arbres trois secondes plus tard.

### Inventaire de la carte Zone

Dans la carte Zone, `zvuk1` et `S_stromy1..6` sont présents. `S_poryv` est
absent de `scene2.bin`, `actors.bin` et `sounds.bin`, aussi bien dans
l'inventaire structuré des noms que dans la recherche sur les octets bruts.
Cette double vérification écarte un simple défaut de l'extracteur de noms.

La copie du script solo produirait donc un résultat nul pour
`FRM_FindFrame(..., "S_poryv")`, puis tenterait d'exécuter
`FRM_SetOn` sur cette référence. Le comportement du moteur dans ce cas — appel
ignoré, erreur de script ou crash — n'est pas établi et ne doit pas être
présumé sûr.

## Option A — variante sans rafale

Premier prototype recommandé : créer uniquement dans le paquet expérimental
`Scripts/ALPS1_MP_ZONE/V_a1_vitr_stromy.scr` à partir du script solo, puis
retirer la recherche et l'activation de `S_poryv`.

Delta conceptuel par rapport au script officiel :

```diff
-frame sound1; frm_findframe(sound1,"S_poryv");
 frame sound2; frm_findframe(sound2,"S_stromy1");
 ...
 frame sound7; frm_findframe(sound7,"S_stromy6");

 rnd_pause = _randomint(18000) + 25000;
 delay(rnd_pause);
-FRM_SetOn(sound1, true);
 delay(3000);
 FRM_SetOn(sound2, true);
 ...
 FRM_SetOn(sound7, true);
```

Le délai de 3 secondes est conservé au premier essai. Cette solution modifie
ainsi seulement la dépendance impossible et préserve la période à laquelle les
arbres réagissaient dans le script solo. Son effet perceptible sera une courte
pause silencieuse à la place de la rafale ; le test d'ambiance décidera si ce
décalage reste naturel dans Zone.

Cette option est une **RECONSTRUCTION EXPÉRIMENTALE**, même si toutes les lignes
restantes sont officielles. Aucun exemplaire historique propre à Zone ne prouve
que la rafale devait y être silencieuse ou que le délai devait être conservé.

## Option B — restaurer un objet sonore équivalent

Une reconstruction plus fidèle en apparence consisterait à ajouter à la carte
un objet `S_poryv` équivalent à celui d'ALPS1, puis à reprendre le script solo
sans adaptation.

Cette option n'est pas recommandée tant que l'édition de `sounds.bin` n'est pas
maîtrisée et vérifiée. Elle exige de reproduire au minimum :

- le type et les paramètres complets de l'objet sonore ;
- son échantillon, sa portée, son volume et sa spatialisation ;
- ses références croisées dans les autres fichiers de mission ;
- son comportement en multijoueur et après sauvegarde/reprise.

Copier seulement un nom ou injecter une frame vide ne constitue pas une
restauration. Cette option touche à la structure binaire de la carte et reste
plus risquée que la variante sans rafale.

## Options rejetées

- **Copier le script solo tel quel** : il déréférence une frame absente.
- **Créer une frame factice `S_poryv`** : ses propriétés officielles dans Zone
  sont inconnues et un objet silencieux masquerait le défaut sans restaurer
  l'ambiance.
- **Supprimer les trois secondes avec la rafale** : cela change aussi la cadence
  des arbres ; à évaluer seulement comme second prototype après écoute.
- **Retirer le binding `zvuk1`** : le registre atteste au contraire qu'un script
  était attendu.
- **Promouvoir directement la variante dans le stable** : la sécurité des
  références nulles et l'équilibre sonore de la carte n'ont pas été testés.

## Prototypes désormais matérialisés

`PROTOTYPE_SIX_TREE_WIND.scr.disabled` correspond à l’option A. Il conserve le
binding officiel `zvuk1`, la pause aléatoire, les trois secondes et les six
émetteurs présents. Il ne cherche jamais `S_poryv` et ne nécessite aucune
édition de scène.

`PROTOTYPE_FULL_SEVEN_EMITTERS.scr.disabled` correspond à l’option B et reprend
le script solo intégral. Il est volontairement inutilisable seul : il ne peut
être activé qu’avec le record sonore décrit par
`PROTOTYPE_S_PORYV_IMPORT.plan.disabled`.

Les deux scripts sont des branches conservables et mutuellement exclusives. La
branche A ne remplace aucun comportement Zone effectif, puisque le binding vise
actuellement un fichier absent. La branche B ajoute l’émetteur manquant sans
modifier les six émetteurs existants.

## Données manquantes et hypothèses

- **Prouvé** : l’échantillon global `SOUNDS/a_a1wind.wav` existe dans
  `Sounds.dta`.
- **Prouvé** : `S_poryv` existe dans `ALPS1/sounds.bin`, mais pas dans les trois
  registres de scène/son de la Zone.
- **Manquant** : décomposition validée de son record binaire, parent et transform
  compris.
- **Manquant** : preuve que le transform solo est adapté à la géométrie Zone ou
  que le colocaliser avec `zvuk1` conserve une spatialisation naturelle.
- **Hypothèse faible** : la branche six arbres est sûre parce qu’elle ne
  déréférence que les six frames attestées.
- **Hypothèse moyenne** : un import exact de `S_poryv` suffit sans autre table ou
  référence croisée.

## Activation et retour arrière additifs

1. Dupliquer `ALPS1_MP_ZONE` ; ne jamais modifier la carte commerciale.
2. Branche A : fournir seulement le script désactivé sous le nom attendu par le
   binding existant.
3. Branche B : importer d’abord le record exact `S_poryv`, puis fournir le script
   sept émetteurs. Ne jamais activer le script complet sans ce record.
4. Ne jamais installer A et B ensemble sous deux propriétaires : `zvuk1` reste
   l’unique porteur de la boucle.
5. Retour arrière A : retirer le script ajouté. Retour arrière B : retirer le
   script et le seul record `S_poryv` importé.
6. Après retrait, l’unique binding orphelin commercial et les six émetteurs Zone
   doivent être byte-identiques à la baseline.

## Protocole de test

### Baseline de sécurité

1. Lancer la carte Zone sans reconstruction et confirmer que le binding vers le
   script absent ne provoque pas lui-même d'erreur.
2. Dans une copie de test jetable, charger une copie exacte du script solo afin
   d'observer explicitement le résultat nul de `FRM_FindFrame("S_poryv")` et le
   comportement de `FRM_SetOn` qui suit.
3. Ne conserver cette copie exacte dans aucun paquet distribué. Tout crash,
   erreur ou état indéfini confirme qu'elle est impropre à l'intégration.

### Variante sans rafale

1. Vérifier au chargement que les six recherches `S_stromy1..6` aboutissent et
   qu'aucune recherche de `S_poryv` n'est exécutée.
2. Observer plusieurs cycles complets : les six arbres doivent s'activer
   ensemble après 28 à 46 secondes, puis reprendre la boucle sans accumulation
   ni erreur.
3. Comparer au même emplacement l'ambiance solo et Zone : densité, volume,
   synchronisation des arbres et naturel de la pause sans rafale.
4. Tester une version de second rang sans le délai de 3 secondes uniquement si
   la pause silencieuse est perceptiblement défectueuse.
5. Recharger la carte plusieurs fois et vérifier une sauvegarde/reprise lorsque
   le mode le permet, avant l'attente, pendant l'attente et après l'activation.
6. Tester hôte et client dans les modes multijoueur concernés pour détecter une
   duplication locale ou une divergence d'ambiance.

Acceptation : aucun crash ni diagnostic de frame nulle, les six sons existants
se déclenchent une seule fois par cycle, la carte reste stable après reprise et
l'ambiance Zone n'est pas plus agressive ou artificielle que la référence solo.

## Verdict

Le manque du script est attesté, mais sa copie directe n'est pas sûre. La seule
reconstruction minimale actuellement défendable est une variante officielle
adaptée qui omet `S_poryv` et conserve d'abord le reste de la séquence solo.
Elle doit rester expérimentale jusqu'à validation dynamique de la référence
nulle, de l'ambiance et du multijoueur. L'ajout d'un véritable objet sonore est
une piste distincte, conditionnée par une édition fiable de `sounds.bin`.

## Sources internes

- registre officiel de `ALPS1_MP_ZONE`, binding de `zvuk1`
- `.analysis/scripts/base/SCRIPTS/ALPS1/V_a1_vitr_stromy.scr`
- inventaires structurés et recherches brutes de `scene2.bin`, `actors.bin` et
  `sounds.bin` d'`ALPS1_MP_ZONE`
