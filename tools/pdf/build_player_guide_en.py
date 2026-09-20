from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Spacer, PageBreak
from pdf_common import OUT, HD2Doc, P, bullet, number_steps, info_box, table, section, cover, Africa4Map


def build_player_en():
    path = OUT / "HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf"
    doc = HD2Doc(str(path), "HD2 - Player guide to secrets")
    s = []
    cover(
        s,
        "Player guide - Edition 0.8.0",
        "Secrets and<br/>easter eggs",
        "Seven hidden sequences, their conditions, and the secret places used to reach them.",
        "Hidden &amp; Dangerous 2: Sabre Squadron 1.12<br/>Practical guide in English - 20 September 2026",
    )

    section(
        s,
        "01",
        "Before you begin",
        "This is a player guide. It explains how to find the secrets, not how the game engine or mission scripts work.",
    )
    s.append(
        info_box(
            "Recommended pack",
            "Install H&amp;D2 Heritage Pack 0.8.0 and keep the official easter egg option selected. "
            "It restores the Africa 1 and Africa 4 surprises that update 1.12 disabled.",
        )
    )
    s.append(Spacer(1, 4 * mm))
    s.append(P("Useful rules", "h2"))
    s.append(
        bullet(
            [
                "Save before the final action of every secret.",
                "Follow the stated order. Several triggers check their condition only once.",
                "Use the normal context action to carry a body or move an object.",
                "Do not enter the extraction point before finishing the secret.",
                "Some results are deliberately strange or macabre.",
            ]
        )
    )
    s.append(P("Quick reference", "h2"))
    s.append(
        table(
            [
                ["Mission", "Trigger", "Result"],
                ["Tutorial", "Switch, truck, gold bar", "Extra targets"],
                ["Africa 1", "Officer on the destroyed jeep", "Burning visitors"],
                ["Burma 1", "All enemies, then 3 skulls", "Procession and show"],
                ["Alps 1", "4 bodies on one rock", "Skeletal surprise"],
                ["Alps 2", "3 bars in 3 rooms, in order", "Burning skeletons"],
                ["Normandy 1", "10 bottles, then the drunk guard", "Hidden sequence"],
                ["Africa 4", "Bring keys A, B, and C together", "Meteor shower"],
            ],
            [32 * mm, 80 * mm, 56 * mm],
        )
    )
    s.append(PageBreak())

    section(s, "02", "Tutorial - The gold bar on the roof")
    s.append(
        number_steps(
            [
                "Complete the exercises through the grenade and anti-tank ranges to open the second training area.",
                "Drive the jeep toward the pool. Pass the truck on your right, turn left, and stop by the reception hut where the instructor is standing.",
                "Inside the hut, use the small red switch to the right of the desk.",
                "Complete the pool exercise before returning. Coming back too early can fail the mission.",
                "The truck in the car park now starts. Move it slightly, climb onto the bonnet, then the roof, and finally the garage roof. Pick up the gold bar in the far corner.",
                "Complete the explosives exercise. Return to the firing range, ignore the instructor, and leave through the door toward the fixed machine gun. Keep the gold bar in your inventory.",
            ]
        )
    )
    s.append(Spacer(1, 4 * mm))
    s.append(
        info_box(
            "Important under version 1.12",
            "Update 1.12 normally prevents climbing onto vehicles. The secret and gold bar still exist, "
            "but the historical route may remain inaccessible. Heritage Pack 0.8.0 does not move the bar, "
            "because that would invent a new hiding place.",
            colors.HexColor("#FFF1DD"),
        )
    )
    s.append(P("Why this matters", "h2"))
    s.append(
        P(
            "The garage roof is the original hiding place. Any future 1.12 solution should preserve that discovery, "
            "or clearly identify a replacement route as a modern reconstruction."
        )
    )
    s.append(PageBreak())

    section(s, "03", "Africa 1 - Spaghetti Airport")
    s.append(P("Goal: burn the jeep and the officer together to summon three visitors."))
    s.append(
        number_steps(
            [
                "Complete every objective except the final regrouping at the vehicle. Keep the jeep intact.",
                "Return to the main building and find the officer who tells you that Schumann has already left.",
                "Kill the officer and carry his body to the tents.",
                "Drive the jeep into the circular part of the trench immediately behind the tents, to the left of the runway.",
                "Climb onto the jeep and place the officer's body on it.",
                "Move away and destroy the jeep with a grenade. The three visitors appear in a fiery scene.",
            ]
        )
    )
    s.append(Spacer(1, 4 * mm))
    s.append(
        info_box(
            "What the trigger really requires",
            "The verified trigger checks the officer, the jeep, and their deaths at the correct location. "
            "The two red barrels mentioned in some older guides are not required.",
        )
    )
    s.append(P("Practical reward", "h2"))
    s.append(P("One visitor carries an MP44, giving you a chance to obtain the weapon very early in the campaign."))
    s.append(PageBreak())

    section(s, "04", "Burma 1 and Alps 1")
    s.append(P("Burma 1 - Anthill", "h2"))
    s.append(
        number_steps(
            [
                "Finish the mission without entering the extraction point.",
                "Kill every enemy, including soldiers in bunkers and isolated positions.",
                "Find and destroy the three skulls hidden around the map. Save the third for last: every enemy must already be dead when it breaks.",
                "Take a single soldier and follow the path toward extraction.",
                "Three figures appear among the ruins. Follow them to the camp where you destroyed the guns and watch the scene.",
            ]
        )
    )
    s.append(
        info_box(
            "If nothing happens",
            "An enemy is probably still alive, or the third skull was destroyed too early. Reload the save made before breaking it.",
            colors.HexColor("#FFF1DD"),
        )
    )
    s.append(Spacer(1, 5 * mm))
    s.append(P("Alps 1 - Babes in the Wood", "h2"))
    s.append(
        number_steps(
            [
                "Advance to the first T-junction, just before the road turns right toward the MG42 position.",
                "Wait for the half-track coming from the left road. Disable it with a few shots.",
                "Kill the four crew members when they dismount.",
                "Carry all four bodies onto the nearest large rock among the trees. Keep them close together in the centre.",
                "Continue the mission normally. A skeletal surprise waits farther ahead.",
            ]
        )
    )
    s.append(PageBreak())

    section(s, "05", "Alps 2 - Estate Agent")
    s.append(P("Three gold bars must be placed in three locations, in this exact order."))
    s.append(
        number_steps(
            [
                "After handing over the papers and speaking to the warehouse guards, enter the castle.",
                "Before meeting Salter, open the secret door behind the large fresco. Free some inventory space and collect at least two gold bars.",
                "In the library, drop the first gold bar before speaking to Salter.",
                "Return for another bar if needed, then speak to Salter and follow her.",
                "After the staircase marked Munition Lager, look at the large paintings on the right. The first one near the door hides a room. Let Salter open the next passage, pick the lock, and leave the second bar in the stolen paintings room.",
                "In the archives, leave the third gold bar in the room containing the file.",
                "Proceed to the courtyard and the truck to reveal the surprise.",
            ]
        )
    )
    s.append(P("Two hidden places to remember", "h2"))
    s.append(
        bullet(
            [
                "The door behind the large fresco hides the gold bar store.",
                "The door behind the first large painting on the right leads to the stolen paintings room.",
            ]
        )
    )
    s.append(
        info_box(
            "Mandatory order",
            "Library, stolen paintings room, archives. Each deposit arms the next trigger.",
        )
    )
    s.append(PageBreak())

    section(s, "06", "Normandy 1 - Lighthouse")
    s.append(
        P(
            "Break ten blue bottles. The tenth must be the bottle in the sleeping quarters beside Gesch D. "
            "Then kill the drunk guard."
        )
    )
    rows = [
        ["1", "Lower level: near two talking guards, in the office room, on the floor beside the desk."],
        ["2", "Explosives bag room: behind the breakable wooden cupboard doors."],
        ["3", "Sleeping quarters: under a bunk bed."],
        ["4", "Sleeping quarters: on top of a metal locker."],
        ["5", "On the shelf above the desk, behind the double doors marked Gesch B."],
        ["6", "Dining room: on a table."],
        ["7", "Kitchen: inside an open cupboard."],
        ["8", "Room marked Arzt: on top of the metal locker."],
        ["9", "Under the Gesch D sign, pass the grilles, turn left, then enter the room on the right: on the table."],
        ["10", "Sleeping quarters beside the previous room. Break this bottle last."],
    ]
    s.append(table([["No.", "Location"]] + rows, [12 * mm, 156 * mm]))
    s.append(Spacer(1, 3 * mm))
    s.append(
        info_box(
            "Final action",
            "After bottle 10, shoot the drunk guard. If he is already dead, reload a save.",
            colors.HexColor("#FFF1DD"),
        )
    )
    s.append(PageBreak())

    section(s, "07", "Africa 4 - The meteor shower")
    s.append(
        P(
            "This seventh easter egg is missing from historical guides because update 1.12 redirects its trigger. "
            "Heritage Pack restores the official branch, but the final deposit point still requires in-game confirmation."
        )
    )
    s.append(Africa4Map("en"))
    s.append(Spacer(1, 3 * mm))
    s.append(
        number_steps(
            [
                "Collect key A in the south-west part of the compound, near the small rooms and lower yard.",
                "Collect key B in the central-east sector, around the square building with the rounded feature.",
                "Collect key C in the north-east sector, near the open building or roof at the upper end of the compound.",
                "Keep all three keys together. The script requires every key to be within three metres of its activation point.",
                "First test the prone MG42 position north-east of key C. If nothing happens, reload your save.",
                "Then test the second official point separately, in the lower central part of the compound. Move clear and watch the sky.",
            ]
        )
    )
    s.append(
        info_box(
            "Procedure still being validated",
            "The same official script is connected to two different points. The files alone do not prove which one "
            "the 1.12 engine uses. A future edition will replace this double test with one visual landmark only after an in-game validation.",
            colors.HexColor("#FFF1DD"),
        )
    )
    s.append(PageBreak())

    section(s, "08", "Other confirmed hidden places")
    s.append(P("Whisky Bar - secret conversation", "h2"))
    s.append(
        P(
            "Approach the hangar quietly and listen to the officers without interrupting them. "
            "The reinforcement information completes the secret objective. The alleged bomb store is not confirmed."
        )
    )
    s.append(P("Final Showdown - radio truck switch", "h2"))
    s.append(
        P(
            "Inspect the side and underside of the radio truck. A small, easy-to-miss switch contributes to the progression."
        )
    )
    s.append(P("Lighthouse - both underground entrances", "h2"))
    s.append(
        P(
            "With the pack installed, the original guidance sequence once again shows both underground entrances. "
            "Compare the two approaches instead of following only one route."
        )
    )
    s.append(P("Poland / London_mp", "h2"))
    s.append(
        P(
            "The ruined city called London_mp in the files is the multiplayer map published as Poland. "
            "It is not a hidden London solo campaign, but its buildings contain many floors and firing lines to explore."
        )
    )
    s.append(P("Free exploration", "h2"))
    s.append(
        P(
            "The pack removes boundary warnings and failures. Save before travelling far: some outer areas have incomplete ground or no intended route."
        )
    )
    s.append(PageBreak())

    section(s, "09", "Secret hunter checklist")
    checks = [
        ["Tutorial", "Red switch used", "Gold bar kept until the machine gun"],
        ["Africa 1", "Jeep intact until the end", "Officer on it inside the trench"],
        ["Burma 1", "Every enemy dead", "Third skull broken last"],
        ["Alps 1", "Four crew members", "Four bodies on the same rock"],
        ["Alps 2", "Library", "Paintings room, then archives"],
        ["Normandy 1", "First nine bottles", "Bottle 10, then drunk guard"],
        ["Africa 4", "Keys A, B, and C", "Test the 2 official points separately"],
    ]
    s.append(table([["Mission", "Check 1", "Check 2"]] + checks, [32 * mm, 67 * mm, 69 * mm]))
    s.append(Spacer(1, 7 * mm))
    s.append(
        info_box(
            "Good hunting",
            "Burma 1, Alps 2, and Normandy 1 are the most order-sensitive secrets. "
            "Use Heritage Pack for Africa 1 and Africa 4. The Africa 4 deposit point and the Tutorial route still await final in-game validation.",
        )
    )
    s.append(Spacer(1, 8 * mm))
    s.append(P("Player sources", "h2"))
    s.append(
        P(
            '<link href="https://gamefaqs.gamespot.com/pc/451072-hidden-and-dangerous-2/cheats">'
            "GameFAQs - historical procedures for the six publicly known secrets</link>",
            "source",
        )
    )
    s.append(
        P(
            '<link href="https://hd2.fandom.com/wiki/Easter_eggs">'
            "H&amp;D 2 Wiki - community easter egg overview</link>",
            "source",
        )
    )
    s.append(
        P(
            "The conditions and the two owners of the seventh Africa 4 secret were verified in the 1.12 files. "
            "Its effective behaviour still requires an in-game test before final publication.",
            "source",
        )
    )
    doc.build(s)
    return path


if __name__ == "__main__":
    print(build_player_en())
