# Hidden & Dangerous 2 Heritage Pack

[Français](README.md) · [English](README_EN.md)

A restoration and expansion pack for **Hidden & Dangerous 2: Sabre Squadron 1.12**.

Heritage Pack brings online play back, repairs forgotten objectives and sequences, opens maps to free exploration, adds the large CMP community collection, and makes selected official remnants available as clearly labelled experiments.

> The original game is required and is not included.

[**Download the latest version**](https://github.com/Alfly-Alyx/Hidden-And-Dangerous-2-Heritage-pack/releases)

## What the pack adds

| Feature | Result in the game |
|---|---|
| Online play | Restores the community server list and enables DirectPlay when needed. |
| Unlocked missions | An optional setting immediately unlocks all 24 H&D2 missions and all 9 Sabre Squadron missions for the active profile. |
| Free exploration | Removes boundary warnings, mission failure, and invisible border walls without removing normal scenery collisions. |
| Restored game content | Restores parts of the original game that the final release no longer used: mission sections, optional objectives, dialogue, character animations, and alternate routes. |
| Easter eggs | Restores the Africa 1 and Africa 4 sequences disabled by update 1.12. |
| Community content | Installs CMP 2.6.5 with 156 cooperative maps and missions. |
| Official remnants | Adds Africa5 Prototype and Normandy3 Zone to multiplayer with names that clearly show their experimental status. |
| Display setup | Detects the monitor and PC, applies the highest usable resolution, and adjusts quality to the machine’s performance. |
| Guides | Installs two French guides and their English editions. |
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

CMP requires about **1.08 GB to download** and **3.12 GB once installed**. It is downloaded only when missing.

## Where to find the content

- Official campaigns and missions remain in the normal solo menus.
- CMP missions are under `Multiplayer → Create → LAN → Cooperation`.
- `PROTOTYPE - Africa5` is available in Deathmatch.
- `PROTOTYPE - Normandy3 Zone` is available in Occupation.
- All four PDFs are copied to the game’s `Guides` folder.

The two prototypes are playable remnants intended for exploration. They are not presented as completed solo missions.

## Included guides

### For players

- [Secrets and easter eggs — French](output/pdf/HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf)
- [Secrets and easter eggs player guide — English](output/pdf/HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf)

The player guide explains how to trigger every documented secret and reach hidden locations without turning into an engine manual.

### The investigation

- [Discovery report — French](output/pdf/HD2-Rapport-des-Decouvertes.pdf)
- [Discovery report — English](output/pdf/HD2-Discovery-Report-EN.pdf)

The report tells the story of the findings: cut content, mission variants, London, forgotten objectives, prototypes, weapons, and vehicles found in the archives.

## Current status

Version **0.7.6** consolidates:

- exact detection of features that are already installed;
- original game content that no longer worked in the final release;
- free exploration applied to both prototypes as well;
- all four PDF guides embedded in the installer;
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

## Credits

- **H&D2 Heritage Pack**: a project initiated by **Alfly-Alyx**.
- **Original game**: created by **Illusion Softworks**.
- **Online play**: **JarnoKai (Mökki Medium)** and **Ondra** are credited for the master-list solution; the **=RpR=** clan hosts and maintains it. **DnA (Hawk)** also created the historical hosts-file updater presented by RpR.
- **Community Map Package 2.6.5**: compiled and preserved by **=RpR=**, with the `had2-cmp` repository published by **ehylla93**.
- **CMP missions and maps**: **BetterYouThanMe, Black Akres, culticaxe, Dr_NO, GS Hawk, GUB, HippoBlindEye, Joe66, Joel, Lars, Matro, miamidos, Polanski, ProSabre, Rs_sabre, Sasha, Sqdn. Ldr. Ted Striker, Stern**, and **Zdenda** are the authors or converters named in the credits of the integrated version.
- **Widescreen support**: **ThirteenAG**, author of `HiddenandDangerous2.WidescreenFix`, distributed under the MIT licence.

The map-by-map details remain available in `cmp_info/README.md`, installed with CMP. Some source entries have no named author or are marked unknown; Heritage Pack preserves that wording instead of inventing an attribution.

Sources: [RpR online-play page](https://www.rprclan.com/hd2/play-online), [CMP repository](https://github.com/ehylla93/had2-cmp), and [Widescreen Fixes Pack](https://github.com/ThirteenAG/WidescreenFixesPack).

Heritage Pack is an independent community project made to preserve and rediscover the game.
