# Collisions de modèles et surcharges de ressources

**27 septembre 2026.** `tools/benelli_asset_preflight.py` complète la gestion
des tables personnelles par un contrôle en lecture seule des ressources.
Il ne choisit pas à la place du moteur un format ou une compression.

## Résultat sur l'installation observée

- **11 archives DTA** inventoriées, sans extraction de leurs contenus dans Git.
- **52 entrées pertinentes** : 34 occurrences des chemins de sources épinglées
  et 18 variantes de textures DX1. Les versions antérieures d'une ressource
  dans les archives restent visibles ; le lecteur de sources vérifie les
  contenus effectifs selon les couches déjà étudiées.
- Aucun fichier libre candidat dans les espaces Models, Maps, Maps_U, Maps_C,
  Sounds et Tables, hors tables centrales traitées séparément.
- Aucune occupation de `PROTOTYPE_BenFPV` ou `PROTOTYPE_BenM4` en I3D, 4DS ou
  5DS dans les archives ou fichiers libres examinés.
- Aucun fournisseur de ressource pertinent dans une archive supplémentaire
  extérieure aux couches déjà relues par les contrôles de sources.

Les 18 textures voisines comprennent les variantes de l'arme, du chargeur,
de l'icône, des douilles, des deux peaux de mains et des manches. Elles sont
**inventoriées et hachées, pas remplacées par les BMP**. Leur priorité et leur
sélection réelle restent à qualifier dans le moteur.

Le rapport privé est `.analysis/benelli-asset-preflight-v2-20260927.json`.
L'empreinte de l'index noms/tailles est explicitement distincte de celle du
contenu complet d'une archive. Les sources utiles sont vérifiées séparément
par leurs propres empreintes de contenu.

## Refus et périmètre

Toute occupation d'un alias moderne, surcharge libre pertinente, source liée,
doublon, archive illisible ou fournisseur non étudié fait échouer le contrôle.
Même une surcharge apparemment identique n'est pas effacée ou écartée
automatiquement. Les deux tables centrales conservent leur
[composition par instantané](SURCHARGES_CENTRALES.md).

Huit tests synthétiques couvrent la casse, les extensions, les formats voisins,
les archives inattendues et les fichiers libres. La portée reste les archives
DTA à la racine et les fichiers directs des six espaces nommés. Ce n'est ni
une preuve exhaustive de tous les mécanismes de chargement, ni une réservation
globale d'identifiant, ni une autorisation d'installation.

```powershell
.\.venv\Scripts\python.exe tools/benelli_asset_preflight.py --game 'D:\Games\Hidden and Dangerous 2' --json-output '.analysis/benelli-asset-preflight-nouveau.json'
```
