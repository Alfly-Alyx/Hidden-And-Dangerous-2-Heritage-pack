from reportlab.lib.units import mm
from reportlab.platypus import Spacer, PageBreak
from pdf_common import OUT, HD2Doc, P, bullet, number_steps, info_box, table, section, cover


def build_report_en():
    path = OUT / "HD2-Discovery-Report-EN.pdf"
    doc = HD2Doc(str(path), "HD2 - Discovery report")
    s = []
    cover(
        s,
        "Game archaeology dossier - Revision 0.7.6",
        "Discovery<br/>report",
        "Cut content, internal variants, fragile objectives, routes, weapons, vehicles, and restoration feasibility.",
        "Commercial 1.12 installation + Sabre Squadron<br/>Local research and period sources - 16 September 2026",
    )

    section(s, "00", "Executive summary")
    s.append(
        info_box(
            "Central conclusion",
            "The installation contains more usable remnants than the game menus reveal. "
            "The stable audit now covers all 33 solo missions, the nine commercial cooperative scenarios, "
            "and 25 scripted multiplayer variants. Complete surviving data is restored, while work that needs "
            "new creation is kept separate and is never presented as recovered official content.",
        )
    )
    s.append(Spacer(1, 4 * mm))
    s.append(P("Strongest findings", "h2"))
    s.append(
        bullet(
            [
                "All 33 declared solo missions were found. No complete final campaign is merely hidden from the menu.",
                "82 readable official mission trees contain 104,405 boundary surfaces and 561 named border objects that can be neutralised.",
                "CMP 2.6.5 is pinned to 23,600 archive entries, 23,277 installable files, and 156 map entries.",
                "All 47 commercial multiplayer folders and both prototypes are declared after installation.",
                "The 25 scripted multiplayer variants contain 203 bindings and 183 available scripts. Their twelve loose scripts have been classified.",
                "Update 1.12 explicitly disables the Africa 1 and Africa 4 easter egg branches while leaving their scenes intact.",
                "ENGLAND, CASTLE1, and CASTLE2 prove internal branches, but not complete standalone maps.",
                "M323, Aichi, La-5, and Fa 223 models are present. A complete flyable implementation is not proven.",
                "London_mp/Poland and the announced England/London campaign are separate historical subjects.",
            ]
        )
    )
    s.append(P("Confidence levels", "h2"))
    s.append(
        table(
            [
                ["Level", "Criterion", "Use"],
                ["A - confirmed", "Reproducible local observation or direct statement", "Restoration basis"],
                ["B - corroborated", "Period source plus local trace, or two independent sources", "Strong evidence"],
                ["C - probable", "Screenshot, identifier, or partial structure", "Prototype only"],
                ["D - hypothesis", "Single interpretation or memory", "Never distribute as fact"],
            ],
            [29 * mm, 91 * mm, 48 * mm],
        )
    )
    s.append(PageBreak())

    section(s, "01", "Online play and the community collection")
    s.append(
        P(
            "RpR still publishes a replacement master server, a GameSpy redirection procedure, active servers, "
            "and CMP 2.6.5 in 2026. A TCP probe of the master server on port 28910 succeeds."
        )
    )
    s.append(
        table(
            [
                ["Component", "Finding", "Status"],
                ["GameSpy resolution", "Three retired host names redirect to 78.47.255.224", "Automated"],
                ["DirectPlay", "Required for networking on current Windows systems", "Checked"],
                ["Internet list", "Infrastructure is present; the real in-game display still needs a human test", "Manual test"],
                ["CMP 2.6.5", "Archive locked by exact size and SHA-256", "Integrated"],
                ["2026 servers", "RpR publishes several ports and modes", "Public"],
            ],
            [36 * mm, 86 * mm, 46 * mm],
        )
    )
    s.append(P("Audited CMP package", "h2"))
    s.append(
        table(
            [
                ["Measure", "Value"],
                ["Commit", "793d979748b27a9924fccc30fa0fba6edb7cd70f"],
                ["Size", "1,084,146,265 bytes"],
                ["SHA-256", "DD0CA6FED1FB056DCB064813C223E0423F1FD9B13E291D106D8B983C467ABC33"],
                ["Contents", "23,600 entries; 23,277 files; 156 map entries"],
                ["Installed size", "3,118,285,955 bytes"],
            ],
            [40 * mm, 128 * mm],
        )
    )
    s.append(P("Sources", "h2"))
    s.append(P('<link href="https://www.rprclan.com/hd2/play-online">RpR - Play Online</link>', "source"))
    s.append(P('<link href="https://rprclan.com/">RpR - servers and CMP announced in 2026</link>', "source"))
    s.append(P('<link href="https://github.com/ehylla93/had2-cmp/">had2-cmp repository</link>', "source"))
    s.append(PageBreak())

    section(s, "02", "Exploration without boundary failure")
    s.append(
        P(
            "Mission boundaries use two surface flags: warning 0x40 and failure 0x20. The pack clears only mask 0x60. "
            "Physical objects explicitly named border are handled separately by replacing their label at constant length, "
            "a method whose non-solid result is supported by tree.klz reverse-engineering tests. Terrain, walls, floors, "
            "fences, and other collision properties remain intact."
        )
    )
    s.append(
        table(
            [
                ["Corpus", "Trees", "With limits", "0x60 surfaces", "Border objects", "Collisions"],
                ["Final official", "82", "75", "104,405", "561", "2,446,014"],
                ["CMP built-in test", "Sample", "-", "1,202", "checked", "-"],
            ],
            [31 * mm, 21 * mm, 26 * mm, 30 * mm, 29 * mm, 31 * mm],
        )
    )
    s.append(
        P(
            '<link href="https://hidden-and-dangerous.net/board/viewtopic.php?t=2173">'
            "Community research into tree.klz and the renaming experiment</link>",
            "source",
        )
    )
    s.append(Spacer(1, 5 * mm))
    s.append(
        info_box(
            "What the fix does not do",
            "It prevents boundary warnings and mission failure and neutralises objects explicitly named border. "
            "It does not create missing terrain, collision, AI navigation, or sectors. Exploring the edge of a map "
            "may therefore reveal usable scenery, an unrelated physical obstacle, or empty space.",
        )
    )
    s.append(P("Research value", "h2"))
    s.append(
        P(
            "Free exploration is an archaeology tool. It allows every map edge to be inspected without an immediate penalty. "
            "A passage becomes a restorable route only when its geometry, collision, and mission progression remain coherent."
        )
    )
    s.append(P("Safety", "h2"))
    s.append(
        P(
            "Every tree is written as a loose override after structural validation. File size remains unchanged, and a second "
            "audit must find no residual boundary marker. Every replaced target is backed up before writing."
        )
    )
    s.append(PageBreak())

    section(s, "03", "Compound objectives and routes")
    s.append(
        table(
            [
                ["Mission", "Fault", "Correction", "Nuance"],
                ["Arctic 3", "A tracked actor is killed by another sequence", "Amik_2 becomes Amik_1", "One route can bypass the trigger; fragile, not always impossible"],
                ["Africa 2", "Tank death never reaches completion", "Signal reconnected to the existing manager", "All resources already exist"],
                ["Normandy 2", "Counter exists only after the first death", "Initialised to five", "The perfect result becomes representable"],
            ],
            [29 * mm, 49 * mm, 44 * mm, 46 * mm],
        )
    )
    s.append(P("Reduced or disabled actions", "h2"))
    s.append(
        P(
            "CASTLE2 is the clearest example. Four structured objectives survive, while a fifth objective for recovering "
            "confiscated weapons is commented out. Its helper scripts are still present. This proves a removed action, "
            "but not a complete standalone mission."
        )
    )
    s.append(P("The lost route choice in France", "h2"))
    s.append(
        P(
            "Operation Overlord - Lighthouse still contains five cameras, two paths, and two underground entrances. "
            "The link between Spawnsingle01 and X_N1_player01.scr disappeared. Restoring it brings back the original "
            "guidance toward both approaches without inventing a tunnel."
        )
    )
    s.append(
        info_box(
            "Research rule",
            "An old three-action objective is confirmed only when all three triggers, their counter, the objective text, "
            "and the usable routes are found. An isolated prop or briefing line is not enough.",
        )
    )
    s.append(PageBreak())

    section(s, "04", "Seven easter eggs, including two disabled branches")
    s.append(
        table(
            [
                ["Mission", "Local state", "Finding"],
                ["Tutorial", "Sequence and gold bar present", "Historical route blocked in 1.12 by the vehicle-climbing change"],
                ["Africa 1", "Complete effects", "Patch forces mrtvi_panaci from 1 to 0; exact restoration is possible"],
                ["Burma 1", "Complete", "Every enemy must die before the third skull"],
                ["Alps 1", "Complete", "Four actors must be gathered by the rock"],
                ["Alps 2", "Complete", "Three successive zones for the same gold bar type"],
                ["Normandy 1", "Complete", "Ten-bottle counter followed by a signal to the guard"],
                ["Africa 4", "Complete effects", "Patch replaces the ACTIVATED jump with END"],
            ],
            [29 * mm, 53 * mm, 86 * mm],
        )
    )
    s.append(Spacer(1, 5 * mm))
    s.append(P("Africa 4 - new evidence", "h2"))
    s.append(
        P(
            "Keys A, B, and C are items 240, 241, and 242. When all are within three metres, the original script sets "
            "a persistent value and activates meteor01. Update 1.12 disables only the branch. Models, paths, and particles remain."
        )
    )
    s.append(P("Africa 1 - the second confirmed neutralisation", "h2"))
    s.append(
        P(
            "Version comparison shows that patch 1.12 forces to zero a condition required by the four deaths in the jeep scene. "
            "The three visitors, red armour, fire gate, and camera remain connected to the mission."
        )
    )
    s.append(
        info_box(
            "0.7.6 decision",
            "Restore Africa 1 and Africa 4 through loose trigger overrides. Leave the five secrets that already work untouched. "
            "Keep the Tutorial under study until a 1.12 solution preserves the original hiding place.",
        )
    )
    s.append(PageBreak())

    section(s, "05", "London: two histories, not one")
    s.append(
        P(
            "The 2001 press named London and Germany among the locations of 24 missions and seven campaigns without listing "
            "all seven campaigns. In June 2003, Games.cz still described a ruined London but explicitly separated the already "
            "replaced English campaign from a possible British multiplayer remnant. By September, GameSpot listed six campaigns "
            "and 23 missions. These changing totals prove redesign, not a calculable number of hidden campaigns."
        )
    )
    s.append(
        table(
            [
                ["Element", "Evidence", "Conclusion"],
                ["England/London campaign", "Period announcements plus the 14-script ENGLAND folder", "Cut project; no complete solo map found"],
                ["London_mp in the base game", "Scene and collision, incomplete multiplayer package, undeclared", "Arena under construction"],
                ["London_mp in Sabre Squadron", "Completed resources plus name=Poland dir=London_mp", "Finished and published multiplayer map"],
            ],
            [43 * mm, 65 * mm, 60 * mm],
        )
    )
    s.append(Spacer(1, 5 * mm))
    s.append(
        info_box(
            "Interpretation correction",
            "Poland is the completed London_mp folder. The chronology makes it plausible that it is the British multiplayer "
            "remnant mentioned in June 2003. This does not prove that the arena is the whole announced English campaign, "
            "or that it preserves a solo mission or the Gary Bristol story.",
        )
    )
    s.append(P("Period sources", "h2"))
    s.append(P('<link href="https://www.gameswelt.de/hidden-dangerous-2/news/interview-mit-dem-chef-designer-61828">Gameswelt, interview of 9 March 2001</link>', "source"))
    s.append(P('<link href="https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655">Games.cz, preview of 7 June 2003</link>', "source"))
    s.append(P('<link href="https://www.gamespot.com/articles/hidden-and-dangerous-2-preview/1100-6030857/">GameSpot, preview of 25 September 2003</link>', "source"))
    s.append(P('<link href="https://www.gamespot.com/articles/qanda-hidden-and-dangerous-2-sabre-squadron/1100-6109875/">GameSpot, Sabre Squadron interview of 7 October 2004</link>', "source"))
    s.append(P('<link href="https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf">Computer Gaming World 207</link>', "source"))
    s.append(PageBreak())

    section(s, "06", "Internal branches and prototypes")
    s.append(
        table(
            [
                ["Folder", "Contents", "Classification"],
                ["ENGLAND", "14 scripts: hostage, guards, sniper, HELP calls, detectors", "Historical fragment without a complete map"],
                ["CASTLE1", "60 scripts from an older branch", "Mission architecture; standalone package absent"],
                ["CASTLE2", "55 scripts, characters, four objectives plus a commented fifth", "Demonstration possible with modern creation"],
                ["ALPS3_OBJ", "Earlier script subset", "Superseded by the complete active Sabre mission"],
                ["ARDENS1_OBJ", "Older script skeleton", "Superseded by the complete active Sabre version"],
                ["NORMANDY3_MP_ZONE", "Truncated official variant; six valid native files", "Normandy3 MP fallback, compatible but not faithful"],
                ["AFRIKA5_MP", "7 native files plus 6 matching resources", "Completed and enabled as a prototype"],
            ],
            [32 * mm, 86 * mm, 50 * mm],
        )
    )
    s.append(P("Finishing very incomplete creations", "h2"))
    s.append(
        P(
            "The project can build demonstrations from ENGLAND or CASTLE2, but must keep three layers separate: surviving "
            "official data, indispensable technical joins, and newly created narrative or visual material."
        )
    )
    s.append(
        info_box(
            "Priority",
            "CASTLE2 is the strongest next candidate because its logic is richer and removed objective 5 is identifiable. "
            "ENGLAND remains a research prototype until original geometry is found.",
        )
    )
    s.append(PageBreak())

    section(s, "07", "Aircraft and vehicles: corrected inventory")
    s.append(
        P(
            "Searching only by common names produced false negatives. Internal spelling, spaces, and one typo explain several mistakes."
        )
    )
    s.append(
        table(
            [
                ["Element", "Local files", "Verdict"],
                ["Me 323", "LA_M323.4ds plus simplified version", "Model present; controllability unproven"],
                ["La-5", "la_La-5.4ds plus simplified version", "Model present; no identified mission"],
                ["Aichi Val", "la_aici.4ds plus simplified version", "Model present under shortened internal spelling"],
                ["Fa 223", "la_Fa 223.4ds plus simplified version", "Model present; the space hid the search result"],
                ["Ju 52", "12 resources and variants", "Present and called by an Africa 1 scene"],
                ["Fw 200", "Main plus simplified model", "Orphan or scenic asset"],
                ["Li-2", "Main plus simplified model", "Orphan or scenic asset"],
                ["DFS 230", "Internal name DSF 230", "Glider present under spelling variant"],
            ],
            [30 * mm, 65 * mm, 73 * mm],
        )
    )
    s.append(Spacer(1, 4 * mm))
    s.append(P("What the models prove", "h2"))
    s.append(
        P(
            "M323, La-5, Aichi, and Fa 223 contain named engines, propellers or rotors, moving surfaces, seats, and cameras. "
            "They are not flat scenery. However, no complete chain of controls, physics, damage, cockpit, AI, and flyable mission is yet proven."
        )
    )
    s.append(info_box("Correct classification", "Vehicle model present; historical playability claim; finished flyable vehicle not proven."))
    s.append(PageBreak())

    section(s, "08", "Weapons and equipment")
    s.append(
        table(
            [
                ["Element", "Trace", "Conclusion"],
                ["Benelli M4", "18 first-person animations, sounds, icon, texture, and ammunition 179", "Best additive candidate; object slot reused by the compass"],
                ["Vickers K", "Mounted and used on the SAS Jeep", "Active vehicle weapon, not a portable weapon"],
                ["Flammenwerfer 35", "Name and ammunition; no complete weapon model", "Announced and removed; reconstruction required"],
                ["Portable No. 2", "Name and ammunition; same missing chain", "Announced and removed"],
                ["flame1.4ds", "471 bytes, only object fire01", "Flame effect, not a flamethrower"],
                ["Garrote", "Named by the lead designer", "Announced weapon; complete local implementation unproven"],
                ["ZK-383", "Alpha/beta screenshot", "Credible visual clue, no playable chain found"],
                ["FG 42 / MG 34", "Orphan identifiers or ammunition", "Candidates, not proof of finished weapons"],
            ],
            [34 * mm, 65 * mm, 69 * mm],
        )
    )
    s.append(P("Why the flamethrowers cannot simply be enabled", "h2"))
    s.append(
        P(
            "A restoration would need a held and world model, animations, tank, sounds, range, damage, reactions, AI, "
            "and multiplayer synchronisation. A first implementation would be a modern experimental mod even though "
            "the names come from the original project."
        )
    )
    s.append(P("Sources", "h2"))
    s.append(P('<link href="https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/">GameSpot - pre-production interview with Thomas Pluharik</link>', "source"))
    s.append(P('<link href="https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655">Games.cz - arsenal announced in 2003</link>', "source"))
    s.append(P('<link href="https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/">Illusion Softworks interview, 2004</link>', "source"))
    s.append(PageBreak())

    section(s, "09", "Cut plot and scenes")
    s.append(
        table(
            [
                ["Element", "What is attested", "Limit"],
                ["Gary Bristol", "Announced team leader linked to Dunkirk and a continuous plot", "Dialogue and complete campaign absent"],
                ["Scarred Man", "Announced recurring opponent", "No confirmed named final equivalent"],
                ["Mr Murrau", "Jet-engine expert to protect across three missions", "Mission arc not found"],
                ["Bridge with train", "Shown or named among pre-release material", "Exact location and level unknown"],
                ["Warehouse", "Same cut-content and redesign dossier", "Studio answer is global, not item-specific"],
                ["London and Germany", "Locations announced in 2001", "A complete playable campaign is not proven"],
            ],
            [34 * mm, 76 * mm, 58 * mm],
        )
    )
    s.append(P("Project redesign", "h2"))
    s.append(
        P(
            "Sources describe an engine change, the departure of the lead designer in 2001, and a redirection of the project. "
            "Promised campaigns, objectives, cooperation, and vehicles may therefore have been removed, replaced, or redistributed."
        )
    )
    s.append(
        info_box(
            "Caution with the 2004 interview",
            "The studio broadly confirms that many pre-release elements changed or were removed. The answer does not separately "
            "confirm every bridge, train, or warehouse screenshot.",
        )
    )
    s.append(P("Sources", "h2"))
    s.append(P('<link href="https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf">Computer Gaming World 207 - Gary Bristol and Dunkirk</link>', "source"))
    s.append(P('<link href="https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655">Games.cz 2003 - redesign and locations</link>', "source"))
    s.append(P('<link href="https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/">Illusion Softworks 2004 - broad confirmation of cuts</link>', "source"))
    s.append(PageBreak())

    section(s, "10", "Corrections to the preliminary dossiers")
    s.append(
        P(
            "The two PDFs supplied at the beginning of the investigation were a starting point. Direct archive auditing requires these corrections."
        )
    )
    s.append(
        table(
            [
                ["Initial reading", "New evidence", "Revised classification"],
                ["No identifiable Me 323 or Aichi model", "LA_M323.4ds and la_aici.4ds found", "Models present"],
                ["Fa 223 missed by the filter", "la_Fa 223.4ds contains a space", "Model present"],
                ["Ju 52 and La-5 absent vehicles", "Models found; Ju 52 called in Africa 1", "Present, controllability unproven"],
                ["ALPS3_OBJ abandoned mission", "Sabre supplies the complete active variant", "Older branch, not a lost level"],
                ["ARDENS1_OBJ standalone prototype", "Complete Sabre version takes precedence", "Older branch"],
                ["Three impossible objectives", "Arctic 3 can be bypassed on one route", "Broken or inconsistent"],
                ["Six easter eggs", "Africa 4 retains a seventh disabled effect", "Seven in the base game"],
            ],
            [51 * mm, 65 * mm, 52 * mm],
        )
    )
    s.append(Spacer(1, 5 * mm))
    s.append(P("Main lesson", "h2"))
    s.append(
        P(
            "A common-name search is not enough. Case, spaces, internal misspellings, and simplified assets change the result. "
            "Every alleged absence must be checked against the full inventory, name variants, model contents, and scene references."
        )
    )
    s.append(PageBreak())

    section(s, "11", "Current status and roadmap")
    s.append(
        table(
            [
                ["Workstream", "Established", "Next step"],
                ["Network", "Master server reachable; configuration automated", "Display the list and join a game"],
                ["Official campaigns", "33 of 33 inventoried", "Search variants, branches, and objectives, not a missing final campaign"],
                ["Exploration", "82 official and 225 local loose trees checked", "Test edges, collision, and sectors mission by mission"],
                ["Objectives", "14 groups tracked and 73 detailed states", "Play alternate routes and save/reload"],
                ["Easter eggs", "Africa 1 and Africa 4 restored", "Validate in game; solve the Tutorial under 1.12"],
                ["Remnants", "Normandy3 Zone and Africa5 Prototype enabled", "AI, mode, and stability tests"],
                ["London", "Announced campaign separated from Poland", "Search for more assets before creating anything"],
                ["Prototypes", "ENGLAND and CASTLE1/2 classified", "CASTLE2 demonstration with objective 5"],
                ["Weapons", "Benelli prioritised; flamethrowers correctly diagnosed", "Separate additive prototype, then new models and behaviour"],
                ["Aircraft", "Exact models located", "Choose one aircraft and build a test bench"],
                ["Community", "CMP 2.6.5 integrated", "Review further packages one by one for licences and conflicts"],
            ],
            [42 * mm, 63 * mm, 63 * mm],
        )
    )
    s.append(Spacer(1, 4 * mm))
    s.append(P("Recommended order of work", "h2"))
    s.append(
        number_steps(
            [
                "In-game testing of network play, objectives, both restored easter eggs, and both prototypes.",
                "Make the Tutorial secret reachable under 1.12 without moving its original hiding place.",
                "Audit CASTLE2 against a related map and restore objective 5 in an isolated demonstration.",
                "Search alternate paths mission by mission, especially the French approaches and multi-action branches.",
                "Build a clearly labelled experimental flamethrower prototype.",
                "Study one aircraft at a time in a dedicated test mission.",
                "Begin an England or Gary Bristol campaign only when historical facts and new story material are kept separate.",
            ]
        )
    )
    s.append(PageBreak())

    section(s, "12", "Sources and traceability")
    sources = [
        ("RpR - online play and GameSpy redirection", "https://www.rprclan.com/hd2/play-online"),
        ("RpR - active servers and CMP 2.6.5", "https://rprclan.com/"),
        ("had2-cmp repository", "https://github.com/ehylla93/had2-cmp/"),
        ("GameSpot - pre-production interview", "https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/"),
        ("Gameswelt - interview of 9 March 2001", "https://www.gameswelt.de/hidden-dangerous-2/news/interview-mit-dem-chef-designer-61828"),
        ("Games.cz - preview of 7 June 2003", "https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655"),
        ("Computer Gaming World 207", "https://www.cgwmuseum.org/galleries/issues/cgw_207.pdf"),
        ("Illusion Softworks - 2004 interview", "https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/"),
        ("GameFAQs - six historical easter eggs", "https://gamefaqs.gamespot.com/pc/451072-hidden-and-dangerous-2/cheats"),
        ("H&amp;D 2 Wiki - easter eggs", "https://hd2.fandom.com/wiki/Easter_eggs"),
        ("RpR - alpha/beta archaeology", "https://www.rprclan.com/forum/22-general/2856-h-d2-lost-content-early-beta-alpha-things?start=36"),
    ]
    for name, url in sources:
        s.append(P(f'<link href="{url}">{name}</link>', "source"))
    s.append(Spacer(1, 5 * mm))
    s.append(
        info_box(
            "Local traceability",
            "Technical conclusions come from commercial archive inventories, comparisons between the base game, patch 1.12, "
            "and Sabre Squadron, and reproducible validations. No commercial game file is reproduced in this report.",
        )
    )
    s.append(P("Related documents", "h2"))
    s.append(
        P(
            "The separate player guide only explains how to trigger the secrets and reach hidden places. "
            "Detailed engineering notes remain in the project's docs folder."
        )
    )
    doc.build(s)
    return path


if __name__ == "__main__":
    print(build_report_en())
