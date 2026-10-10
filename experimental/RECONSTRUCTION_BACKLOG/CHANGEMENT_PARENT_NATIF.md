# Retrait de liaison avant changement de parent

Composant original du **10 octobre 2026**, désactivé. Le changement de parent
ne modifie pas le vecteur d'appartenance du modèle : sa notification est donc
distincte des [ajouts, retraits et libérations](NOTIFICATIONS_CYCLE_VIE_NATIVE.md).
Elle utilise **le même état de garde et le même registre compilé**, dans le
processeur privé. Aucun dispositif n'est installé dans le jeu.

## Comportement réalisé

`Hd2BeforeHandParentChange` retire la liaison si l'objet déplacé **ou sa nouvelle
destination** est le modèle surveillé ou l'un de ses nœuds. Une destination nulle
est un détachement valide. Une demande ne changeant finalement pas le parent
retire également la liaison, par prudence. Les événements étrangers sont neutres.
L'événement enregistré vaut quatre ; générations et compteur d'invalidation
restent partagés avec la garde d'appartenance, sans bouclage du compteur.

La dérivation privée de `1001d680` remplace six octets couvrant trois instructions
entières. Elle appelle la garde, restaure l'état puis rejoue le prologue natif,
y compris son alignement de pile. Les registres, indicateurs et champs x87 sont
contrôlés avant ce prologue ; ses propres effets sont vérifiés séparément.
Un refus arrête le banc avant toute mutation native. Comme pour les premières
dérivations, cet arrêt diagnostique `UD2` n'est **pas** une gestion de refus
acceptable dans un client réel.

## Vérifications privées

- Deux arbres de onze et 128 nœuds, avec vecteurs de modèle préalloués.
- **16 reprises de prologue**, deux détachements occupés arrêtés, changement
  étranger, rattachement d'un objet étranger sous un nœud surveillé, détachement,
  restauration, demande sans effet et déplacement du modèle surveillé lui-même.
- Cinq générations partagées par scénario : le dernier réarmement est retiré
  par un véritable ajout natif, via la dérivation déjà réalisée.
- Liens parent / premier enfant / frère et indicateurs comparés à une référence
  indépendante ; appartenance, références, noms, poses et gardes mémoire intacts.
- **34 contrôles directs de garde**, dont seize refus. Pendant les notifications,
  toutes les pages d'objets natifs sont inaccessibles au processeur : seules les
  identités et les vues possédées sont nécessaires.
- Image native et registres intégralement restaurés ; treize tests unitaires
  publics couvrent les forêts inventées et les refus avant exécution.

Les chemins natifs exécutés utilisent les indicateurs **0 et 2** : pas de
conservation de transformation mondiale, pas de rafraîchissement immédiat, pas
de notifications de scène. La garde ne dépend pas de ces indicateurs, mais ces
autres chemins natifs ne sont pas qualifiés ici. Les cycles sont refusés par
l'appelant du banc ; cela ne démontre pas une détection de cycle par le moteur.

Le contrôle à 128 nœuds a d'abord atteint la limite de temps du collecteur.
Le routage de surveillance a été allégé sans changer le budget ni les contrôles
du collecteur ; la reconstruction suivante passe. Le premier répertoire privé
incomplet est conservé, et n'est pas un résultat valide.

## Reproduction et suites

`tools/build_native_hand_parent_hooks.py --output-name HandParentHooks_Compiled_v2`,
destination neuve, avec `--library`, `--compiled-collection`, `--compiled-hook`
et `--compiled-lifecycle` vérifiés. Manifeste privé sous
`.analysis/modern-assets/HandParentHooks_Compiled_v2/`.

Image originale de 2 560 octets, sans import système et refusant l'initialisation
par chargement Windows ordinaire. SHA-256 :
`17716a5576e4d1a783d8ec9294a0432810240ebace1d606d6186ac1cba821573`.

Il reste à traiter la conservation mondiale, les autres branches de scène,
la gestion de refus réelle, la reconnaissance des ressources autorisées et le
remplacement / la destruction complets. Les allocations restent fournies par
le banc ; aucune correction de pose n'est exécutée dans ce scénario de durée
de vie, aucun allocateur ou destructeur n'est appelé, aucun jeu n'est modifié.
