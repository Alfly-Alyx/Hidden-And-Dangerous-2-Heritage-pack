# Contenu communautaire : provenance, crédits et distribution

## Community Map Package

Le module facultatif de l'installateur utilise le dépôt public
[ehylla93/had2-cmp](https://github.com/ehylla93/had2-cmp), présenté par ses
mainteneurs comme le *Official Coop Map Package for Hidden & Dangerous 2*.
La version de référence est la CMP 2.6.5, compilée par =RpR= et annoncée comme
publiée le 20 mai 2026. À chaque installation demandée, le Heritage Pack consulte
la branche principale du dépôt officiel afin d’identifier sa dernière révision.

La source est figée sur le commit :

`793d979748b27a9924fccc30fa0fba6edb7cd70f`

Cette révision constitue le repli audité lorsque GitHub n’est pas joignable.
Contrôles associés :

- URL : `https://codeload.github.com/ehylla93/had2-cmp/zip/793d979748b27a9924fccc30fa0fba6edb7cd70f` ;
- taille exacte : `1 084 146 265` octets ;
- SHA-256 : `DD0CA6FED1FB056DCB064813C223E0423F1FD9B13E291D106D8B983C467ABC33` ;
- `23 600` entrées d'archive attendues ;
- `156` entrées de carte dans `cmp_info/cmp_Maplist.txt`.

Si le dépôt publie un commit plus récent, l’installateur télécharge l’archive de
ce commit précis, refuse les chemins dangereux, doublons, racines ou dossiers
inattendus, limite le nombre d’entrées et la taille décompressée, lit la version
annoncée dans le README du paquet et calcule son SHA-256. Le commit, la version,
la taille et l’empreinte réellement installée sont inscrits dans le journal de
restauration. Les modifications locales déjà suivies provoquent l’arrêt de la
mise à jour au lieu d’être écrasées.

Le catalogue source crédite les créateurs mission par mission. Le Heritage
Pack conserve le `README.md` et les fichiers d'information de la CMP sous
`cmp_info` afin que ces crédits accompagnent l'installation. =RpR= est
crédité pour la compilation et la maintenance du paquet ; les cartes restent
attribuées à leurs auteurs respectifs.

## Politique de distribution

Au 15 septembre 2026, GitHub n'identifie aucune licence pour ce dépôt et sa
racine ne contient ni `LICENSE`, ni `LICENCE`, ni `COPYING`. Le fait que
le paquet soit publiquement téléchargeable et que =RpR= explique comment
l'installer ne constitue pas, à lui seul, une autorisation générale de
republication.

En conséquence :

- aucune donnée CMP n'est incorporée à
  `H-D2-Heritage-Pack-Setup.exe` ;
- aucune archive CMP n'est publiée dans le dépôt ou les livrables du Heritage
  Pack ;
- l'utilisateur choisit la case CMP, puis l'installateur récupère directement
  la dernière révision du dépôt officiel ;
- la révision 2.6.5 de référence reste verrouillée par taille et SHA-256 ; une
  révision officielle plus récente est liée à son commit, contrôlée structurellement
  et reçoit une empreinte SHA-256 locale avant installation ;
- l'installation est interrompue si la structure, les dossiers autorisés, les
  limites de taille ou la liste multijoueur ne correspondent pas ;
- une copie locale fournie manuellement n'est acceptée que si elle est
  strictement identique à l'archive épinglée ;
- un futur embarquement exigera une autorisation explicite et vérifiable des
  détenteurs concernés.

Cette règle ne préjuge pas des droits propres à chaque carte. Elle évite
simplement de présenter l'absence de licence publiée comme une permission.

## Sources vérifiées

- [Dépôt CMP officiel](https://github.com/ehylla93/had2-cmp)
- [Page =RpR= pour jouer en ligne et obtenir la CMP](https://www.rprclan.com/hd2/play-online)
- [Guide =RpR= d'installation des cartes personnalisées](https://www.rprclan.com/hd2/install-custom-maps)

## Conditions avant publication finale

- recontrôler que le commit épinglé est toujours accessible ;
- conserver la notice de crédits dans le dossier installé ;
- vérifier que la construction finale n'embarque aucune archive ou donnée CMP ;
- demander une autorisation séparée avant toute redistribution intégrée.
