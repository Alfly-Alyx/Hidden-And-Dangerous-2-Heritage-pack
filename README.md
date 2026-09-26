# Hidden & Dangerous 2 Heritage Pack

[**English**](README.md) · [Français](README_FR.md)

A restoration and expansion pack for **Hidden & Dangerous 2: Sabre Squadron 1.12**.

Heritage Pack brings online play back, repairs forgotten objectives and sequences, opens maps to free exploration, adds the large CMP community collection, and makes selected official remnants available as clearly labelled experiments.

> The original game is required and is not included.

[**Download the latest version**](https://github.com/Alfly-Alyx/Hidden-And-Dangerous-2-Heritage-pack/releases)

## What the pack adds

| Feature | Result in the game |
|---|---|
| Online play | Combines the established H&D2 community master and OpenSpy in one in-game list, removes duplicates, and enables DirectPlay when needed. |
| Unlocked missions | An optional setting immediately unlocks all 24 H&D2 missions and all 9 Sabre Squadron missions for the active profile. |
| Free exploration | Removes boundary warnings, mission failure, and invisible border walls without removing normal scenery collisions. |
| Restored game content | Restores parts of the original game that the final release no longer used: mission sections, optional objectives, dialogue, character animations, and alternate routes. |
| Easter eggs | Restores the Africa 1 and Africa 4 sequences disabled by update 1.12. |
| Community content | Checks the official CMP repository and installs or updates the latest available revision (currently 2.6.5 with 156 cooperative maps and missions). |
| Custom missions | Adds `Solo → Custom Missions`, with separate lists for player missions, multiplayer adaptations, and free exploration. The included manager scans the `CustomMissions` folder without replacing existing creations. |
| Solo adaptations | An optional setting builds 11 solo missions from cooperative missions and official objective variants already present in the installed game. They are clearly labelled and placed in `Multiplayer adaptations`. |
| Official remnants | Adds Africa5 Prototype and Normandy3 Zone to multiplayer with names that clearly show their experimental status. |
| Display setup | Detects the monitor and PC, applies the highest usable resolution, and adjusts quality to the machine’s performance. |
| Restore option | Backs up replaced files and can return the game to its previous state. |

The installer detects features that are already active. After installation or verification, completed options are automatically unticked.

Heritage Pack restores content designed for H&D2 but removed, disabled, or incorrectly connected in the final release. These are not new missions invented for the pack: the elements were already present in the original game files.

## Installation

1. Install **Hidden & Dangerous 2: Sabre Squadron** and update **1.12**.
2. Close the game.
3. Download `H-D2-Heritage-Pack-Setup.exe` from Releases.
4. Run it as administrator.
5. Check the game folder, choose your options, and select **Installer**.
6. Run the tool again and select **Vérifier l’état** if you want to confirm the result.

CMP 2.6.5 requires about **1.08 GB to download** and **3.12 GB once installed**. The installer checks the official repository, identifies its version and commit, and downloads only the selected official revision.

## Where to find the content

- Official campaigns and missions remain in the normal solo menus.
- CMP missions are under `Multiplayer → Create → LAN → Cooperation`.
- Open `Solo → Custom Missions` to access the three separate custom lists.
- The `Multiplayer adaptations` list contains solo versions of Alps 3 Objective, Ardennes 1 Objective, Brest Co-op, Burgundy 1–3 Co-op, Libya 1–3 Co-op, and Sicily 1–2 Co-op when the corresponding installer option is selected.
- To add a mission, place its folder containing `tree.klz` and its required files in `CustomMissions`, then run `HD2-Custom-Mission-Manager.exe` from the game root and select **Scan and install**. Existing advanced packages with `mission.json` remain supported.
- `PROTOTYPE - Africa5` is available in Deathmatch.
- `PROTOTYPE - Normandy3 Zone` is available in Occupation.

The two prototypes are playable remnants intended for exploration. They are not presented as completed solo missions.

## Separate release documents

These PDFs are separate downloads on the GitHub release page. The installer
does not copy or manage them in the game folder.

### For players

- [Secrets and easter eggs — French](output/pdf/HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf)
- [Secrets and easter eggs player guide — English](output/pdf/HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf)

The player guide explains how to trigger every documented secret and reach hidden locations without turning into an engine manual.

### The investigation

- [Discovery report — French](output/pdf/HD2-Rapport-des-Decouvertes.pdf)
- [Discovery report — English](output/pdf/HD2-Discovery-Report-EN.pdf)

The report tells the story of the findings: cut content, mission variants, London, forgotten objectives, prototypes, weapons, and vehicles found in the archives.

## Current status

Version **0.9.0** consolidates:

- exact detection of features that are already installed;
- one H&D2 server list assembled from the established community service and OpenSpy;
- the native custom-mission menu, its three separate categories, and automatic scanning of mission folders without a required manifest;
- automatic deployment of that in-game menu by the main Heritage Pack installer, even before a custom mission is added;
- optional creation and installation of 11 solo adaptations from the player’s own H&D2 archives, without replacing the original cooperative missions;
- original game content that no longer worked in the final release;
- free exploration applied to both prototypes as well;
- reversible installation and protection of player progress.

## What is not playable yet

The game archives retain fragments of removed content, but not always enough to simply switch it back on. This includes:

- the Tutorial secret, still disabled by version 1.12;
- the `ENGLAND`, `CASTLE1`, and `CASTLE2` mission fragments, including CASTLE objective 5;
- the former Gary Bristol storyline and the announced missions or campaigns in London/England, Germany, and Dunkirk;
- incomplete weapons: both flamethrowers, the garrote, and the ZK-383;
- aircraft and the Fa 223 found as models or scenery, but without a complete system for piloting them.

The missing parts — map sections, objectives, mission reactions, animations, or weapon and vehicle behaviour — must be recreated and tested before these contents can be presented as playable.

## Restoring the previous game

Run the installer again and choose **Restaurer**. Heritage Pack restores its backups and removes the additions it manages without overwriting progress made after installation.

## Reporting a problem

If a mission will not start, the game hangs, or an installed feature is detected incorrectly, open a [GitHub issue](https://github.com/Alfly-Alyx/Hidden-And-Dangerous-2-Heritage-pack/issues) and include the mission, game mode, and what appears on screen.

## Current licence

The H&D2 Heritage Pack code is currently released under [GPL-3.0-or-later](LICENSE). It may be used, modified, and shared, including commercially. A modified version that is distributed must remain under the GPL and keep its source code available.

This licence covers the Heritage Pack code, not the original game or community creations. The widescreen fix retains its MIT licence, and CMP maps remain attributed to their creators. Further details are available in [THIRD_PARTY.md](THIRD_PARTY.md) and the [community-content notice](docs/CONTENU_COMMUNAUTAIRE.md).

Moving the whole project to MIT would first require replacing the archive readers connected to the GPL-licensed **HD2unpacker** project.

## External components and their authors

The Heritage Pack brings together the following external creations and services:

- **Hidden & Dangerous 2 and Sabre Squadron** — created by **Illusion Softworks**. The commercial game is required and is never included in the pack.
- **Established H&D2 master-list service** — the solution is credited to **JarnoKai (Mökki Medium)** and **Ondra**; it is hosted and maintained by the **=RpR= clan**. **DnA (Hawk)** created the historical hosts-file updater presented by RpR.
- **OpenSpy network service** — developed and maintained by the **OpenSpy project contributors**. The Heritage Pack queries the service directly; the separate `openspy-client` DLL maintained by **anzz1** is not bundled because the local bridge does not require it.
- **GameSpy EnctypeX protocol implementation** — the local two-service bridge uses an adaptation of the GPL-2.0-or-later decoder/encoder published by **Luigi Auriemma**.
- **Community Map Package 2.6.5** — compiled and preserved by the **=RpR= clan**; its public `had2-cmp` repository is published by **ehylla93**. It is downloaded from that repository when the user selects it and is not stored in this installer.
- **CMP missions and maps** — **BetterYouThanMe, Black Akres, culticaxe, Dr_NO, GS Hawk, GUB, HippoBlindEye, Joe66, Joel, Lars, Matro, miamidos, Polanski, ProSabre, Rs_sabre, Sasha, Sqdn. Ldr. Ted Striker, Stern**, and **Zdenda** are the authors or converters named by the installed CMP credits.
- **HiddenandDangerous2.WidescreenFix** — created by **ThirteenAG** and included under the MIT licence.
- **HD2unpacker format research** — the DTA readers follow the public documentation and GPL-3.0 implementation by **M3tox**.
- **DirectPlay** — a legacy Windows component supplied by **Microsoft**. The installer can enable the copy already provided by Windows; it does not redistribute it.

**H&D2 Heritage Pack itself** was initiated by **Alfly-Alyx**. Its installer, restoration code, local list-merging bridge, custom-mission manager, restored scripts, tests and guides are released with this repository.

The map-by-map details remain available in `cmp_info/README.md`, installed with CMP. Some source entries have no named author or are marked unknown; Heritage Pack preserves that wording instead of inventing an attribution.

Sources: [RpR online-play page](https://www.rprclan.com/hd2/play-online), [OpenSpy](https://github.com/openspy), [CMP repository](https://github.com/ehylla93/had2-cmp), [Widescreen Fixes Pack](https://github.com/ThirteenAG/WidescreenFixesPack), and [HD2unpacker](https://github.com/M3tox/HD2unpacker).

Heritage Pack is an independent community project made to preserve and rediscover the game.
