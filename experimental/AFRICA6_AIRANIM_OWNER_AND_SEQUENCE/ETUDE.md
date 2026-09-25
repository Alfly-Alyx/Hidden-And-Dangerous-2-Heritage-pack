# Africa 6 — animations aériennes et propriétaire retrouvé

État : ressources et hiérarchie retrouvées, concurrence moteur à établir,
26 septembre 2026. Aucun script lié ou réactivé.

## Correction du constat initial

`AF5_airanim.scr` est libre et saute à END avant six appels
`FRM_SetAnimationDelayed(this, "#aircraftN.I3D", 0)`. Patch.dta : 786 octets,
SHA-256 `e917662e5a056ef2b10646515ea332347d371309faf94cf84a4089f9d510a92f`.
La fermeture compte 13 racines, 17 scripts accessibles et 19 disponibles,
sans manquant; airanim n'est pas accessible.

L'affirmation « aucun propriétaire/modèle » est trop forte :

- scene2.bin contient un modèle `#aircraftdum` de type 9, transformation
  d'instance identité, ressource `#aircraftdum`;
- `MODELS\#aircraftdum.4ds` existe : un nœud dummy `airdummy`, type 6,
  zéro matériau, aucune animation déclarée, 109 octets;
- le modèle **ju88 déjà actif** référence comme parent
  `#aircraftdum.airdummy` dans actors.bin et utilise `la_Ju88High`.

Ce dernier nom dans actors.bin est une **référence de parent**, pas un nouvel
acteur autonome à dupliquer. La hiérarchie fournit un candidat historique
fort pour le support d'animation; elle ne prouve pas à elle seule que le script
airanim devait être lié à la racine, au nœud ou à l'avion.

## Six couples de ressources officiels

Dans models.dta, `#aircraft1..6.4ds` font chacun 109 octets : un nœud `airdummy`,
type 6, zéro matériau, indicateur d'animation 1. Les six `.5DS` correspondants
existent : 14143, 28855, 28855, 28855, 28855 et 15767 octets. Ce sont des
supports/pistes, pas six géométries d'avion manquantes. Les références I3D du
script et les ressources 4DS/5DS doivent encore être vérifiées en moteur.

Leurs positions initiales sont distinctes; la continuité et la durée des pistes
5DS ne sont pas déduites de leur taille. Six appels portant un délai 0 ne
prouvent ni six animations simultanées ni une file séquentielle : mesurer la
sémantique de la primitive avant de supprimer le saut initial.

SHA-256 du support `#aircraftdum.4ds` :
`8f524abd87ffd3b03c7d15e2a06319bb1e44606d628b503eafe00f74f43fd839`.
Empreintes 4DS 1..6 :

```text
532ff8faa616bd413f5410a0d891a3ebc2db4a5f2eac0d01124c01788e1a3715
ac9740c0f82b391e1bddc8b7fcf2fe65456dde196378dd3865b4edb0bfa5c934
1abd414df20709787cd7ebc6fd5be7fc875bd9f68f398b2876c954be90798e1b
415ac721faa345f6c8ca30b13e59019ae47ddfa8c4abb92ba158a6d590a5156d
115091139b8dbf3512292ddad68f6654a5007ff4e7acd6e28fe944e5d0baf459
e2a38dba882c57be9cdd7f2c3cd785ddbf9f5354ea1a0d3304b0625cf6ffdba8
```

## Pourquoi aucune activation dans la mission commerciale

Le contrôleur lié `AF5_obj` appelle déjà `SetupJunkers88(diff,100)`, allume ju88
et lui donne l'état 5/6/7 selon la valeur de campagne 40. Il valide aussi
l'approche à moins de 500 unités. Le script lié `AF5_ju88` gère la cinématique
31 et la fin de l'objectif. Une animation supplémentaire sur le parent peut
donc déplacer l'avion **déjà piloté par cette chaîne native**, pas ajouter un
décor indépendant. Il faut observer ce propriétaire effectif avant tout delta.

Sources Patch.dta : AF5_obj, 1399 octets, SHA-256
`5e97435d62ead169585065351bc2778060ce28b1332187a0dbd8e940c24e10a8`;
AF5_ju88, 688 octets, SHA-256
`0dde14455c6663bfe0fda3c4bb9d872da48ab974e3b4061c15d273c258042e73`.
Sources missions.dta : scene2.bin, 3240723 octets, SHA-256
`1e44128df8f7036e644814758500a064ee9d698cc71b2ddf2ff3b473e5678dc3`;
actors.bin, 1531 octets, SHA-256
`c6cf9ee6994e83f83cd93e9a646eaba20ca57132768e096ea100638063cb2d10`.

## Prochaine expérience

Dans le [laboratoire décoratif](../AIRCRAFT_DECOR_LAB/ETUDE.md) isolé : un support
et une piste à la fois, enfant visuel explicitement moderne, aucune invocation
de SetupJunkers88, aucun objectif commercial. Vérifier espace local/global,
continuité, arrêt et sauvegarde avant d'enchaîner les six pistes. Cette sonde
n'est pas encore construite : le laboratoire impose d'abord son contrôle
positif et son chargement local. La mission Africa6 reste intacte.
