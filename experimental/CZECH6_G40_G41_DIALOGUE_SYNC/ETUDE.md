# Czech 6 — anciens signaux de synchronisation du dialogue G40/G41

État du 25 septembre 2026 : **vestige documenté, aucun prototype justifié sans
observation visuelle**. Aucun script commercial, son ou binding n'est modifié.

## Ce qui fonctionne déjà

Les acteurs `C5_G40`, `C5_G41` et le contrôleur `C5_G40_G41_speech` ont chacun
une liaison unique. Les deux humains sont sérialisés dans les acteurs Patch;
le contrôleur est dans `scene2.bin`. Les trois scripts effectifs proviennent de
`Scripts.dta`.

Le contrôleur commence le dialogue lorsque le joueur entre à 22 m. Il utilise
directement `FRM_MorphSpeechDelayed` pour 23994618/16/19/17, puis
`FRM_MorphSpeech` pour 23994620. Après 20 secondes, une boucle alterne la
réplique 19993812 entre les deux acteurs avec des délais de 30 secondes. Cette
séquence est active : les deux anciens signaux commentés ne sont pas requis
textuellement pour lancer ces appels.

G40 et G41 possèdent parallèlement des boucles gestuelles avec les animations
commerciales `%%rozhovor*` et `%%kecy*`. Cela peut être une composition voulue
entre gestes et parole; une recherche de lignes ne démontre pas un conflit
visuel ou une désynchronisation.

## Ce que les deux lignes ne permettent pas de restaurer

Au début du détecteur 22 m, deux `SendSignal(..., 1)` vers G40/G41 sont
commentés. **Aucun des deux scripts acteurs ne possède de récepteur 1.** Les
décommenter seuls ne recrée donc pas un protocole exploitable. Un handler
arrêtant la boucle de gestes serait une création moderne, pas le corps
historique retrouvé.

À l'inverse, les signaux 1 envoyés **par** G40/G41 au contrôleur speech sur
alarme ou mort sont actifs; le contrôleur les reçoit et termine son script.
Ils ne doivent pas être inversés, supprimés ou rejoués. Le garde G40 alerte
aussi G11/G43 sur alarme, mais ni sa mort ni l'alarme de G41 ne font cette
propagation. Ce contrat distinct reste celui de
[l'étude des récepteurs d'alarme](../CZECH6_G11_G43_SIGNALS/PROPOSITION.md).

## Décision et essais requis

Ne pas ajouter de fichier `.scr.disabled` complet pour l'instant : le défaut
à corriger n'est pas démontré. Observer le dialogue commercial à 22 m, les
gestes pendant les cinq répliques initiales et la boucle suivante. Tester
entrée/sortie du rayon, alarme et mort de chacun, puis sauvegarde/reprise.

Si les gestes et la parole se composent correctement, classer les anciens
signaux comme protocole abandonné sans restauration nécessaire. Sinon relever
précisément quel geste, quelle réplique et quelle interruption posent problème
avant de définir un handler moderne. Ne pas supprimer en bloc les animations
ni ajouter une seconde voix pour masquer la désynchronisation.

## Empreintes des sources relues

| Fichier | Octets | SHA-256 |
|---|---:|---|
| `c5_g40_g41_speech.scr` | 1164 | `51964889d720777adc548942ed283840952a5bd069ef5d8f5a4b637b02fe1ca0` |
| `c5_g40.scr` | 1767 | `2b1fcee05eced8ce5c264376dd13d99178a7b89e0c566f10ea4f322cba4e78c3` |
| `c5_g41.scr` | 1701 | `5a6bc8bf9e6d77e31de9ca04b8fbc0cc914f962caa70727460d710877d49ce9a` |

Le registre, les acteurs et la scène sont les mêmes sources épinglées dans
le profil radio Czech 6. Ce renvoi est une provenance commune, **pas une
autorisation de combiner le dialogue, la radio Base et des récepteurs d'alarme**.
