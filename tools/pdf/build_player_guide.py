from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Spacer, PageBreak
from pdf_common import OUT, HD2Doc, P, bullet, number_steps, info_box, table, section, cover, Africa4Map

def build_player():
    path = OUT / "HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf"
    doc = HD2Doc(str(path), "HD2 - Guide joueur des secrets")
    s = []
    cover(s, "Guide joueur - Edition 0.7.5", "Secrets et<br/>easter eggs",
          "Sept séquences cachées, leurs conditions et les coins secrets utiles pour les atteindre.",
          "Hidden &amp; Dangerous 2: Sabre Squadron 1.12<br/>Guide pratique en français - 15 septembre 2026")

    section(s, "01", "Avant de commencer", "Ce guide va droit au but. Il ne décrit ni le moteur du jeu ni la fabrication des missions.")
    s.append(info_box("Pack conseillé",
        "Installez H&amp;D2 Heritage Pack 0.7.5 et laissez cochée l'option des easter eggs. "
        "Elle rend à nouveau activables les surprises d'Africa 1 et d'Africa 4, neutralisées par la mise à jour 1.12."))
    s.append(Spacer(1,4*mm))
    s.append(P("Règles utiles","h2"))
    s.append(bullet([
        "Faites une sauvegarde avant la dernière action de chaque secret.",
        "Respectez l'ordre indiqué : plusieurs déclencheurs ne vérifient l'état qu'une seule fois.",
        "Pour porter un corps ou déplacer un objet, utilisez l'action contextuelle habituelle.",
        "Ne rejoignez pas le point d'extraction avant d'avoir terminé le secret.",
        "Les effets sont parfois volontairement étranges ou macabres."
    ]))
    s.append(P("Vue rapide","h2"))
    s.append(table([
        ["Mission","Déclencheur","Résultat"],
        ["Tutorial","Interrupteur, camion, lingot","Cibles supplémentaires"],
        ["Africa 1","Officier sur le jeep détruit","Invités enflammés"],
        ["Burma 1","Tous les ennemis puis 3 crânes","Procession et spectacle"],
        ["Alps 1","4 corps sur un rocher","Surprise osseuse"],
        ["Alps 2","3 lingots dans 3 pièces, dans l'ordre","Squelettes en flammes"],
        ["Normandy 1","10 bouteilles puis garde ivre","Séquence cachée"],
        ["Africa 4","Réunir les clés A, B et C","Pluie de météores"]
    ],[32*mm,80*mm,56*mm]))
    s.append(PageBreak())

    section(s,"02","Tutorial - Le lingot sur le toit")
    s.append(number_steps([
        "Terminez les exercices jusqu'au stand de grenades et de tir antichar afin d'ouvrir la seconde zone.",
        "Prenez le jeep vers la piscine. Passez le camion sur votre droite, tournez à gauche et arrêtez-vous devant la baraque d'accueil où se tient l'instructeur.",
        "Dans la baraque, actionnez le petit interrupteur rouge situé à droite du bureau.",
        "Terminez ensuite l'exercice de la piscine avant de revenir. Si vous revenez trop tôt, la mission peut échouer.",
        "Le camion du parking démarre maintenant. Avancez-le légèrement, montez sur le capot, puis sur son toit et enfin sur le toit du garage. Prenez le lingot dans l'angle éloigné.",
        "Terminez l'exercice des explosifs. Revenez au stand de tir, ignorez l'instructeur et passez par la porte de sortie vers la mitrailleuse fixe. Gardez le lingot dans votre inventaire."
    ]))
    s.append(Spacer(1,4*mm))
    s.append(info_box("Attention avec la version 1.12",
        "La mise à jour 1.12 empêche normalement de grimper sur les véhicules. Le secret et le lingot existent toujours, "
        "mais cette route historique peut rester inaccessible. Le Heritage Pack 0.7.5 ne déplace pas encore le lingot afin de ne pas inventer une nouvelle cachette.",
        colors.HexColor("#FFF1DD")))
    s.append(P("Pourquoi c'est important","h2"))
    s.append(P("Le toit du garage est la cache d'origine. Une future correction 1.12 devra conserver cette découverte, ou signaler clairement tout nouvel accès."))
    s.append(PageBreak())

    section(s,"03","Africa 1 - Spaghetti Airport")
    s.append(P("But : brûler ensemble le jeep et l'officier pour faire apparaître trois invités."))
    s.append(number_steps([
        "Accomplissez tous les objectifs, sauf le regroupement final au véhicule. Gardez le jeep intact.",
        "Retournez au bâtiment principal et trouvez l'officier qui vous annonce que Schumann est déjà parti.",
        "Tuez cet officier et transportez son corps jusqu'aux tentes.",
        "Conduisez le jeep dans la partie circulaire de la tranchée située juste derrière les tentes, à gauche de la piste.",
        "Montez sur le jeep et déposez le corps de l'officier dessus.",
        "Éloignez-vous puis détruisez le jeep avec une grenade. Les trois invités apparaissent dans une mise en scène de feu."
    ]))
    s.append(Spacer(1,4*mm))
    s.append(info_box("Ce qui compte vraiment",
        "Le déclencheur vérifié demande l'officier, le jeep et leurs morts au bon endroit. "
        "Les deux tonneaux rouges parfois mentionnés dans d'anciens guides ne sont pas obligatoires."))
    s.append(P("Récompense pratique","h2"))
    s.append(P("L'un des invités porte un MP44, une occasion d'obtenir cette arme très tôt dans la campagne."))
    s.append(PageBreak())

    section(s,"04","Burma 1 et Alps 1")
    s.append(P("Burma 1 - Anthill","h2"))
    s.append(number_steps([
        "Terminez la mission sans rejoindre l'extraction.",
        "Éliminez absolument tous les ennemis, y compris ceux des bunkers et les isolés.",
        "Cherchez les trois crânes dispersés dans la carte et détruisez-les. Gardez le troisième pour la fin : tous les ennemis doivent déjà être morts au moment où vous le brisez.",
        "Prenez un seul homme et suivez le chemin vers l'extraction.",
        "Trois silhouettes apparaissent entre les ruines. Suivez-les jusqu'au camp où vous avez détruit les pièces et observez la scène."
    ]))
    s.append(info_box("Si rien ne se passe",
        "Un ennemi est probablement encore vivant, ou le troisième crâne a été détruit trop tôt. Rechargez la sauvegarde faite avant ce dernier crâne.",
        colors.HexColor("#FFF1DD")))
    s.append(Spacer(1,5*mm))
    s.append(P("Alps 1 - Babes in the Wood","h2"))
    s.append(number_steps([
        "Progressez jusqu'au premier carrefour en T, juste avant que la route tourne à droite vers le nid de MG42.",
        "Attendez le half-track venant de la route de gauche. Immobilisez-le avec quelques tirs.",
        "Tuez les quatre membres d'équipage lorsqu'ils descendent.",
        "Transportez les quatre corps sur le grand rocher le plus proche, dans les arbres. Regroupez-les bien au centre.",
        "Continuez la mission normalement. Une surprise osseuse vous attend plus loin."
    ]))
    s.append(PageBreak())

    section(s,"05","Alps 2 - Estate Agent")
    s.append(P("Trois lingots doivent être déposés dans trois endroits, dans cet ordre."))
    s.append(number_steps([
        "Après avoir remis les papiers et parlé aux gardes de l'entrepôt, entrez dans le château.",
        "Avant de rejoindre Salter, ouvrez la porte secrète derrière la grande fresque. Allégez votre inventaire et récupérez au moins deux lingots.",
        "Dans la bibliothèque, déposez le premier lingot avant de parler à Salter.",
        "Retournez chercher un autre lingot si nécessaire, puis parlez à Salter et suivez-la.",
        "Après l'escalier marqué Munition Lager, repérez les grandes peintures à droite. La première près de la porte cache une pièce. Laissez Salter ouvrir le passage suivant, crochetez la porte et déposez le deuxième lingot dans la salle des tableaux volés.",
        "Dans les archives, déposez le troisième lingot dans la pièce contenant le dossier.",
        "Rejoignez ensuite la cour et le camion pour découvrir la surprise."
    ]))
    s.append(P("Les deux coins cachés à retenir","h2"))
    s.append(bullet([
        "La porte derrière la grande fresque cache la réserve de lingots.",
        "La porte derrière la première grande peinture à droite mène à la pièce des tableaux volés."
    ]))
    s.append(info_box("Ordre obligatoire","Bibliothèque, salle des tableaux, archives. Chaque dépôt arme le déclencheur suivant."))
    s.append(PageBreak())

    section(s,"06","Normandy 1 - Lighthouse")
    s.append(P("Brisez dix bouteilles bleues. La dixième doit être celle des quartiers voisins de Gesch D. Tuez ensuite le garde ivre."))
    rows = [
        ["1","Niveau inférieur : près de deux gardes qui parlent, dans la pièce au bureau, au sol près du bureau."],
        ["2","Salle des sacs d'explosifs : derrière les portes en bois d'un placard à briser."],
        ["3","Quartiers de couchage : sous un lit superposé."],
        ["4","Quartiers de couchage : au-dessus d'une armoire métallique."],
        ["5","Sur l'étagère au-dessus du bureau, derrière les doubles portes marquées Gesch B."],
        ["6","Salle à manger : sur une table."],
        ["7","Cuisine : dans un placard ouvert."],
        ["8","Pièce marquée Arzt : au-dessus de l'armoire métallique."],
        ["9","Sous le panneau Gesch D, passez les grilles, tournez à gauche, puis entrez dans la pièce à droite : sur la table."],
        ["10","Quartiers de couchage juste à côté de la pièce précédente. Brisez celle-ci en dernier."]
    ]
    s.append(table([["N°","Emplacement"]]+rows,[12*mm,156*mm]))
    s.append(Spacer(1,3*mm))
    s.append(info_box("Dernière action","Après la bouteille 10, abattez le garde ivre. S'il est déjà mort, rechargez une sauvegarde.",colors.HexColor("#FFF1DD")))
    s.append(PageBreak())

    section(s,"07","Africa 4 - La pluie de météores")
    s.append(P("Ce septième easter egg est absent des guides historiques parce que la mise à jour 1.12 détourne son déclencheur. Le Heritage Pack 0.7.5 le réactive."))
    s.append(Africa4Map())
    s.append(Spacer(1,3*mm))
    s.append(number_steps([
        "Récupérez la clé A dans le secteur sud-ouest de l'enceinte, près du groupe de petites pièces et de la cour basse.",
        "Récupérez la clé B dans le secteur central-est, autour du bâtiment carré reconnaissable à son élément arrondi.",
        "Récupérez la clé C dans le secteur nord-est, près du bâtiment ouvert ou du toit à l'extrémité haute de l'enceinte.",
        "Réunissez les trois clés au même endroit, très proches les unes des autres, dans un rayon d'environ trois mètres.",
        "Écartez-vous et regardez le ciel : la séquence de météores doit se déclencher."
    ]))
    s.append(info_box("Astuce","Transportez les trois clés vers un point central et dégagé. Si l'effet ne part pas, rapprochez encore les objets ; les avoir simplement trouvés ne suffit pas."))
    s.append(PageBreak())

    section(s,"08","Autres coins cachés confirmés")
    s.append(P("Whisky Bar - conversation secrète","h2"))
    s.append(P("Approchez discrètement du hangar et écoutez les officiers sans interrompre leur conversation. L'information sur les renforts valide l'objectif secret. Le supposé dépôt de bombes n'est pas confirmé."))
    s.append(P("Final Showdown - interrupteur du camion radio","h2"))
    s.append(P("Inspectez le côté et le dessous du camion radio. Un petit interrupteur discret participe à la progression et peut facilement être pris pour un détail du décor."))
    s.append(P("Lighthouse - les deux accès souterrains","h2"))
    s.append(P("Avec le pack, la séquence de guidage d'origine montre de nouveau les deux accès souterrains. Comparez les deux approches au lieu de suivre une seule route."))
    s.append(P("Poland / London_mp","h2"))
    s.append(P("La ville en ruines appelée London_mp dans les fichiers est la carte multijoueur visible sous le nom Poland. Ce n'est pas une campagne solo Londres cachée, mais son architecture offre de nombreux étages et lignes de tir à explorer."))
    s.append(P("Exploration libre","h2"))
    s.append(P("Le pack enlève les avertissements et échecs de frontière. Sauvegardez avant de vous éloigner : certaines zones n'ont ni sol complet ni passage prévu."))
    s.append(PageBreak())

    section(s,"09","Checklist du chasseur de secrets")
    checks = [
        ["Tutorial","Interrupteur rouge activé","Lingot gardé jusqu'à la mitrailleuse"],
        ["Africa 1","Jeep intact jusqu'à la fin","Officier dessus dans la tranchée"],
        ["Burma 1","Tous les ennemis morts","Troisième crâne détruit en dernier"],
        ["Alps 1","Quatre membres d'équipage","Quatre corps sur le même rocher"],
        ["Alps 2","Bibliothèque","Tableaux puis archives"],
        ["Normandy 1","Neuf bouteilles d'abord","Bouteille 10 puis garde ivre"],
        ["Africa 4","Clés A, B et C","Réunies dans un rayon de 3 m"]
    ]
    s.append(table([["Mission","Contrôle 1","Contrôle 2"]]+checks,[32*mm,67*mm,69*mm]))
    s.append(Spacer(1,7*mm))
    s.append(info_box("Bonne chasse",
        "Les séquences les plus sensibles à l'ordre sont Burma 1, Alps 2 et Normandy 1. "
        "Pour Africa 1 et Africa 4, utilisez le Heritage Pack 0.7.5. Le secret du Tutorial attend encore une solution 1.12 validée en jeu."))
    s.append(Spacer(1,8*mm))
    s.append(P("Sources joueur","h2"))
    s.append(P('<link href="https://gamefaqs.gamespot.com/pc/451072-hidden-and-dangerous-2/cheats">GameFAQs - procédures historiques des six secrets publics</link>',"source"))
    s.append(P('<link href="https://hd2.fandom.com/wiki/Easter_eggs">H&amp;D 2 Wiki - synthèse communautaire des easter eggs</link>',"source"))
    s.append(P("Les précisions d'ordre et le septième secret d'Africa 4 ont été vérifiés dans les fichiers de l'installation 1.12.","source"))
    doc.build(s)
    return path

if __name__ == "__main__":
    print(build_player())
