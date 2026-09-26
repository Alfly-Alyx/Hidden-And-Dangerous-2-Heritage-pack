# Parcours natif des 500 emplacements — preuve hors moteur

**27 septembre 2026.** Le module original `tools/item_table_oracle.py` fait
exécuter la boucle commerciale de lecture des objets dans l'émulateur privé,
sur les tables Sabre/PatchX01 et leurs variantes Benelli désactivées.

La version du client et de l'image privée est verrouillée par les mêmes
empreintes que le [contrat natif des descripteurs](CONTRAT_NATIF.md). Aucun code
commercial, exécutable décompacté ou tableau extrait n'est ajouté au dépôt.

## Périmètre exact

- Départ **0x7dca3c**, après lecture du fichier ; arrêt **0x7dcb00**, avant
  libération du tampon. L'ouverture, les appels système, les chemins d'erreur,
  l'interface et le nettoyage natifs ne sont pas exécutés.
- La **boucle originale**, les trois constructeurs et les lecteurs des
  descripteurs s'exécutent réellement en émulation. Les allocations sont
  remplacées par une arène privée bornée à **262 144 octets** ; aucun accès à
  un processus Windows n'a lieu.
- À chacun des 500 passages, comparaison de l'identifiant, du curseur source,
  de la case de destination et de la borne avec le lecteur indépendant.
- Après la boucle, contrôle de chaque pointeur vide et de chaque objet vivant :
  classe, identifiant, membres, noms et octets des descripteurs d'action.
- Le tampon source est mappé en lecture seule, son dernier octet au bord de
  la zone mémoire. Comparaison finale de tous les octets ; destination inconnue
  ou dépassement des budgets d'instructions/temps font refuser le contrôle.

L'arène de 64 Kio employée pour un objet isolé aurait été trop petite pour la
table entière : les sources commerciales utilisent **66 880 octets** répartis
en 1 347 allocations. La variante Benelli utilise **67 216 octets / 1 353
allocations**, sans allocation de taille non bornée.

## Résultats obtenus

| Table | Emplacements parcourus | Objets contrôlés | Pointeurs vides | Curseur final | Réserve non parcourue |
|---|---:|---:|---:|---:|---:|
| Sabre original | 500 | 272 | 228 | 139088 | 112912 |
| Sabre + Benelli désactivé | 500 | 273 | 227 | 139592 | 112408 |
| PatchX01 original | 500 | 272 | 228 | 139088 | 112912 |
| PatchX01 + Benelli désactivé | 500 | 273 | 227 | 139592 | 112408 |

**2 000 passages d'emplacement et 1 090 objets** contrôlés. L'objet ajouté
reste à l'indice 359 ; les cases suivantes gardent leur identifiant malgré
le décalage physique de 504 octets. Les deux restitutions de tables restent
exactes. Les empreintes des résultats correspondent aux
[laboratoires de transaction](TRANSACTION_TABLES.md).

Le rapport privé `.analysis/item-table-traversal-20260927.json` contient
également les empreintes de chaque record chargé et les surcharges exclues.
Huit tests synthétiques nouveaux couvrent les refus, l'arène, les curseurs,
les couches et les reçus incomplets ; ils ne remplacent pas cette exécution
privée de la boucle commerciale.

## Ce qui n'est pas démontré

Ce contrôle **n'est pas un chargement en jeu**. Il n'exécute ni le chargeur FPV
complet, ni les modèles/scènes, ni l'ouverture effective des fichiers, ni les
sauvegardes de partie. Il n'accorde aucune liberté globale d'identifiant et
n'active aucun des fichiers désactivés. Les tables Base/Patch de 255 slots ne
sont pas passées à cette boucle de 500 slots.

```powershell
.\.venv\Scripts\python.exe tools/item_table_traversal_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --descriptor-lab '.analysis/item-descriptor-labs/BenelliDescriptor_v3' --json-output '.analysis/item-table-traversal-nouveau.json'
```

Un rapport existant n'est jamais écrasé. L'outil relit les sources verrouillées,
reconstruit la variante en mémoire, contrôle les deux états et vérifie le retrait.
