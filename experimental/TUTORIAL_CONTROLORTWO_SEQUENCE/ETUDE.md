# Étude expérimentale — séquence perdue de `ControlorTwo`

État : protocole ancien partiellement lisible, chaîne active absente,
14 septembre 2026. Aucun handler ni binding n'est proposé à l'intégration.

## Verdict

Le registre lie bien l'acteur `ControlorTwo` à `TUT_Piker_1.scr`, un simple
script de garde sans réception de signal. Aucun `TUT_ControlorTwo.scr` n'est
présent. `TUT_dummy_pike1in` est lui aussi lié et ses signaux 1/2 sont donc des
no-op dans la mission courante.

Un second ensemble de fragments subsiste, mais il n'est plus actif :

- `TUT_dummy_pike1in` envoie 1 à l'entrée du joueur ou du Jeep dans la zone,
  puis 2 à leur sortie ;
- le fichier **non lié** `TUT_Driver.scr` attend 4 pour s'arrêter et 5 pour
  reprendre sa route, puis renvoie 4 à `ControlorTwo` avant de franchir
  `Jeep_21` et de descendre.

Il ne manque donc pas un saut unique mais un automate de barrière/jeep complet.
Les numéros de protocole sont attestés ; le corps qui transforme 1/2 en 4/5 et
consomme le retour 4 a disparu, tout comme le binding de l'acteur conducteur.

## Fragments conservés

`TUT_dummy_pike1in` possède deux paires de détecteurs, pour le joueur et le
Jeep : entrée à 8/15 unités, sortie à 10/15 unités. Les deux sources utilisent
les mêmes signaux 1/2, ce qui indique que le contrôleur suivait l'occupation de
la zone, pas l'identité de l'objet.

Le pilote vestigial expose une séquence très lisible :

```text
OnSignal(4) { HUMAN_Drive("", 0); }
OnSignal(5) {
  HUMAN_Drive("Jeep_20", 10);
  SendSignal(ControlorTwo, 4);
  HUMAN_Drive("Jeep_21", 10);
  ... descente et suite du tutoriel ...
}
```

Une correspondance possible serait : entrée 1 → demander l'arrêt du pilote par
4 ; sortie 2 → autoriser la reprise par 5 ; retour 4 du pilote → fermer la
phase. Cette table reste une **INFÉRENCE DE CONCEPTION**, car aucun émetteur
survivant de 4/5 n'existe et le récepteur conducteur n'est pas attaché.

`TUT_Piker_1.scr` ne conserve que les checkpoints de garde `CAG_1` et `CAG_2`.
La table de checkpoints contient aussi `CAG_3`, `_4` et `_5`, inutilisés par les
scripts retrouvés. Ils peuvent appartenir au contrôleur perdu, mais ne donnent
ni ordre, ni animation, ni condition.

Les checkpoints `Jeep_01` à `Jeep_21` et `Driver_00` subsistent aussi, mais les
frames `TUT_speech1` et `Private_1..3` référencées par le script vestigial ne
sont pas liées dans le registre. Attacher seulement `TUT_Driver.scr` créerait
donc de nouvelles ruptures au lieu de restaurer une route autonome.

`T_dummy_gate_in.scr` déclare `ControlorTwo`, le premier instructeur et
`F_tut_vrata01`, mais son cutscene est vide et il n'envoie aucun signal. La
scène ne livre qu'un objet `Zavora1.Cylinder01`; aucune seconde barrière nommée
n'a été retrouvée. Ces stubs confirment une suppression plus large et interdisent
d'inventer une `Zavora2`.

## Comparaison avec `ControlorOne`

`TUT_ControlorOne.scr` montre les catégories de comportement attendues d'un
contrôleur : référence à la barrière, état de conducteur, dialogues, ronde de
garde et gestion de mort. Il ne peut pas être copié : ses checkpoints, son
dialogue et ses signaux appartiennent à l'autre phase. De plus, même ce script
survivant ne satisfait pas toutes les mentions « received from ControlorOne »
du pilote, signe que l'architecture des deux postes a été partiellement élaguée.

## Recherche de versions

Une seule version Tutorial est présente dans les couches commerciales
extraites. Les corpus de démonstration locaux ne contiennent pas de variante du
tutoriel. Le CMP public 2.6.5 ne réemploie aucun de ces noms dans sa mission
`GREAT_BATTLE`; aucune autre version locale de `TUT_Piker_1.scr` n'est présente.

## Reconstruction autorisable ultérieurement

Une maquette moderne devrait d'abord recréer un acteur conducteur réellement
lié et valider toutes ses frames, puis posséder au minimum trois états — libre,
Jeep arrêté, reprise envoyée — et dédupliquer les entrées simultanées
joueur/Jeep. Elle devrait aussi décider, source à l'appui, qui actionne la
barrière et comment les checkpoints CAG_3–5 sont employés. Sans ces éléments,
même un automate qui envoie correctement 4/5 pourrait bloquer le Jeep, fermer
la barrière sur le joueur ou déclencher deux reprises.

**Aucun prototype exécutable.** La table 1→4, 2→5, 4→fin est conservée comme
spécification expérimentale à tester seulement après récupération d'une source
ou observation instrumentée de la scène.

## Sources internes

- `.analysis/tutorial/base/MISSIONS/TUTORIAL/Scripts.dta`
- `.analysis/tutorial/base/MISSIONS/TUTORIAL/check2.bin` et `scene2.bin`
- `.analysis/binding-tutorial-check.json`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_dummy_pike1in.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_Piker_1.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_Driver.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/TUT_ControlorOne.scr`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/T_dummy_gate_in.scr`
- CMP public 2.6.5, commit `793d979748b27a9924fccc30fa0fba6edb7cd70f`
