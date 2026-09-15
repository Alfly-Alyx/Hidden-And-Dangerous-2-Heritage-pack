# Tutoriel — accès au secret sous la version 1.12

État : **création moderne minimale, placement éditeur requis**, 14 septembre
2026. Aucun objet commercial n’est déplacé et aucun binaire actif n’est fourni.

## Verdict

La chaîne du secret est complète : T_EE_Button rend item_cihla visible et remet
du carburant au Bedford ; T_EE_Activator1 vérifie l’objet d’inventaire 245 puis
active les quatre cibles et les cinq effets. La rupture concerne seulement
l’accès physique : la route historique par le Bedford n’est plus praticable
quand l’escalade des véhicules est désactivée en 1.12.

Aucune option de script ou propriété mission-locale restaurant cette collision
n’a été trouvée dans les scripts Base/Patch ni dans les notes locales. Le repli
TUT-ACCESS est donc appliqué : **une seule courte échelle physique**, clonée
d’un objet commercial du tutoriel, sans téléporteur.

## Donneur commercial choisi

Le cadre la_Tut_rebrik_ est une échelle déjà présente dans la même mission à
45.935543, 0.743713, 14.415919. Il sert de donneur complet de modèle, collision,
matériau et échelle. Les autres échelles commerciales restent inchangées.

Le nouvel objet portera le nom TUT_access_ladder_112 et l’étiquette explicite
MODERNE. Sa transformation cible n’est pas inventée dans ce dépôt : l’éditeur
doit l’ajuster contre l’accès historique près du Bedford avec la collision et
le gabarit du joueur visibles.

Repères confirmés :

- la_Bedford_1 : -17.804197, -1.512808, 80.766449 ;
- T_dummy_EE_Activator1 : 57.962864, 1.353687, 41.821579.

Ces repères n’autorisent pas une interpolation aveugle : l’orientation, la
hauteur du toit et le volume de collision doivent être mesurés en éditeur.

## Contraintes non négociables

- un seul nouvel objet ;
- cloner l’enregistrement complet de la_Tut_rebrik_, pas seulement son modèle ;
- ne déplacer ni Bedford, lingot/item_cihla, bouton, cibles ou déclencheurs ;
- aucun script, checkpoint, signal ou téléporteur supplémentaire ;
- ne pas masquer un objet commercial existant ;
- la variante doit se désinstaller en retirant uniquement le clone moderne.

## Tests

1. Baseline 1.12 : confirmer l’inaccessibilité par le véhicule et la chaîne
   secrète encore active.
2. Placer le clone en éditeur, puis tester montée/descente avec tous les profils
   de personnage et sans saut forcé.
3. Vérifier absence d’accrochage, chute sous carte et blocage du Bedford.
4. Presser le bouton, prendre l’objet 245 et terminer toute la chaîne du secret.
5. Sauvegarder/reprendre au pied, au sommet et après le bouton.
6. Désinstaller le clone et comparer les hashes/positions de tous les objets
   protégés : ils doivent être identiques au commercial.

Le plan reste bloqué tant qu’une transformation collision-safe n’a pas été
capturée et documentée depuis l’éditeur.

