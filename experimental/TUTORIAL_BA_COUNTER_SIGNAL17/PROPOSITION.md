# Proposition expérimentale — signal 17 du compteur d'obstacles Tutorial

État : étude non intégrée et prototype désactivé, 14 septembre 2026. Aucun
script commercial ni fichier de mission n'est modifié. Le corps proposé est
explicitement une **RECONSTRUCTION MODERNE**, pas un handler officiel retrouvé.

## Classification

**Correction anti-répétition probable, à condition de reproduire le défaut.**
Les cinq actions du parcours sont actives et correctement raccordées. Il ne
s'agit donc pas de contenu coupé. L'anomalie porte uniquement sur le signal 17
que l'instructeur envoie au compteur des barrières après validation globale et
que ce compteur ne traite pas.

| Aspect | Niveau | Motif |
| --- | ---: | --- |
| Cinq étapes du parcours | 4/4 | handlers 1 à 5 actifs dans l'aide instructeur |
| Cinq barrières | 4/4 | compteurs et émetteurs 1 à 5 actifs |
| Intention de terminaison du signal 17 | 3/4 | envoyé dans les cinq branches après validation |
| Corps exact du handler 17 | 1/4 | aucun exemplaire conservé |

## Deux compteurs officiels

### Compteur global de l'instructeur

`TUT_Instructor1_AID.scr` incrémente `MOC` pour cinq segments :

1. snakeway ;
2. passerelles ;
3. barrières et échelle ;
4. barbelés ;
5. tranchées.

Dans chacune des cinq branches, dès que `MOC > 4`, le script :

- désactive l'indice concerné par signal 31 ;
- prévient le second instructeur par signal 10 ;
- envoie le signal 17 à `dummy_BA_counter` ;
- joue les répliques de validation ;
- valide l'objectif par signal 1.

Les branches ne possèdent pas de verrou local après cette validation. Un nouvel
événement peut donc incrémenter encore `MOC` et rejouer le bloc tant que le
script n'a pas reçu son propre signal 10 de terminaison.

### Compteur spécifique des cinq barrières

`TUT_dummy_BA_counter.scr` reçoit les signaux 1 à 5 des cinq détecteurs
d'obstacles. Chacun incrémente `counter` et, dès que `counter > 4`, envoie le
signal 3 à `TUT_Instructor1_aid`. La première barrière déclenche aussi une
réplique par `dummy_dabing`.

Le compteur ne désactive ni ses signaux ni son script après cinq événements.
Chaque réception ultérieure de 1 à 5 renvoie donc le signal 3 à l'instructeur.
Ce signal 3 est précisément la branche « barrières et échelle » du compteur
global : elle incrémente de nouveau `MOC` et, si le parcours est déjà validé,
rejoue notamment le signal 17 et la validation d'objectif.

Aucun `OnSignal(17)` n'est présent dans `TUT_dummy_BA_counter.scr`, et aucune
copie Patch du script ne fournit le corps absent.

## Architecture ancienne encore visible

Le registre commercial lie simultanément `dummy_MicroObj_counter` à
`TUT_Dummy_MicroObj_counter.scr` et `TUT_Instructor1_aid` à son nouveau script.
Cependant, les compteurs SW, LA, BA et ZA ainsi que `dummy_WI` envoient désormais
leurs résultats à `TUT_Instructor1_aid`. Aucun émetteur courant ne transmet plus
les signaux 1 à 5 à l'ancien compteur ; certains commentaires LA nomment encore
ce destinataire, ce qui révèle la transition incomplète.

L'ancien `TUT_Dummy_MicroObj_counter.scr` conserve un arrêt exact sur signal 10 :

```text
DisableSignals(true);
EndScript();
```

`TUT_Instructor1_aid.scr` emploie le même corps pour son propre signal 10.
Enfin, `T_dummy_AC_Hint.scr` envoie 10 aux deux compteurs si le joueur abandonne
la zone, preuve que cette paire coexistait pendant la migration. Ces trois faits
établissent le **vocabulaire officiel d'arrêt d'un compteur**, mais pas le numéro
17 ni le corps historique qui manquent dans `dummy_BA_counter`.

## Hypothèse

**INFÉRENCE forte.** Le signal 17 devait neutraliser le compteur spécialisé une
fois que l'instructeur avait validé les cinq catégories du parcours. Sa présence
dans chacun des cinq blocs `MOC > 4` est cohérente avec une terminaison quel que
soit le dernier segment accompli.

Cette interprétation explique aussi pourquoi le signal cible le compteur des
barrières plutôt qu'un objectif : il coupe une source de répétitions, tandis que
la validation proprement dite est déjà envoyée séparément à
`dummy_objectives`.

Le corps exact reste inconnu. Il pouvait se limiter à `EndScript()`, désactiver
d'abord les signaux, ou réinitialiser certains états. Une remise de `counter` à
zéro serait même dangereuse : les détecteurs BA 2 à 5 restent actifs et pourraient
reconstruire le compte puis réémettre. Aucun reset n'est donc proposé sans source.

## Porte de décision obligatoire

Avant tout prototype, reproduire le parcours original sans handler 17 :

1. franchir les cinq catégories jusqu'à la première validation globale ;
2. confirmer que `dummy_BA_counter` reçoit bien le signal 17 sans réaction ;
3. retraverser un ou plusieurs détecteurs BA déjà comptabilisés ;
4. relever `counter`, `MOC`, les signaux 3 et 17, les répliques et les signaux
   vers `dummy_objectives` ;
5. vérifier si la validation, les sous-titres ou les instructions se répètent.

Si les détecteurs BA sont déjà rendus inactifs par le moteur ou par leur propre
script, et qu'aucune répétition n'est observable, classer le signal 17 comme
redondant et ne rien ajouter.

## Delta expérimental conditionnel — MODERNE

Seulement si la baseline démontre que le compteur continue d'émettre après la
validation, essayer le handler suivant :

```diff
+OnSignal(17)
+{
+  DisableSignals(true);
+  EndScript();
+}
```

Ce corps est le candidat le plus prudent parce que :

- la réception de 17 arrive après que l'instructeur a déjà validé `MOC > 4` ;
- le compteur n'a plus de sortie utile démontrée après cette étape ;
- l'ancien `TUT_Dummy_MicroObj_counter.scr` et `TUT_Instructor1_AID.scr`
  utilisent tous deux la séquence `DisableSignals(true); EndScript();` sur 10.

L'analogie rend le delta plausible, pas officiel. Un second essai avec
`EndScript()` seul peut déterminer si `DisableSignals(true)` est nécessaire,
mais ne doit pas devenir la variante de référence sans différence observée.
Le fragment testable est conservé dans
`PROTOTYPE_SIGNAL17_STOP.scr.disabled` ; il n'est ni lié ni installé.

## Risques à contrôler

- **Arrêt prématuré :** `MOC` peut atteindre cinq avant que les cinq entrées BA
  aient toutes été reçues ; confirmer qu'aucune instruction ultérieure ne
  dépend encore du compteur BA.
- **Ordre synchrone :** si le signal 3 du compteur provoque immédiatement la
  validation et le signal 17 en retour, vérifier que terminer le compteur
  pendant sa propre pile d'appel est sûr.
- **Répétition déjà engagée :** le handler ne doit pas dupliquer une réplique ou
  empêcher la validation en cours de se terminer.
- **Sauvegarde/reprise :** l'état terminé doit rester cohérent avant et après la
  réception de 17.
- **Plusieurs joueurs :** des franchissements quasi simultanés ne doivent ni
  perdre le cinquième événement ni produire plusieurs validations.

## Matrice de test

1. Accomplir les cinq segments dans plusieurs ordres, les barrières en premier
   puis en dernier.
2. Répéter chaque détecteur BA avant le seuil, au seuil et après le seuil.
3. Produire deux franchissements presque simultanés au moment où `counter`
   passe de 4 à 5.
4. Vérifier que le cinquième événement envoie encore exactement un signal 3 et
   que le signal 17 n'interrompt pas la réplique ou l'objectif en cours.
5. Après 17, confirmer que les signaux BA 1 à 5 ne produisent plus aucun effet.
6. Tester la réception directe du signal 10 de l'instructeur avant et après 17.
7. Sauvegarder/reprendre avec `counter` à 4, immédiatement après le cinquième
   événement et après la terminaison.

Acceptation : une seule validation globale, aucune répétition de l'instruction
ou de l'objectif, aucun blocage avant le cinquième événement utile et aucune
erreur lors du retour synchrone du signal 17.

## Verdict

Le signal 17 constitue vraisemblablement une terminaison perdue du compteur BA,
mais cette conclusion ne transforme pas les cinq obstacles en contenu coupé.
Le prototype MODERNE reprend un idiome d'arrêt officiel sans prétendre restaurer
le handler exact. Il n'est autorisé qu'après reproduction d'une répétition ;
aucun reset et aucun delta stable ne sont proposés.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_Instructor1_AID.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_BA_counter.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_BA1.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_BA2.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_BA3.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_BA4.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_BA5.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_Dummy_MicroObj_counter.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/T_dummy_AC_Hint.scr`
- `.analysis/tutorial/base/MISSIONS/TUTORIAL/Scripts.dta`
