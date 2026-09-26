# Africa 4 — transition radio et rythme de l'invasion

État : delta historique désactivé, composition à valider, 25 septembre 2026.

## Séquence effective

`AF3b_organizer.scr` Patch (3997 octets, SHA-256
`46bf3adc728550785c65095201720468692360d1b72818d4c87a488d9f41744d`)
est lié à `dummy_organizer`, présent dans `scene2.bin`. Le `Whenever radio_used`
sur l'état 2 de la radio saute à `GOOO`. Les trois appels de transition visuelle
avant ce saut sont commentés. `GOOO` active `S_invaze`, calcule l'espacement
des groupes puis envoie immédiatement l'ordre au premier conducteur Opel.
Un `Delay(20000)` commenté précède cet ordre.

Après cet ordre, le script attend 10000 avant le second tankiste, puis 20000
avant le premier groupe à pied. Ces attentes sont actives et **distinctes**
de la pause initiale dormante. Les autres groupes et véhicules conservent leurs
propres attentes. Ne pas ajouter deux fois une pause de 20 secondes.

## Composition avec Heritage

La source commerciale charge la valeur de campagne 20 puis force `odvysilali=1`.
Le module existant
[`Africa4RadioConsequenceInstaller.cs`](../../installer/Africa4RadioConsequenceInstaller.cs)
retire ce forçage et contrôle les deux branches : conducteurs 20/21, soldats 1/2,
espacement 30000/20000. Ce travail est déjà réalisé dans Heritage; la variante
de rythme ne doit ni le remplacer ni réintroduire le forçage.

Le [fragment](DELTA_TRANSITION.scr.disabled) indique seulement les deux sites
historiques à décommenter. Ce n'est pas un script complet. La composition future
doit appliquer le même delta à une baseline commerciale **ou** Heritage vérifiée,
en conservant son choix radio initial. Ces baselines ne sont pas interchangeables.
Le générateur actuel n'accepte que les archives commerciales : aucun export
complet n'est proposé ici comme remplacement compatible de Heritage.

Ne pas cumuler cette expérience avec
[l'assaut de proximité](../AFRICA4_PROXIMITY_ASSAULT_VARIANT/ETUDE.md), qui déplace
l'autorité des signaux vers dix fantassins. Une fusion éventuelle serait une
troisième expérience, avec sa propre trace de référence.

## Contrôles à effectuer

1. Tracer séparément le témoin commercial et le témoin Heritage, valeurs 20=0/1,
   radio utilisée une fois, réutilisée et sauvegardée autour du déclenchement.
2. La variante doit conserver exactement destinataires, valeurs et ordre des
   signaux; seul le début est retardé. Le nombre d'émissions n'augmente pas.
3. Mesurer fade-out, pause 1000, fade-in et son `S_invaze`. Les appels de fondu
   ne sont pas supposés bloquants sans observation : ne pas annoncer une durée
   totale exacte en additionnant naïvement leurs arguments.
4. Vérifier qu'un fondu d'une autre cinématique, une interruption ou la reprise
   ne laisse pas l'écran noir et ne réarme pas l'assaut.

Aucun verrou moderne, signal, objectif ou valeur de sauvegarde n'est inventé
pour contourner ces essais; la version commerciale reste disponible par défaut.

## Script complet du 26 septembre 2026

`africa4-invasion-transition` reconstruit maintenant le script complet depuis
la source Patch épinglée : 3997 → 3989 octets, quatre préfixes `//` retirés,
aucun autre octet changé. Le registre, les acteurs et `dummy_organizer` dans
la scène sont vérifiés. La fermeture de mission native est complète.

La paire compare **commercial contre commercial + transition**. Elle conserve
donc volontairement le forçage `odvysilali=1` présent dans ce témoin. Elle ne
doit pas remplacer le script Heritage dans l'installation personnelle. La
composition avec la conséquence radio Heritage reste une expérience distincte
à préparer; ce lot ne la déclare pas résolue ni testée.
