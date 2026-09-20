from reportlab.lib.units import mm
from reportlab.platypus import Spacer, PageBreak
from pdf_common import OUT, HD2Doc, P, bullet, number_steps, info_box, table, section, cover

def build_report():
    path = OUT / "HD2-Rapport-des-Decouvertes.pdf"
    doc = HD2Doc(str(path), "HD2 - Rapport des découvertes")
    s = []
    cover(s, "Dossier d'archéologie - Révision 0.7.6", "Rapport des<br/>découvertes",
          "Contenu coupé, variantes internes, objectifs fragiles, routes, armes, véhicules et faisabilité de restauration.",
          "Installation commerciale 1.12 + Sabre Squadron<br/>Recherche locale et sources d'époque - 15 septembre 2026")

    section(s,"00","Synthèse")
    s.append(info_box("Conclusion centrale",
        "L'installation contient davantage de vestiges exploitables qu'un simple inventaire des menus ne le laisse voir. "
        "L'audit stable couvre désormais les 33 missions solo, les neuf scénarios coopératifs commerciaux et les 25 variantes multijoueurs scriptées. Il restaure les données encore complètes et isole les créations nécessaires au lieu de les présenter comme du contenu officiel retrouvé."))
    s.append(Spacer(1,4*mm))
    s.append(P("Les découvertes les plus solides","h2"))
    s.append(bullet([
        "33 missions solo déclarées et retrouvées : aucune campagne finale complète n'est simplement oubliée.",
        "82 arbres officiels lisibles ; 104 405 surfaces de zone et 561 objets border neutralisables.",
        "CMP 2.6.5 figée : 23 600 entrées, 23 277 fichiers et 156 entrées de cartes.",
        "Les 47 dossiers multijoueurs commerciaux et les deux prototypes sont tous déclarés après installation.",
        "Les 25 variantes multijoueurs scriptées totalisent 203 liaisons et 183 scripts disponibles ; leurs douze scripts libres ont été classés.",
        "Africa 1 et Africa 4 sont explicitement neutralisés par la mise à jour 1.12 alors que leurs scènes restent complètes.",
        "ENGLAND, CASTLE1 et CASTLE2 prouvent des branches internes, mais pas des cartes autonomes complètes.",
        "M323, Aichi, La-5 et Fa 223 ont bien des modèles dans l'archive ; la jouabilité pilotable n'est pas démontrée.",
        "London_mp/Poland et la campagne Angleterre/Londres annoncée sont deux dossiers historiques à distinguer."
    ]))
    s.append(P("Niveaux de confiance","h2"))
    s.append(table([
        ["Niveau","Critère","Usage"],
        ["A - confirmé","Observation locale reproductible ou déclaration directe","Base d'une restauration"],
        ["B - recoupé","Source d'époque + trace locale, ou deux sources indépendantes","Solide"],
        ["C - probable","Capture, identifiant ou structure partielle","Prototype seulement"],
        ["D - hypothèse","Interprétation isolée ou souvenir","Ne pas distribuer comme fait"]
    ],[29*mm,91*mm,48*mm]))
    s.append(PageBreak())

    section(s,"01","Jeu en ligne et collection communautaire")
    s.append(P("RpR publie encore en 2026 un serveur maître, une procédure GameSpy de remplacement, des serveurs actifs et CMP 2.6.5. Le contrôle TCP du serveur maître sur le port 28910 réussit."))
    s.append(table([
        ["Élément","Constat","Statut"],
        ["Résolution GameSpy","Trois anciens noms redirigés vers 78.47.255.224","Automatisé"],
        ["DirectPlay","Requis sur Windows moderne pour le réseau","Contrôlé"],
        ["Liste Internet","Infrastructure présente ; affichage réel à tester dans le jeu","Test humain requis"],
        ["CMP 2.6.5","Archive verrouillée par taille et SHA-256","Intégrée au flux"],
        ["Serveurs 2026","Plusieurs ports et modes publiés par RpR","Publics"]
    ],[36*mm,86*mm,46*mm]))
    s.append(P("CMP auditée","h2"))
    s.append(table([
        ["Mesure","Valeur"],
        ["Commit","793d979748b27a9924fccc30fa0fba6edb7cd70f"],
        ["Taille","1 084 146 265 octets"],
        ["SHA-256","DD0CA6FED1FB056DCB064813C223E0423F1FD9B13E291D106D8B983C467ABC33"],
        ["Contenu","23 600 entrées ; 23 277 fichiers ; 156 entrées de cartes"],
        ["Déployé","3 118 285 955 octets"]
    ],[40*mm,128*mm]))
    s.append(P("Sources","h2"))
    s.append(P('<link href="https://www.rprclan.com/hd2/play-online">RpR - Play Online</link>',"source"))
    s.append(P('<link href="https://rprclan.com/">RpR - serveurs et CMP annoncés en 2026</link>',"source"))
    s.append(P('<link href="https://github.com/ehylla93/had2-cmp/">Dépôt had2-cmp</link>',"source"))
    s.append(PageBreak())

    section(s,"02","Exploration sans échec de frontière")
    s.append(P("Les limites de mission sont portées par deux indicateurs de surface : avertissement 0x40 et échec 0x20. Le paquet efface seulement le masque 0x60. Les objets physiques explicitement nommés border sont traités séparément : leur étiquette est remplacée à longueur constante, méthode dont l'effet non solide est attesté par les essais de rétro-ingénierie de tree.klz. Les murs, sols, clôtures et autres propriétés restent intacts."))
    s.append(table([
        ["Corpus","Arbres","Avec limites","Surfaces 0x60","Objets border","Collisions"],
        ["Officiel final","82","75","104 405","561","2 446 014"],
        ["CMP - test intégré","Échantillon","-","1 202","contrôlés","-"]
    ],[31*mm,21*mm,26*mm,30*mm,29*mm,31*mm]))
    s.append(P('<link href="https://hidden-and-dangerous.net/board/viewtopic.php?t=2173">Recherche communautaire du format tree.klz et essai de renommage</link>',"source"))
    s.append(Spacer(1,5*mm))
    s.append(info_box("Ce que la correction ne fait pas",
        "Elle empêche l'avertissement et l'échec de zone et neutralise les objets explicitement nommés border. Elle n'ajoute pas de terrain, de collision, de navigation IA ou de secteurs absents. "
        "Une exploration peut donc révéler un décor praticable, un obstacle réel non identifié comme bord, ou simplement le vide."))
    s.append(P("Conséquence pour la recherche","h2"))
    s.append(P("Le mode libre sert d'outil d'archéologie : il permet d'examiner les bords de chaque carte sans sanction immédiate. Un passage devient une route restaurable seulement si sa géométrie, ses collisions et sa progression restent cohérentes."))
    s.append(P("Sécurité","h2"))
    s.append(P("Chaque arbre est copié dans un fichier de surcharge après contrôle structurel. La taille reste identique et une seconde passe doit trouver zéro indicateur résiduel. Toute cible remplacée est sauvegardée avant écriture."))
    s.append(PageBreak())

    section(s,"03","Objectifs composés et routes")
    s.append(table([
        ["Mission","Anomalie","Correction","Nuance"],
        ["Arctic 3","Un acteur suivi est tué par une autre séquence","Amik_2 devient Amik_1","Une route peut contourner le déclencheur ; objectif fragile, pas toujours impossible"],
        ["Africa 2","La mort du char ne rejoint pas la validation","Signal relié au gestionnaire existant","Ressources déjà présentes"],
        ["Normandy 2","Le compteur n'existe qu'après une première mort","Initialisé à cinq","Le résultat parfait redevient représentable"]
    ],[29*mm,49*mm,44*mm,46*mm]))
    s.append(P("Actions réduites ou désactivées","h2"))
    s.append(P("CASTLE2 offre le meilleur exemple : quatre objectifs structurés subsistent, tandis qu'un cinquième objectif de récupération des armes saisies est commenté. Ses scripts auxiliaires restent présents. Cela prouve une action retirée, mais pas encore une mission autonome complète."))
    s.append(P("Choix de chemin en France","h2"))
    s.append(P("Dans Operation Overlord - Lighthouse, cinq caméras, deux trajectoires et deux accès souterrains existent encore. La liaison entre Spawnsingle01 et X_N1_player01.scr a disparu. Sa restauration rétablit le guidage original vers les deux approches sans créer de nouveau tunnel."))
    s.append(info_box("Règle d'enquête",
        "Un ancien objectif à trois actions n'est confirmé que si les trois déclencheurs, leur compteur, le texte et les routes praticables sont tous retrouvés. Un objet isolé ou une ligne de briefing ne suffit pas."))
    s.append(PageBreak())

    section(s,"04","Sept easter eggs, dont deux neutralisés")
    s.append(table([
        ["Mission","État local","Découverte"],
        ["Tutorial","Séquence et lingot présents","Route historique bloquée en 1.12 par l'escalade des véhicules"],
        ["Africa 1","Effets complets","Le patch force mrtvi_panaci de 1 à 0 ; restauration exacte possible"],
        ["Burma 1","Complet","Tous les ennemis doivent être morts avant le troisième crâne"],
        ["Alps 1","Complet","Quatre acteurs doivent être réunis près du rocher"],
        ["Alps 2","Complet","Trois zones successives pour le même type de lingot"],
        ["Normandy 1","Complet","Compteur de dix bouteilles puis signal au garde"],
        ["Africa 4","Effets complets","Le patch remplace le saut ACTIVATED par END"]
    ],[29*mm,53*mm,86*mm]))
    s.append(Spacer(1,5*mm))
    s.append(P("Africa 4 - preuve nouvelle","h2"))
    s.append(P("Les clés A, B et C sont les objets 240, 241 et 242. Lorsqu'elles sont toutes à moins de trois mètres, le script d'origine active une valeur persistante et la scène meteor01. La mise à jour 1.12 neutralise uniquement le branchement. Les modèles, trajectoires et particules restent en place."))
    s.append(P("Africa 1 - seconde neutralisation confirmée","h2"))
    s.append(P("La comparaison de versions montre que le patch 1.12 force à zéro une condition nécessaire aux quatre morts de la mise en scène du jeep. Les trois invités, l'armure rouge, le portail de feu et la caméra sont toujours liés à la mission."))
    s.append(info_box("Décision 0.7.6",
        "Restaurer Africa 1 et Africa 4 avec une surcharge de leurs déclencheurs. Ne pas modifier les cinq secrets qui fonctionnent déjà. Le Tutorial reste en étude pour une solution 1.12 qui ne déplace pas arbitrairement le lingot."))
    s.append(PageBreak())

    section(s,"05","Londres : deux histoires, pas une")
    s.append(P("La presse de 2001 cite Londres et l'Allemagne parmi les lieux de 24 missions et sept campagnes, sans nommer les sept campagnes. En juin 2003, Games.cz annonce encore un Londres en ruines mais distingue explicitement la campagne anglaise déjà remplacée d'un possible reliquat multijoueur britannique. En septembre, GameSpot ne compte plus que six campagnes et 23 missions. Ces nombres variables prouvent une refonte, pas un nombre calculable de campagnes cachées."))
    s.append(table([
        ["Élément","Preuve","Conclusion"],
        ["Campagne Angleterre/Londres","Annonces d'époque + dossier ENGLAND de 14 scripts","Projet coupé ; carte solo complète non retrouvée"],
        ["London_mp, jeu de base","Scène et collision, paquet multijoueur incomplet, non déclaré","Arène en chantier"],
        ["London_mp, Sabre Squadron","Ressources complétées + name=Poland dir=London_mp","Carte multijoueur achevée et publiée"]
    ],[43*mm,65*mm,60*mm]))
    s.append(Spacer(1,5*mm))
    s.append(info_box("Correction d'interprétation",
        "Poland est bien l'achèvement du dossier London_mp. La chronologie rend plausible qu'il corresponde au reliquat multijoueur britannique évoqué en juin 2003. Cela ne prouve pas que cette arène soit la totalité de la campagne anglaise annoncée, ni qu'elle conserve une mission solo ou le scénario de Gary Bristol."))
    s.append(P("Sources d'époque","h2"))
    s.append(P('<link href="https://www.gameswelt.de/hidden-dangerous-2/news/interview-mit-dem-chef-designer-61828">Gameswelt, entretien du 9 mars 2001</link>',"source"))
    s.append(P('<link href="https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655">Games.cz, preview du 7 juin 2003</link>',"source"))
    s.append(P('<link href="https://www.gamespot.com/articles/hidden-and-dangerous-2-preview/1100-6030857/">GameSpot, preview du 25 septembre 2003</link>',"source"))
    s.append(P('<link href="https://www.gamespot.com/articles/qanda-hidden-and-dangerous-2-sabre-squadron/1100-6109875/">GameSpot, entretien Sabre Squadron du 7 octobre 2004</link>',"source"))
    s.append(P('<link href="https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf">Computer Gaming World 207</link>',"source"))
    s.append(PageBreak())

    section(s,"06","Branches internes et prototypes")
    s.append(table([
        ["Dossier","Contenu","Classement"],
        ["ENGLAND","14 scripts : otage, gardes, sniper, appels HELP, détecteurs","Fragment historique sans carte complète"],
        ["CASTLE1","60 scripts d'une branche ancienne","Architecture de mission, paquet autonome absent"],
        ["CASTLE2","55 scripts, personnages, quatre objectifs + cinquième commenté","Démonstration possible avec création moderne"],
        ["ALPS3_OBJ","Sous-version de scripts","Recouverte par la mission Sabre complète déjà active"],
        ["ARDENS1_OBJ","Ancien squelette de scripts","Recouvert par la version Sabre complète déjà active"],
        ["NORMANDY3_MP_ZONE","Variante officielle tronquée ; six fichiers propres valides","Fallback Normandy3 MP, compatible mais non fidèle"],
        ["AFRIKA5_MP","7 fichiers propres + 6 ressources identiques disponibles","Complétée et activée comme prototype"]
    ],[32*mm,86*mm,50*mm]))
    s.append(P("Finir les créations très incomplètes","h2"))
    s.append(P("Le projet peut construire des démonstrations à partir d'ENGLAND ou CASTLE2, mais doit distinguer trois couches : données officielles conservées, raccords techniques indispensables, création narrative ou visuelle nouvelle."))
    s.append(info_box("Priorité",
        "CASTLE2 est le meilleur candidat suivant : sa logique est plus riche et son objectif 5 retiré est identifiable. ENGLAND reste un prototype de recherche tant que sa géométrie d'origine n'est pas retrouvée."))
    s.append(PageBreak())
    section(s,"07","Aéronefs et véhicules : inventaire corrigé")
    s.append(P("Une recherche par noms usuels avait produit de faux négatifs. Les noms internes, les espaces et une faute d'orthographe expliquent plusieurs erreurs."))
    s.append(table([
        ["Élément","Fichiers locaux","Verdict"],
        ["Me 323","LA_M323.4ds + version simplifiée","Modèle présent ; pilotabilité non démontrée"],
        ["La-5","la_La-5.4ds + version simplifiée","Modèle présent ; aucune mission identifiée"],
        ["Aichi Val","la_aici.4ds + version simplifiée","Modèle présent sous orthographe interne raccourcie"],
        ["Fa 223","la_Fa 223.4ds + version simplifiée","Modèle présent ; l'espace du nom masquait le résultat"],
        ["Ju 52","12 ressources et variantes","Présent et appelé par une scène d'Africa 1"],
        ["Fw 200","Modèle principal + simplifié","Asset orphelin ou de scène"],
        ["Li-2","Modèle principal + simplifié","Asset orphelin ou de scène"],
        ["DFS 230","Nom interne DSF 230","Planeur présent sous variante orthographique"]
    ],[30*mm,65*mm,73*mm]))
    s.append(Spacer(1,4*mm))
    s.append(P("Ce que montrent les modèles","h2"))
    s.append(P("M323, La-5, Aichi et Fa 223 contiennent des éléments nommés comme moteurs, hélices ou rotors, surfaces mobiles, sièges et caméras. Ils ne sont donc pas de simples images. Mais aucune chaîne complète de commandes, physique, dégâts, cockpit, IA et mission pilotable n'est encore démontrée."))
    s.append(info_box("Classement correct","Présent comme modèle de véhicule ; jouabilité annoncée historiquement ; véhicule pilotable fini non prouvé."))
    s.append(PageBreak())

    section(s,"08","Armes et équipements")
    s.append(table([
        ["Élément","Trace","Conclusion"],
        ["Benelli M4","18 animations de vue, sons, icône, texture et munition 179","Meilleur candidat additif ; emplacement objet remplacé par la boussole"],
        ["Vickers K","Montée et utilisée sur la Jeep SAS","Active comme arme de véhicule, pas comme arme portative"],
        ["Flammenwerfer 35","Nom + munition ; pas de modèle d'arme complet","Arme annoncée et retirée ; reconstruction nécessaire"],
        ["Portable No. 2","Nom + munition ; même lacune","Arme annoncée et retirée"],
        ["flame1.4ds","471 octets, seul objet fire01","Effet de flamme, pas lance-flammes"],
        ["Garota","Citée par le lead designer","Arme annoncée ; implémentation locale complète non prouvée"],
        ["ZK-383","Capture alpha/bêta","Indice visuel crédible, pas de chaîne jouable trouvée"],
        ["FG 42 / MG 34","Identifiants ou munitions orphelins","Candidats, pas preuve d'une arme finie"]
    ],[34*mm,65*mm,69*mm]))
    s.append(P("Pourquoi les lance-flammes ne sont pas simplement activés","h2"))
    s.append(P("Il faudrait recréer le modèle tenu et posé, les animations, le réservoir, les sons, la portée, les dégâts, l'effet sur les personnages, l'IA et la synchronisation multijoueur. Une première version serait un mod expérimental moderne, même si les noms viennent du projet d'origine."))
    s.append(P("Sources","h2"))
    s.append(P('<link href="https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/">GameSpot - entretien de préproduction avec Thomas Pluharik</link>',"source"))
    s.append(P('<link href="https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655">Games.cz - arsenal annoncé en 2003</link>',"source"))
    s.append(P('<link href="https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/">Entretien Illusion Softworks, 2004</link>',"source"))
    s.append(PageBreak())

    section(s,"09","Intrigue et scènes coupées")
    s.append(table([
        ["Élément","Ce qui est attesté","Limite"],
        ["Gary Bristol","Chef d'équipe annoncé, lié à Dunkerque et à une intrigue continue","Dialogue et campagne complète absents"],
        ["Scarred Man","Adversaire récurrent annoncé","Aucun équivalent final nommé confirmé"],
        ["M. Murrau","Expert des moteurs à réaction à protéger pendant trois missions","Arc de missions non retrouvé"],
        ["Pont avec train","Visible ou cité parmi les éléments de préversion","Localisation et niveau exacts inconnus"],
        ["Entrepôt","Même dossier de coupes/refontes","La réponse studio est globale, pas une attribution séparée"],
        ["Londres et Allemagne","Lieux annoncés en 2001","Une campagne jouable complète n'est pas prouvée"]
    ],[34*mm,76*mm,58*mm]))
    s.append(P("Refonte du projet","h2"))
    s.append(P("Les sources indiquent un changement de moteur, le départ du concepteur principal en 2001 et une réorientation. Les promesses de campagnes, objectifs nombreux, coopération et véhicules ont donc pu être supprimées, remplacées ou redistribuées."))
    s.append(info_box("Prudence sur l'entretien de 2004",
        "Le studio confirme globalement que beaucoup d'éléments montrés avant la sortie ont été modifiés ou retirés. La réponse ne confirme pas séparément chaque capture de pont, train ou entrepôt."))
    s.append(P("Sources","h2"))
    s.append(P('<link href="https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf">Computer Gaming World 207 - Gary Bristol et Dunkerque</link>',"source"))
    s.append(P('<link href="https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655">Games.cz 2003 - refonte et lieux</link>',"source"))
    s.append(P('<link href="https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/">Illusion Softworks 2004 - confirmation générale des coupes</link>',"source"))
    s.append(PageBreak())

    section(s,"10","Corrections apportées aux dossiers préliminaires")
    s.append(P("Les deux PDF fournis au début de l'enquête ont servi de point de départ. L'audit direct des archives impose les corrections suivantes."))
    s.append(table([
        ["Première lecture","Preuve nouvelle","Classement révisé"],
        ["Me 323 et Aichi sans modèle identifiable","LA_M323.4ds et la_aici.4ds trouvés","Modèles présents"],
        ["Fa 223 absent du filtre","la_Fa 223.4ds contient un espace","Modèle présent"],
        ["Ju 52 et La-5 véhicules absents","Modèles trouvés ; Ju 52 appelé en Africa 1","Présents, pilotabilité non démontrée"],
        ["ALPS3_OBJ mission abandonnée","Sabre apporte la variante complète déjà active","Ancienne branche, pas niveau perdu"],
        ["ARDENS1_OBJ prototype autonome","Version Sabre complète prioritaire","Ancienne branche"],
        ["Trois objectifs impossibles","Arctic 3 peut être contourné selon la route","Cassés ou incohérents"],
        ["Six easter eggs","Africa 4 conserve un septième effet neutralisé","Sept dans le jeu de base"]
    ],[51*mm,65*mm,52*mm]))
    s.append(Spacer(1,5*mm))
    s.append(P("Principale leçon","h2"))
    s.append(P("Une recherche par nom courant ne suffit pas : la casse, les espaces, les fautes internes et les ressources simplifiées changent le résultat. Chaque absence supposée doit être contrôlée par inventaire complet, variantes de nom, contenu du modèle et références de scènes."))
    s.append(PageBreak())

    section(s,"11","État des lieux et feuille de route")
    s.append(table([
        ["Chantier","Acquis","Étape suivante"],
        ["Réseau","Serveur maître joignable, configuration automatisée","Voir la liste et rejoindre une partie dans le jeu"],
        ["Campagnes officielles","33 sur 33 inventoriées","Chercher variantes, branches et objectifs, pas une campagne finale manquante"],
        ["Exploration","82 arbres officiels et 225 arbres libres locaux contrôlés","Tester les bords, collisions et secteurs mission par mission"],
        ["Objectifs","14 ensembles suivis et 73 états détaillés","Jouer les routes alternatives et sauvegarder/recharger"],
        ["Easter eggs","Africa 1 et Africa 4 réactivés","Valider en jeu ; résoudre le Tutorial 1.12"],
        ["Vestiges","Normandy3 Zone et Africa5 Prototype activés","Essais IA, modes et stabilité"],
        ["Londres","Campagne annoncée distinguée de Poland","Rechercher d'autres assets avant toute recréation"],
        ["Prototypes","ENGLAND et CASTLE1/2 classés","Démonstration CASTLE2 avec objectif 5"],
        ["Armes","Benelli priorisé ; lance-flammes correctement diagnostiqués","Prototype additif séparé, puis modèles et comportements nouveaux"],
        ["Aéronefs","Modèles exacts retrouvés","Choisir un appareil et construire un banc d'essai"],
        ["Communauté","CMP 2.6.5 intégrée","Évaluer d'autres paquets un par un avec licences et conflits"]
    ],[42*mm,63*mm,63*mm]))
    s.append(Spacer(1,4*mm))
    s.append(P("Ordre de travail recommandé","h2"))
    s.append(number_steps([
        "Test en jeu du réseau, des objectifs, des deux easter eggs réactivés et des deux prototypes.",
        "Rendre le secret du Tutorial accessible en 1.12 sans déplacer arbitrairement sa cachette.",
        "Auditer CASTLE2 sur une carte apparentée et restaurer son objectif 5 dans une démonstration isolée.",
        "Rechercher les chemins alternatifs mission par mission, notamment les accès français et les branches à plusieurs actions.",
        "Construire un prototype de lance-flammes clairement étiqueté comme création expérimentale.",
        "Étudier un aéronef à la fois avec une mission d'essai dédiée.",
        "N'engager une campagne Angleterre ou Gary Bristol qu'en séparant faits historiques et scénario nouveau."
    ]))
    s.append(PageBreak())

    section(s,"12","Sources et traçabilité")
    sources = [
        ("RpR - jouer en ligne et redirection GameSpy","https://www.rprclan.com/hd2/play-online"),
        ("RpR - serveurs actifs et CMP 2.6.5","https://rprclan.com/"),
        ("Dépôt had2-cmp","https://github.com/ehylla93/had2-cmp/"),
        ("GameSpot - entretien de préproduction","https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/"),
        ("Gameswelt - entretien du 9 mars 2001","https://www.gameswelt.de/hidden-dangerous-2/news/interview-mit-dem-chef-designer-61828"),
        ("Games.cz - preview du 7 juin 2003","https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655"),
        ("Computer Gaming World 207","https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf"),
        ("Illusion Softworks - entretien de 2004","https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/"),
        ("GameFAQs - six easter eggs historiques","https://gamefaqs.gamespot.com/pc/451072-hidden-and-dangerous-2/cheats"),
        ("H&amp;D 2 Wiki - easter eggs","https://hd2.fandom.com/wiki/Easter_eggs"),
        ("RpR - archéologie alpha/bêta","https://www.rprclan.com/forum/22-general/2856-h-d2-lost-content-early-beta-alpha-things?start=36")
    ]
    for name,url in sources:
        s.append(P(f'<link href="{url}">{name}</link>',"source"))
    s.append(Spacer(1,5*mm))
    s.append(info_box("Traçabilité locale",
        "Les conclusions techniques reposent sur l'inventaire des archives commerciales, la comparaison jeu de base / Patch 1.12 / Sabre Squadron, et des validations reproductibles. Aucun fichier commercial n'est reproduit dans ce rapport."))
    s.append(P("Documents associés","h2"))
    s.append(P("Le guide joueur séparé explique seulement comment déclencher les secrets et atteindre les coins cachés. Les notes détaillées du projet restent dans le dossier docs."))
    doc.build(s)
    return path

if __name__ == "__main__":
    print(build_report())
