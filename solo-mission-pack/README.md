# Pack personnel de 11 missions solo

Ce constructeur transforme `ALPS3_OBJ`, `ARDENS1_OBJ`, `CO_BREST`,
`CO_BURGUNDY1–3`, `CO_LIBYE1–3` et `CO_SICILY1–2` en missions solo distinctes.
Elles apparaissent dans **Solo > Missions personnalisées > Adaptations
multijoueur** et ne remplacent pas leurs versions multijoueur.

## Construire l'installateur autonome

Depuis la racine du dépôt :

```powershell
.\build-solo-mission-pack.ps1 -GamePath 'D:\Games\Hidden and Dangerous 2'
```

Le résultat est `dist\HD2-Solo-Mission-Pack-Setup.exe`. Il contient les onze
missions complètes extraites de cette installation du jeu : géométrie, acteurs,
navigation, scripts, sons et textes. Il embarque aussi les quatre archives
commerciales qui ont servi à la conversion (`missions.dta`, `Scripts.dta`,
`Patch.dta` et `SabreSquadron.dta`). Une archive absente ou différente est
remplacée par la copie vérifiée embarquée, avec conservation de l'ancienne copie.

L'exécutable ainsi produit contient des données commerciales provenant de la
copie du jeu du constructeur. Il est destiné à son usage personnel et ne doit
pas être publié ni redistribué.

## Garanties de l'installation

- validation de la charge utile avant toute intégration ;
- déploiement transactionnel avec restauration en cas d'échec ;
- conservation des autres missions personnalisées ;
- conservation des missions multijoueur originales ;
- contrôle final des 11 paquets et des 11 missions installées ;
- bouton **Retirer ce pack** qui enlève uniquement ces onze adaptations.

Le jeu de base doit rester exécutable. Ce programme installe les missions et le
menu associé ; il ne constitue pas une réinstallation complète de Hidden &
Dangerous 2.
