# Londres, l'Angleterre et la carte Poland

## Conclusion

Deux histoires différentes ont souvent été confondues :

1. une campagne ou des missions en Angleterre, avec Londres parmi les lieux annoncés avant la sortie ;
2. le dossier multijoueur London_mp, achevé par Sabre Squadron et affiché sous le nom Poland.

Les archives prouvent le second point. Elles ne prouvent pas que l'arène Poland soit la totalité, ni même la carte exacte, de la campagne anglaise annulée.

## La campagne annoncée

En mars 2001, Gameswelt rapporte 24 missions dans sept campagnes et cite Afrique, Birmanie, Londres, Normandie et Allemagne. La preview Games.cz de juin 2003 décrit ensuite une refonte importante du projet après le départ du concepteur principal, une intrigue autour de Gary Bristol et une Angleterre supprimée ou remplacée.

Sources contemporaines :
- https://www.gameswelt.de/hidden-dangerous-2/news/interview-mit-dem-chef-designer-61828
- https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655
- https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/
- https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf

L'archive officielle contient en plus quatorze scripts sous le nom ENGLAND. Ils décrivent gardes, sniper, appels au secours, otage et détecteurs de tranchée. Il manque toutefois la géométrie, les acteurs de mission, les objets, les sons, les collisions et un briefing complet correspondant. C'est un prototype de logique, pas une campagne récupérable telle quelle.

## London_mp dans le jeu de 2003

Le dossier MISSIONS\LONDON_MP contient neuf ressources, dont une scène et un arbre de collision, mais pas les éléments nécessaires à une partie multijoueur complète. Il n'est pas déclaré dans la liste finale du jeu de base.

La ville en ruines est visible dans l'introduction, ce qui a entretenu le nom London auprès des joueurs.

## Poland dans Sabre Squadron

Sabre Squadron réutilise le même dossier interne London_mp et le complète :

- scène et collision enrichies ;
- volumes de jeu ajoutés ;
- données multijoueurs complètes ;
- déclaration visible name="Poland" dir="London_mp".

La carte livrée est donc bien la version achevée de ce dossier multijoueur. Le maintien du nom interne évite de casser les références. Il ne suffit pas à démontrer que le décor représente encore Londres dans l'intention finale.

## Décision de restauration

Le paquet garde Poland, déjà achevée et active. Il n'ajoute pas un doublon London.

Une mission solo dans ce décor reste possible comme création communautaire. Elle devra être présentée comme une adaptation moderne, sauf découverte future d'une build contenant objectifs, acteurs, dialogues et briefing d'origine.

Pour la campagne Angleterre/Londres, la voie raisonnable est d'abord de reconstruire un dossier historique et une démonstration séparée, puis de signaler clairement chaque partie inventée.
