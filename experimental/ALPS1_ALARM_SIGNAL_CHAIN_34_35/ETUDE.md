# Ge34/ge35 — chaîne additive d'alarme

État : **profils de test désactivés, handlers 3/4 reconstructifs**, 15 septembre
2026. La réaction release ge34→ge33 et tout le corps actuel de ge35 sont
conservés. Rien n'est compilé.

## Chaîne attestée

`ge_34.scr` conserve un bloc commenté qui, pour toute alarme sauf 64, enverrait
le signal 1 à `signal_ke_strelnici`. Sa réaction active reste indépendante :
sur l'alarme 32, ge34 se met debout, envoie le signal 3 à ge33, s'arme, se tourne
vers le joueur et termine.

Le contrôleur `signal_ke_strelnici.scr` attend le signal 1. Deux secondes plus
tard il envoie 3 à ge35 ; après huit secondes supplémentaires il envoie 3 à
`ridiccasovac`, ge30, ge31 et ge32. Ces quatre dernières cibles possèdent leur
chaîne d'alerte ; ge35 ne traite actuellement que le signal 1.

Une seconde rupture existe : `ge_36.scr` envoie le signal 4 à ge35 dans
`OnAlarm()`, sans récepteur correspondant.

## Réactions ge35 proposées

Le label `hotovo` est la seule convergence interne complète de ge35 : il coupe
signaux/événements, choisit une cinématique ou la branche `founikdet`, prévient
ge36/ge37 et peut échouer l'objectif. Relier les signaux 3/4 à ce label est donc
plausible, mais à haut impact et non attesté.

[`PROTOTYPE_GE35_HANDLERS.scr.disabled`](PROTOTYPE_GE35_HANDLERS.scr.disabled)
ajoute explicitement deux handlers séparés vers `hotovo`. Un verrou moderne
`alarm_chain_armed` n'autorise ce saut qu'après le signal 1 commercial de ge35 ;
il évite qu'une alerte hors séquence lance une cinématique avant l'activation de
la zone. Ce verrou est une sécurité expérimentale, pas une source historique.

[`PROTOTYPE_GE34_EMITTER.scr.disabled`](PROTOTYPE_GE34_EMITTER.scr.disabled)
réactive seulement le bloc commenté. La branche active `aievent==32` vers ge33
doit rester immédiatement après et inchangée.

## Profils gradués

Le [`VARIANT_SELECTOR.plan.disabled`](VARIANT_SELECTOR.plan.disabled) impose :

1. `RELEASE` ;
2. émetteur ge34 seul, ge35 toujours no-op sur 3 ;
3. handler 3→hotovo seul avec chaque source testée séparément ;
4. handler 4→hotovo seul depuis ge36 ;
5. combinaison seulement si les deux chemins sont sûrs et dédupliqués.

Le signal 3 de ge35 a deux sources (`signal_k_ohni` et
`signal_ke_strelnici`) ; elles doivent être distinguées dans les traces. Le
signal 4 ne doit pas devenir un alias silencieux : son origine ge36 et son
verdict sont consignés séparément.

## Tests

- tester ge34 sur chaque type d'alarme, particulièrement 32 et 64, et confirmer
  que ge33 conserve exactement sa réaction actuelle ;
- déclencher ge35 signal 3 avant/après son signal 1, depuis le feu puis depuis
  le stand, avec téléphone intact/détruit et valeurs 10/11/14 variées ;
- tester signal 4 depuis chaque chemin d'alarme de ge36 ;
- couvrir signaux simultanés 3+4, compteurs b/c juste avant seuil, explosion 16,
  cinématiques 1/2, objectif 6, ge36/ge37 morts et conversations ;
- sauvegarder avant l'armement, avant `hotovo`, pendant les cinématiques et
  après `founikdet`.

Rejet : cinématique prématurée, double exécution de `hotovo`, objectif modifié
hors condition, réaction ge33 perdue, chaîne ge30–32 perturbée ou différence
réseau. En cas d'échec, laisser les émissions/handlers commentés plutôt que
modifier silencieusement le label.

## Sources

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_34.scr` à `ge_36.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/signal_ke_strelnici.scr` et
  `signal_k_ohni.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_30.scr` à `ge_32.scr` ;
- `experimental/ALPS1_GE33_GE35_SIGNALS/ETUDE.md`.
