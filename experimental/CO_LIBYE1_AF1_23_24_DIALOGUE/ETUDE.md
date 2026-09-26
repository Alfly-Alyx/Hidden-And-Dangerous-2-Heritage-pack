# Co-Libye 1 — conversation AF1_23 / AF1_24

État : ressources retrouvées, synchronisation à reconstruire, 26 septembre 2026.
Aucune voix réactivée ni nouveau signal envoyé.

Les deux soldats et `AF1_23_AF1_24_speech` sont liés dans le registre coop.
Les déclencheurs A1/A2/A3 utilisent le script A1 à 6 unités; A4/A5 utilisent A4
à 2 unités. Chacun envoie signal 1 aux deux soldats. **Seul AF1_23** renvoie
signal 1 au coordinateur; AF1_24 se réveille sans accusé de présence.

Le coordinateur incrémente `sync` et démarre seulement à `sync==2`. Un compteur
de deux messages n'identifie pas deux participants : des activations répétées
d'AF1_23 peuvent satisfaire le seuil sans prouver qu'AF1_24 soit prêt. Ajouter
seulement son émission manquante ne protège pas contre les doublons provenant
des cinq volumes. Ne pas modifier ces volumes pour compenser le compteur.

Douze appels 52990012..52990023 sont commentés. Leurs gardes d'état commentées
emploient une expression combinée ambiguë; ne pas la réactiver en supposant
qu'elle équivaut à deux comparaisons explicites avec l'état 1. Le chemin actuel
attend 1000 ms puis renvoie signal 2 aux deux soldats pour leurs patrouilles.
Alarmes et morts des deux soldats envoient déjà signal 2 au coordinateur, qui
arrête les deux voix et termine le script.

## Audio disponible dans l'édition anglaise vérifiée

LangEnglish.dta contient les douze WAV et les douze fichiers
`Tables/Dabing/<id>.dat`, tous lus et empreintés. Durées PCM des WAV, dans
l'ordre 12..23 : 1,642812 / 3,817370 / 4,231837 / 3,532336 / 3,565986 /
3,298639 / 3,111474 / 2,408481 / 1,822766 / 3,633923 / 2,043356 / 3,499501 s.
Présence et durée ne prouvent pas la synchronisation visuelle sur ces acteurs.
Aucune écoute ni validation dans une autre langue n'est revendiquée.

Exemples de preuve : 52990012.wav, 72492 octets, SHA-256
`c6d1d9d0cf37e32d74b67920ecc095e45fe852871479065e1f050bd76f3ea88f`;
son .dat, 672 octets,
`93d63ab577b6c00f1023c0da37c79be36ef60cdde3a1f9810f2987aa57e62aa9`.
52990023.wav, 154372 octets,
`2fda860dece8fee55074120888d056938c960a5f81afd3b68c260b79d6e9d1ee`;
son .dat, 1408 octets,
`b4e5679af72596941b7b048b2d7a510dd33ba8c7b68b63e2151ba49c69b879cb`.

## Contrat moderne minimal

Une variante atomique doit traiter les deux scripts humains et le coordinateur :
une identité distincte par participant, un drapeau de présence par acteur,
un verrou de départ unique, des états vivants vérifiés avant chaque réplique,
une annulation irréversible sur alarme/mort et une seule libération finale de
chaque patrouille. Aucun numéro de signal neuf n'est réservé sans audit du
graphe. Le mode coop impose aussi un seul détenteur de l'autorité audio.

Avant export complet : approche des cinq volumes dans tous les ordres,
doublons d'activation, un soldat absent/mort, alarme pendant chaque réplique,
déconnexion, sauvegarde et contrôle de lèvres/volume sur hôte et clients.
Ne pas remplacer la version coop par le dialogue solo complet.

Sources Sabre : coordinateur 3196 octets,
`a8f9dd95c22a6d8f2b8425b345ac983cdded653f696af4378c6b133661f3bc4c`;
AF1_23 1317 octets,
`0c39f910d7a07f8ce6555905788f7264b9fb2ae6ca9e9a46243dd26919a6c472`;
AF1_24 1253 octets,
`18348a0b629c5a5b597ce41e1147265277e4764ac54b35db0eb772e80bf478a0`.
