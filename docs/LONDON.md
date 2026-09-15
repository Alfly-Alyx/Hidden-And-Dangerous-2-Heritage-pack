# Londres, l'Angleterre et la carte Poland

## Conclusion

Deux histoires différentes ont souvent été confondues :

1. une campagne ou des missions en Angleterre, avec Londres parmi les lieux annoncés avant la sortie ;
2. le dossier multijoueur London_mp, achevé par Sabre Squadron et affiché sous le nom Poland.

Les archives prouvent le second point. Elles ne prouvent pas que l'arène Poland soit la totalité, ni même la carte exacte, de la campagne anglaise annulée.

## La campagne annoncée

En mars 2001, Gameswelt rapporte 24 missions dans sept campagnes et cite
l'Afrique, la Birmanie, Londres, la Normandie et l'Allemagne parmi les lieux.
Il faut conserver cette formulation : l'article ne donne pas les sept noms de
campagne et ne permet donc pas d'affirmer que chaque lieu formait à lui seul une
campagne.

La preview Games.cz du 7 juin 2003 donne ensuite le chaînon chronologique le
plus précis. Elle attribue la refonte du concept au départ de Tomáš Pluhařík et
d'autres membres de l'équipe à l'automne 2001. Elle annonce encore un
« Londres en ruines », mais affirme séparément que la campagne située en
Angleterre ne figurera plus dans la version finale, qu'elle sera remplacée par
une campagne alors non nommée et qu'un environnement britannique pourrait
subsister dans au moins une carte multijoueur.

En septembre 2003, à un mois de la sortie, GameSpot ne compte plus que six
campagnes et 23 missions. La preview décrit de grandes cartes, des objectifs
successifs et plusieurs approches, sans citer Londres. Les nombres de campagnes
annoncés ont donc varié de sept à neuf puis six selon les dates et les sources :
ils documentent la refonte, mais ne permettent pas de calculer un nombre exact
de campagnes coupées.

| Date | Source | Ce qu'elle atteste | Limite |
|---|---|---|---|
| 9 mars 2001 | Gameswelt | 24 missions, sept campagnes ; Londres et Allemagne parmi les lieux | liste de lieux incomplète, pas sept campagnes nommées |
| archive GameSpot de la première conception | entretien Thomas Pluharik | personnage principal, objectifs dépassant deux ou trois actions, arc de trois missions avec M. Murrau | page republiée plus tard ; aucun lien direct donné avec Londres |
| 7 juin 2003 | Games.cz | refonte après 2001, Gary Bristol ancien concept, Londres en ruines, campagne anglaise remplacée, reliquat multijoueur britannique envisagé | ne nomme pas la campagne de remplacement |
| 25 septembre 2003 | GameSpot | six campagnes, 23 missions, grandes cartes à objectifs successifs et plusieurs approches | état presque final, Londres n'est plus cité |
| 7 octobre 2004 | GameSpot, Petr Miksa | Poland est l'une des trois nouvelles cartes deathmatch de Sabre Squadron | ne dit pas que Poland est une mission solo Londres récupérée |

Sources contemporaines :
- https://www.gameswelt.de/hidden-dangerous-2/news/interview-mit-dem-chef-designer-61828
- https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655
- https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/
- https://www.gamespot.com/articles/hidden-and-dangerous-2-preview/1100-6030857/
- https://www.gamespot.com/articles/qanda-hidden-and-dangerous-2-sabre-squadron/1100-6109875/
- https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf

L'archive officielle contient en plus quatorze scripts sous le nom ENGLAND. Ils décrivent gardes, sniper, appels au secours, otage et détecteurs de tranchée. Il manque toutefois la géométrie, les acteurs de mission, les objets, les sons, les collisions et un briefing complet correspondant. C'est un prototype de logique, pas une campagne récupérable telle quelle.

## London_mp dans le jeu de 2003

Le dossier MISSIONS\LONDON_MP contient neuf ressources, dont une scène et un arbre de collision, mais pas les éléments nécessaires à une partie multijoueur complète. Il n'est pas déclaré dans la liste finale du jeu de base.

La ville en ruines est visible dans l'introduction, ce qui a entretenu le nom
London auprès des joueurs. Le fait que Games.cz prévoie encore en juin 2003 un
reliquat multijoueur britannique, alors que la campagne anglaise était déjà
annoncée comme supprimée, rend plausible que `London_mp` soit ce reliquat.
Il s'agit d'une inférence chronologique, pas d'une preuve d'identité avec une
mission solo.

## Poland dans Sabre Squadron

Sabre Squadron réutilise le même dossier interne London_mp et le complète :

- scène et collision enrichies ;
- volumes de jeu ajoutés ;
- données multijoueurs complètes ;
- déclaration visible name="Poland" dir="London_mp".

L'entretien GameSpot de Petr Miksa du 7 octobre 2004 confirme en plus Poland
comme carte deathmatch officielle de Sabre Squadron. La carte livrée est donc
bien la version achevée de ce dossier multijoueur. Le maintien du nom interne
évite de casser les références. Il ne suffit pas à démontrer que le décor
représente encore Londres dans l'intention finale.

## Degré de preuve

- **Certain** : une campagne anglaise a été annoncée puis retirée ou remplacée
  avant la sortie ; un Londres en ruines et un reliquat multijoueur britannique
  étaient encore évoqués en juin 2003.
- **Certain par les archives commerciales** : `London_mp` est incomplet dans
  le jeu de base, puis complété et déclaré sous le nom Poland dans Sabre
  Squadron.
- **Plausible** : `London_mp` correspond à la survivance multijoueur évoquée
  par Games.cz.
- **Non démontré** : Poland serait la carte intégrale d'une mission solo
  londonienne, Gary Bristol y aurait eu un rôle, ou les quatorze scripts
  `ENGLAND` auraient été écrits pour ce décor.

## Décision de restauration

Le paquet garde Poland, déjà achevée et active. Il n'ajoute pas un doublon London.

Une mission solo dans ce décor reste possible comme création communautaire. Elle devra être présentée comme une adaptation moderne, sauf découverte future d'une build contenant objectifs, acteurs, dialogues et briefing d'origine.

Pour la campagne Angleterre/Londres, la voie raisonnable est d'abord de reconstruire un dossier historique et une démonstration séparée, puis de signaler clairement chaque partie inventée.
