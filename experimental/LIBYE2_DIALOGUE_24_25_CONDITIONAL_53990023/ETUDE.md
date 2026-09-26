# Libye 2 — réplique conditionnelle 53990023

État : audio et condition commerciale vérifiés, contrat de reprise à tester,
26 septembre 2026. La phrase n'est pas décommentée sans condition.

`AF2_24_25_speech.scr` solo et coop sont byte-identiques : SabreSquadron.dta,
1582 octets, SHA-256
`f9fe3179451386b0c110ce1831655ec85271c0b0ae30e556569590db7186ddce`.
La ligne 53990023 est commentée entre 22 et 24, avec la note « parc détruit ».
Le contrôleur est lié, tout comme les deux locuteurs AF2_24/25.

## Condition exacte, pas un compteur approximatif

`AF2_obj3` considère le parc détruit lorsque les **huit** états sont à zéro :
Opel1..5, Opelflak1/2 et la_kubelAf_. Jeep1 ne fait pas partie de ce premier
test. Un second test ajoute Jeep1; détruire tous les moyens d'évacuation peut
échouer la mission. Ne pas exiger le neuvième véhicule pour une phrase parlant
du parc, ni modifier l'objectif ou détruire des véhicules pour rendre la phrase
accessible. Source du contrôleur : 1777 octets, SHA-256
`19d0bdbe5b98775232c7ce8b2bb5fd52281744a707274abd65688e0010401ff9`.

La condition doit être relue **au moment de la réplique**, pas mémorisée au
démarrage du dialogue. Une activation pendant le passage d'un véhicule
d'endommagé à détruit ne doit pas raconter un état encore faux.

## Ressource anglaise prouvée

LangEnglish.dta contient Sounds/53990023.wav, 242896 octets, mono PCM16 à
22050 Hz, **5,506848 s**, SHA-256
`768d89b0fcc7191a270677adfaa053e27bf9bbf16d048555651f7d6afba9cb01`.
Tables/Dabing/53990023.dat : 2216 octets, SHA-256
`c0c8ce1d16a5f3146df5e2c93279237887f72e942b63dd8e4fdaaa186e34ebea`;
la copie SabreSquadron est identique. Les fichiers ont été lus en mémoire,
pas diffusés ni écoutés. Le raccord labial en jeu reste à vérifier.

## Cycle du dialogue à préserver

Proximité 50 du coordinateur → signal 2 à AF2_24 → déplacement AF2_24_03,
rotation vers AF2_25 → retour 2 → séquence 14..24. Les deux soldats envoient
signal 1 pour annuler sur alarme ou mort. AF2_25 peut alors embarquer dans
Opelflak1 : cette action commerciale ne doit pas être retardée par la phrase.

Une variante MODERNE doit ajouter un drapeau de phrase déjà consommée, le
verrouiller avant lancement, vérifier les huit véhicules et les deux acteurs
vivants et conserver l'annulation des deux voix. Les répétitions du signal 2
et la reprise après sauvegarde doivent être mesurées. Une simple ligne If
autour du commentaire ne démontre pas la sécurité de toute cette séquence.

Comparer : parc intact, un seul véhicule restant, huit détruits avec Jeep1
préservée, locuteur mort/alerté avant 23, destruction pendant 22, alarme pendant
23, retour du même signal et sauvegarde à chaque étape. La variante coop ne
sera qualifiée qu'après essais réseau distincts. Aucun nouvel objectif ajouté.
