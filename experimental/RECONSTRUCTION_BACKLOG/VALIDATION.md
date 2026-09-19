# Validation et critères de promotion

## Contrôles statiques obligatoires

- Aucun fichier expérimental exécutable ne doit porter l'extension active `.scr`.
- Tous les liens Markdown locaux doivent résoudre vers un fichier existant.
- Chaque propriétaire ajouté doit avoir une frame, une transformation, une
  liaison de script et un cycle de vie documentés.
- Chaque signal ajouté doit avoir un émetteur, un récepteur et une sémantique
  locale démontrés.
- Les labels, checkpoints, sons, animations et particules doivent être présents
  dans la variante de mission ciblée, pas seulement dans une mission voisine.
- Aucun binaire commercial extrait, aucune archive de jeu et aucun fichier de
  sauvegarde ne doit entrer dans Git.

## Contrôles d'exécution minimaux

Pour chaque variante activable :

1. chargement à froid et depuis sauvegarde;
2. chemin commercial inchangé quand le profil expérimental est désactivé;
3. chemin expérimental complet sans boucle infinie ni blocage de cutscene;
4. objectifs, compteurs et conditions de fin inchangés sauf modification
   explicitement étudiée;
5. aucun double son, double signal, double téléport, double acteur ou double
   récompense;
6. interruption par alarme, mort du propriétaire, changement de secteur et fin de
   cutscene;
7. essai dans chaque mode disponible : solo, Carnage et coopération;
8. désinstallation ou retour au profil commercial sans sauvegarde corrompue.

## Cas particuliers

### Dialogues et sons

- Confirmer WAV, synchronisation labiale et texte localisé avant de qualifier une
  ligne d'officielle.
- Si le son existe sans texte retrouvé, garder le texte moderne explicitement
  marqué et optionnel.
- Rendre les déclencheurs idempotents quand une cutscene et un signal direct
  peuvent viser le même son.

### IA, postures et animations

- Ne pas employer une animation nommée seulement parce qu'elle apparaît dans un
  commentaire.
- Tester retour alarme, interruption, mort, arme en main et sortie de véhicule.
- Fournir un profil moderne minimal quand la pose historique est invérifiable.

### Véhicules et routes

- Vérifier rayon de braquage, hauteur, collision, passagers, vitesse et ordre des
  checkpoints.
- Ne pas recréer un checkpoint `???` ou vide sans preuve géométrique enregistrée.

### Effets et lightmaps

- Tester un seul propriétaire à la fois, puis comparer capture A/B et coût en
  boucle.
- Refuser les boucles sans délai et les groupes lightmap sans propriétaire
  sérialisé.

### Conversion multijoueur vers solo

- Les quatre validations menu/apparition/objectifs/fin sont indivisibles.
- Une validation doit enregistrer mission, mode, profil, date, résultat et preuve
  reproductible.

## Passage de `.disabled` à une intégration distribuable

Un prototype ne peut être promu que si :

- toutes ses preuves sont classées et reliées;
- le propriétaire et les ressources sont résolus;
- le profil commercial reste le défaut;
- les tests statiques et d'exécution ci-dessus sont réussis;
- le dossier explique la désactivation et le retour arrière;
- une relecture vérifie qu'aucun faux positif déjà fermé n'a été réintroduit.

Tant qu'un point échoue, le fichier reste une étude ou un prototype désactivé.
