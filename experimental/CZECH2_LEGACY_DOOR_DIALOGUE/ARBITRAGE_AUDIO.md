# Contrat d'arbitrage audio exclusif

## États modernes

| État | Propriétaire de 19993810/11 | Porte | Cinématique 2 |
| ---: | --- | --- | --- |
| 0 | aucun | peut réclamer | peut réclamer |
| 1 | porte | joue une fois | saute 810/811, conserve 813–815 et toute la scène |
| 2 | cinématique | devient muette | joue la séquence release complète |

La première transition 0→1 ou 0→2 est atomique et persistée. Aucun retour à 0
n'est permis pendant la mission.

## Déroulement

- si la porte gagne, `bigboskecac` joue 810/811 une fois avec son délai
  officiel ; la copie alternative de `cut2` commence ensuite à 813 ;
- si la cinématique gagne, elle joue les cinq voix et désarme définitivement
  la porte ;
- un signal de porte reçu pendant la cinématique ou après elle est ignoré ;
- si le Big Boss est mort, aucun dialogue ne joue et la logique d'échec release
  conserve l'autorité.

## Classification

- signal porte, délai et deux voix : **OFFICIELS, branche ancienne** ;
- cinématique complète : **OFFICIELLE release** ;
- état partagé, exclusion et version de `cut2` sautant deux appels :
  **ARBITRAGE MODERNE** ;
- éventuel indice de journal sans voix : **CRÉATION MODERNE**.

Aucun script `.disabled` n'est fourni avant d'avoir démontré comment partager
l'état entre `doors2`, `bigboskecac` et `cut2` à travers une sauvegarde sans
course réseau ou double callback de cinématique.

