# État de préparation de la branche

Date : **2026-09-19**

Branche : `codex/experimental-reconstruction-inventory`

Base commerciale du dépôt : commit `8e1aefa` (`Fix README language links`)

## Conclusion

La branche est prête à commencer un futur travail de reconstruction. Aucun cas
de mission, prototype ou installateur n'a été implémenté dans cette préparation.
Les seuls ajouts sont l'inventaire, les références, les instructions et
l'environnement d'outils reproductible.

## Vérifications réussies

- Git 2.52.0, PowerShell 7.6.5 et Python 3.14 disponibles;
- compilateurs C# .NET Framework 4 32 et 64 bits disponibles;
- installation commerciale 1.12 et onze archives DTA principales détectées;
- environnement `.venv` créé et ignoré par Git;
- Pillow 12.3.0, ReportLab 5.0.1 et Unicorn 2.1.4 installés;
- 30 interfaces de ligne de commande chargées avec `--help` sans erreur;
- registre d'exécution structurellement valide : 56 scénarios, tous encore
  honnêtement marqués `pending`;
- baseline solo statique : 33 missions sur 33;
- conversion multijoueur vers solo : 21 candidates commerciales et zéro
  conversion revendiquée comme validée;
- scan de l'ID d'objet 359 : aucune collision parmi 149 573 enregistrements et
  7 135 déclarations de catalogue, avec avertissements de conteneurs dégradés
  conservés; ce résultat doit être rescanné avant toute intégration;
- liens Markdown locaux du registre résolus;
- aucun script `.scr` actif ajouté par la préparation.

## Contenu fourni pour démarrer

- inventaire thématique des missions et systèmes;
- catalogue des 134 dossiers expérimentaux existants;
- règles de preuve et de reconstruction additive;
- carte des outils, exemples de commandes et procédures d'audit;
- manifeste lisible et verrou exact des dépendances Python;
- script de création de l'environnement isolé;
- critères statiques, tests en jeu et conditions de promotion;
- références internes, commerciales et externes déjà connues.

## Ce qui reste volontairement non exécuté

- aucun prototype activé ou déployé;
- aucune archive commerciale modifiée;
- aucun build de l'installateur lancé;
- aucun scénario manuel marqué réussi;
- aucune conversion solo annoncée;
- aucun des travaux locaux préexistants ajouté au commit de cette branche.

## Premier geste lorsque le travail sera autorisé

Choisir un seul identifiant du registre, relire son dossier existant, capturer
la baseline commerciale et ouvrir une étude locale sous
`experimental/<IDENTIFIANT>/`. L'installateur et les scripts actifs restent hors
scope jusqu'à validation séparée.
