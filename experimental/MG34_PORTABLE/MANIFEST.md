# Manifeste — MG34_PORTABLE

## OFFICIEL

- objet 201 : `Ammunition - MG 34` ;
- icônes et sons MG34 présents dans les archives ;
- objet 211 : `Ammunition - MG 34 - tank version` ;
- MG34 monté/TANK actif, à préserver comme chaîne distincte.
- ligne 32 de `item_shoot.tbl`, 135 octets aux offsets 4656–4791 ;
  sémantique de tir encore non qualifiée, slot natif 32 réutilisé par un casque.

## DÉRIVÉ / INFÉRÉ

- une version portative a existé au catalogue ;
- aucune ressource montée ne prouve son apparence ou ses paramètres portables.

## CRÉATION MODERNE REQUISE

- modèle extérieur/sol : [fabriqué](MODELE_MODERNE.md), tenue et moteur non validés ;
- [neuf animations originales de pièces construites](../RECONSTRUCTION_BACKLOG/ANIMATIONS_MODERNES.md), sans mains ni liaison moteur ;
- [modèle et clips FPV rigides construits](../RECONSTRUCTION_BACKLOG/BANQUES_FPV_RIGIDES.md), sans mains, cadrage ni copie moteur qualifiés ;
- [banques de mains privées et associations construites](../RECONSTRUCTION_BACKLOG/MAINS_ARMES_RIGIDES.md) ; prises, trajectoire de sortie et coudes ajustés sans qualification moteur ;
- [descripteur Weapon, textes et tables additives privées construits](DESCRIPTEUR_ET_TABLES.md) : munition portative 201, sons 34/38, alias courts et retrait exact ; aucune activation ;
- cadrage FPV ; gestes de recharge ; animations de personnage ; intégration Weapon en jeu ;
- alimentation, cadence, recul, dispersion, dégâts, bipied et rechargement ;
- mapping sonore vérifié ; inventaire, IA, sauvegarde et réseau.

## INTERDIT

- remplacer ou renommer le TANK MG34 ; partager implicitement son ammo/acteur ;
- annoncer une restauration à partir des seules munition/icônes/sons.
