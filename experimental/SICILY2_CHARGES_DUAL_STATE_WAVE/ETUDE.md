# Sicily 2 — vague après déminage partiel

État du 25 septembre 2026 : profil **MODERNE**
`sicily2-three-cleared-wave`, généré et désactivé; essais moteur en attente.

## Contrat observé

Les six charges `naloz_1..6` sont sérialisées. Chacun de leurs scripts observe
l'état 0 puis termine; l'ancienne conversion 0→3 est commentée. Leur signal
d'explosion ne traite que l'état 1, puis écrit l'état 2.

`dummy_naloze_test` exige les **six états 0** et envoie le signal 3 à l'unique
gestionnaire d'objectifs. Réactiver les six conversions 0→3 empêcherait ce test
de réussir. Il ne faut donc pas décommenter ces conversions.

L'inventaire initial disait que l'activateur « met trois charges à l'état 3 » :
c'était inexact. `dummy_druha_vlna` **observe** exactement trois états 3; il ne
modifie aucune charge. Trois autres conditions peuvent déjà lancer sa vague :
compte des ennemis, proximité 150 m et temporisation de six minutes après 260 m.

## Variante implémentée

Un seul prédicat change dans `Sic2_vlna2_aktivator.scr` : il compte les états 0
au lieu des états 3 et exige **au moins trois** au lieu d'exactement trois.
Cela évite de manquer le seuil si plusieurs charges sont retirées entre deux
observations. Les états 1, 2 et 3 ne comptent pas comme charges retirées.

Tous les autres octets restent identiques : six scripts de charges, test final
de déminage, autorité des objectifs, trois déclencheurs alternatifs, dix-huit
destinataires de la vague et terminaison `EndScript()`. Aucun compteur partagé,
signal ou objectif supplémentaire n'est ajouté. Le mécanisme commun de fin du
contrôleur est conservé; son comportement lors de déclenchements simultanés doit
être observé, pas supposé validé par les tests hors moteur.

Le choix moderne porte sur le moment de la vague, pas sur une restauration
historique authentifiée. Le profil commercial reste le défaut.

## Preuves et artefacts

Le [catalogue](../reconstruction-variants.json) verrouille cinq sources, dont
le contrôleur d'objectifs de déminage (non modifié), le registre et les acteurs.
Le propriétaire de vague est une frame typée de `scene2.bin`, pas un humain dans
`actors.bin`. Le générateur exige désormais cette source de propriétaire
explicitement déclarée et verrouillée, sans élargir la recherche aux chaînes
arbitraires. Les six charges et les dix-huit destinataires sont vérifiés.

La sortie fait 3228 octets, SHA-256
`0f0414e6432b26f2030ffb10f40713db4e51ee3ddf7acb5b84fb1b93e72caf37`.
Le laboratoire copie 131 fichiers par branche et résout 117 scripts accessibles,
sans dépendance absente. Les [tests de modèle](../../tests/test_reconstruction_state_models.py)
examinent les 4096 combinaisons des états 0..3 des six charges et le saut du seuil
2→4. Ils vérifient le prédicat, **pas** l'ordonnancement ou la physique du moteur.

## Validation et retrait

Comparer dans les deux copies : déminage progressif 0/1/2/3/4/6, retrait rapide
de plusieurs charges, charge explosée, arrivée préalable par proximité, puis
déclenchement pendant la temporisation. Observer une seule vague, les mêmes
dix-huit destinataires, l'objectif de déminage après six retraits et la fin de
mission. Tester sauvegarde/reprise avant et après le seuil, puis juste avant le
dernier retrait. Une seconde vague, un objectif bloqué ou une fausse validation
interdit la promotion. Le retrait concerne seulement la copie laboratoire;
aucun fichier du jeu courant n'est modifié par la génération.
