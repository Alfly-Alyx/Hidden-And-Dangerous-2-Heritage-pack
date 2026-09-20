#!/usr/bin/env python3
"""Check that installer features are wired into validation, install and status paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


VALIDATE_RE = re.compile(
    r"Console\.WriteLine\((?P<class>[A-Za-z0-9_]+)\.ValidateOnly\("
)
INSTALL_RE = re.compile(
    r"^\s*(?P<class>[A-Za-z0-9_]+)\.Install\(", re.MULTILINE
)
STATUS_RE = re.compile(
    r"if\s*\(\s*(?P<class>[A-Za-z0-9_]+)\."
    r"Is[A-Za-z0-9_]*Active\(gamePath\)\s*\)\s*ready\+\+;"
)
OPTION_MAP = {
    "ConfigureMasterServer": "master",
    "EnableDirectPlay": "directPlay",
    "InstallCmp": "cmp",
    "FreeExploration": "exploration",
    "FixOptionalObjectives": "objectives",
    "RestoreDormantSequences": "dormant",
    "RestoreOfficialEasterEggs": "officialEasterEggs",
    "UnlockAllMissions": "unlockMissions",
    "AutoConfigureGraphics": "graphics",
}
HISTORICAL_ICON_SHA256 = (
    "9CB711B564CFD425C9D720EA2B39272C56283DD177D5AA9902B5FAD0414E7185"
)


def between(text: str, start: str, end: str, source: Path) -> str:
    begin = text.find(start)
    finish = text.find(end, begin + len(start))
    if begin < 0 or finish < 0:
        raise ValueError(f"Unable to isolate {start!r} in {source}")
    return text[begin:finish]


def duplicates(values: list[str]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})


def audit(root: Path) -> dict[str, object]:
    installer = root / "installer"
    program_path = installer / "Program.cs"
    core_path = installer / "InstallerCore.cs"
    status_path = installer / "FeatureStatusDetector.cs"
    config_path = installer / "Config.cs"
    main_form_path = installer / "MainForm.cs"
    graphics_path = installer / "GraphicsConfigurator.cs"
    easter_egg_path = installer / "Africa4EasterEggInstaller.cs"
    tree_patcher_path = installer / "TreeKlzPatcher.cs"
    objectives_path = installer / "ObjectiveFixInstaller.cs"
    czech2_carnage_path = installer / "Czech2CarnageFreibergInstaller.cs"
    czech2_smoke_path = installer / "Czech2CutsceneSmokeInstaller.cs"
    czech3_sequences_path = installer / "Czech3DormantSequencesInstaller.cs"
    africa5_storage_alarm_path = installer / "Africa5StorageAlarmInstaller.cs"
    africa5_schumann_path = installer / "Africa5SchumannAmbushInstaller.cs"
    africa5_dormant_actors_path = installer / "Africa5DormantActorsInstaller.cs"
    dta_archive_path = installer / "DtaArchive.cs"
    burgundy3_guard32_path = installer / "Burgundy3Guard32PatrolInstaller.cs"
    africa3_mechanic_path = installer / "Africa3MechanicCoverInstaller.cs"
    africa1_cards_path = installer / "Africa1CardPlayersInstaller.cs"
    africa1_ambient_routes_path = installer / "Africa1AmbientRoutesInstaller.cs"
    africa2_guard_signals_path = installer / "Africa2GuardSignalInstaller.cs"
    alps1_civil_alarm_path = installer / "Alps1CivilAlarmInstaller.cs"
    africa3_vehicle_path = installer / "Africa3VehicleDiscoveryInstaller.cs"
    arctic3_car_hit_path = installer / "Arctic3CarHitInstaller.cs"
    co_libye1_dialogues_path = installer / "CoLibye1DormantDialoguesInstaller.cs"
    arctic4_dog_patrol_path = installer / "Arctic4DogPatrolInstaller.cs"
    arctic4_ice_fall_path = installer / "Arctic4IceFallInstaller.cs"
    czech5_weather_path = installer / "Czech5WeatherInstaller.cs"
    assembly_path = installer / "AssemblyInfo.cs"
    build_path = root / "build.ps1"
    icon_path = installer / "assets" / "hd2-heritage-icon.ico"
    readme_path = root / "README.md"
    runtime_validation_path = root / "validation" / "runtime-validation.json"
    report_builder_path = root / "tools" / "pdf" / "build_report.py"
    player_guide_builder_path = root / "tools" / "pdf" / "build_player_guide.py"
    program = program_path.read_text(encoding="utf-8-sig")
    core = core_path.read_text(encoding="utf-8-sig")
    status = status_path.read_text(encoding="utf-8-sig")
    config = config_path.read_text(encoding="utf-8-sig")
    main_form = main_form_path.read_text(encoding="utf-8-sig")
    graphics = graphics_path.read_text(encoding="utf-8-sig")
    easter_eggs = easter_egg_path.read_text(encoding="utf-8-sig")
    tree_patcher = tree_patcher_path.read_text(encoding="utf-8-sig")
    objectives = objectives_path.read_text(encoding="utf-8-sig")
    czech2_carnage = czech2_carnage_path.read_text(encoding="utf-8-sig")
    czech2_smoke = czech2_smoke_path.read_text(encoding="utf-8-sig")
    czech3_sequences = czech3_sequences_path.read_text(encoding="utf-8-sig")
    africa5_storage_alarm = africa5_storage_alarm_path.read_text(
        encoding="utf-8-sig"
    )
    africa5_schumann = africa5_schumann_path.read_text(encoding="utf-8-sig")
    africa5_dormant_actors = africa5_dormant_actors_path.read_text(
        encoding="utf-8-sig"
    )
    dta_archive = dta_archive_path.read_text(encoding="utf-8-sig")
    burgundy3_guard32 = burgundy3_guard32_path.read_text(encoding="utf-8-sig")
    africa3_mechanic = africa3_mechanic_path.read_text(encoding="utf-8-sig")
    africa1_cards = africa1_cards_path.read_text(encoding="utf-8-sig")
    africa1_ambient_routes = africa1_ambient_routes_path.read_text(
        encoding="utf-8-sig"
    )
    africa2_guard_signals = africa2_guard_signals_path.read_text(
        encoding="utf-8-sig"
    )
    alps1_civil_alarm = alps1_civil_alarm_path.read_text(encoding="utf-8-sig")
    africa3_vehicle = africa3_vehicle_path.read_text(encoding="utf-8-sig")
    arctic3_car_hit = arctic3_car_hit_path.read_text(encoding="utf-8-sig")
    co_libye1_dialogues = co_libye1_dialogues_path.read_text(encoding="utf-8-sig")
    arctic4_dog_patrol = arctic4_dog_patrol_path.read_text(encoding="utf-8-sig")
    arctic4_ice_fall = arctic4_ice_fall_path.read_text(encoding="utf-8-sig")
    czech5_weather = czech5_weather_path.read_text(encoding="utf-8-sig")
    assembly = assembly_path.read_text(encoding="utf-8-sig")
    build = build_path.read_text(encoding="utf-8-sig")
    readme = readme_path.read_text(encoding="utf-8-sig")
    runtime_validation = json.loads(
        runtime_validation_path.read_text(encoding="utf-8-sig")
    )
    report_builder = report_builder_path.read_text(encoding="utf-8-sig")
    player_guide_builder = player_guide_builder_path.read_text(
        encoding="utf-8-sig"
    )
    mutation_sources = []
    unhashed_mutation_sources = []
    for source in sorted(installer.glob("*.cs")):
        if source.name == "InstallerCore.cs":
            continue
        content = source.read_text(encoding="utf-8-sig")
        if "InstallerCore.PrepareTarget(" not in content:
            continue
        mutation_sources.append(source.name)
        if ".RecordHash(" not in content:
            unhashed_mutation_sources.append(source.name)

    local_block = between(
        program,
        'if (command == "--self-test-local")',
        'if (command == "--self-test")',
        program_path,
    )
    full_block = between(
        program,
        'if (command == "--self-test")',
        'if (command == "--install")',
        program_path,
    )
    status_block = between(
        status,
        "private static string DetectDormantGuidance(string gamePath)",
        "private static string DetectEasterEggs(string gamePath)",
        status_path,
    )

    local = VALIDATE_RE.findall(local_block)
    full = VALIDATE_RE.findall(full_block)
    installed = INSTALL_RE.findall(core)
    status_classes = STATUS_RE.findall(status_block)
    status_checks = len(re.findall(r"\bready\+\+;", status_block))
    total_match = re.search(
        r"return\s+CountStatus\(ready,\s*(?P<total>\d+)\s*\);",
        status_block,
    )
    if total_match is None:
        raise ValueError("DetectDormantGuidance has no CountStatus total")
    declared_total = int(total_match.group("total"))

    errors: list[str] = []
    for label, values in (
        ("local self-test", local),
        ("full self-test", full),
        ("install", installed),
    ):
        repeated = duplicates(values)
        if repeated:
            errors.append(f"Duplicate classes in {label}: {', '.join(repeated)}")

    full_without_cmp = [name for name in full if name != "CmpInstaller"]
    if full_without_cmp != local:
        errors.append("Local and full self-tests differ beyond CmpInstaller")
    if full.count("CmpInstaller") != 1:
        errors.append("Full self-test must contain CmpInstaller exactly once")
    if "CmpInstaller" in local:
        errors.append("Local self-test must not require the external CMP archive")

    expected_full = set(installed) | {
        "DiagnosticStatusMatcher",
        "GraphicsConfigurator",
    }
    if set(full) != expected_full:
        missing = sorted(set(installed) - set(full))
        extra = sorted(set(full) - expected_full)
        if missing:
            errors.append("Installed without full self-test: " + ", ".join(missing))
        if extra:
            errors.append("Full self-test without install path: " + ", ".join(extra))

    missing_status_tests = sorted(set(status_classes) - set(local))
    missing_status_install = sorted(set(status_classes) - set(installed))
    if missing_status_tests:
        errors.append(
            "Status checks without local self-test: " + ", ".join(missing_status_tests)
        )
    if missing_status_install:
        errors.append(
            "Status checks without install path: " + ", ".join(missing_status_install)
        )
    if declared_total != status_checks:
        errors.append(
            f"Dormant status total is {declared_total}, but {status_checks} checks increment ready"
        )
    if unhashed_mutation_sources:
        errors.append(
            "Mutation sources without RecordHash: "
            + ", ".join(unhashed_mutation_sources)
        )
    if "journal.SealMissingHashes(options.GamePath)" not in core:
        errors.append("InstallerCore does not seal legacy missing hashes")
    updating = core.find("bool updating = File.Exists(AppConfig.StateFile);")
    update_preflight = core.find("EnsureSafeUpdate(options.GamePath);")
    open_journal = core.find("StateJournal.OpenExisting(options.GamePath)")
    safe_update_preflight = (
        min(updating, update_preflight, open_journal) >= 0
        and updating < update_preflight < open_journal
        and "List<string> conflicts = FindModifiedFiles(state);" in core
    )
    if not safe_update_preflight:
        errors.append("Updates do not check tracked-file conflicts before opening the journal")
    prototype_install = core.find("ExperimentalContentInstaller.Install(")
    cmp_install = core.find("CmpInstaller.Install(")
    loose_tree_pass = core.find("OfficialContentInstaller.PatchLooseMissionTrees(")
    exploration_postpass = (
        min(prototype_install, cmp_install, loose_tree_pass) >= 0
        and cmp_install < prototype_install < loose_tree_pass
    )
    if min(prototype_install, cmp_install, loose_tree_pass) < 0:
        errors.append("Exploration post-pass wiring is incomplete")
    elif not exploration_postpass:
        errors.append(
            "Prototypes must run after CMP and before the loose-tree exploration pass"
        )

    native_resolution_policy = all((
        "profile.Width = nativeWidth;" in graphics,
        "profile.Height = nativeHeight;" in graphics,
        "EnumDisplaySettings(null, EnumCurrentSettings" in graphics,
        "WriteInt32(updated, 2, profile.Width);" in graphics,
        "WriteInt32(updated, 6, profile.Height);" in graphics,
        "int maxWidth" not in graphics,
        "int maxHeight" not in graphics,
        "profile.Width > 3840" not in graphics,
        "profile.Height > 2160" not in graphics,
    ))
    if not native_resolution_policy:
        errors.append(
            "Graphics configuration must use the physical desktop resolution without a 4K cap"
        )
    graphics_integer_encoding = all((
        "data[offset] = (byte)(value & 0xFF);" in graphics,
        "data[offset + 1] = (byte)((value >> 8) & 0xFF);" in graphics,
        "data[offset + 2] = (byte)((value >> 16) & 0xFF);" in graphics,
        "data[offset + 3] = (byte)((value >> 24) & 0xFF);" in graphics,
        "ReadInt32(encodingProbe, 2) != profile.Width" in graphics,
        "ReadInt32(encodingProbe, 6) != profile.Height" in graphics,
        "Convert.ToByte(value" not in graphics,
    ))
    if not graphics_integer_encoding:
        errors.append(
            "Graphics integer encoding can overflow or lacks its round-trip self-test"
        )
    adaptive_quality_policy = all((
        "profile.GpuRamBytes" in graphics,
        "profile.RamBytes" in graphics,
        "profile.LogicalProcessors" in graphics,
        "bool dedicatedGpu" in graphics,
        "bool modernIntegratedGpu" in graphics,
        "int performance = 0;" in graphics,
    ))
    if not adaptive_quality_policy:
        errors.append("Graphics quality does not use CPU, RAM and GPU evidence")
    widescreen_install = core.find("WidescreenInstaller.Install(")
    graphics_apply = core.find("GraphicsConfigurator.Apply(")
    widescreen_before_resolution = (
        widescreen_install >= 0 and graphics_apply > widescreen_install
    )
    if not widescreen_before_resolution:
        errors.append("Widescreen support must be installed before applying resolution")

    africa4_exact_bindings = all((
        'registry, "dummy_ee", "AF3b_ee.scr"' in easter_eggs,
        '"dummy_ee_activator",' in easter_eggs,
        '"w_mg42Lie_00",' in easter_eggs,
        '"AF3b_ee_activator.scr"' in easter_eggs,
        "RegistryContainsBinding(" in easter_eggs,
    ))
    if not africa4_exact_bindings:
        errors.append(
            "Africa 4 validation does not require both commercial trigger owners"
        )

    boundary_object_policy = all((
        "private const byte MissionAreaMask = 0x60;" in tree_patcher,
        "RenameBoundaryLabels(data, stats);" in tree_patcher,
        "(byte)'H', (byte)'2', (byte)'B', (byte)'O', (byte)'R', (byte)'D'"
        in tree_patcher,
        "data[offset + 1] & ~MissionAreaMask" in tree_patcher,
    ))
    if not boundary_object_policy:
        errors.append(
            "Free exploration no longer clears area flags and border objects"
        )

    objective_validation_accepts_active = all((
        "int alreadyActive = 0;" in objectives,
        "if (BytesEqual(original, patched)) alreadyActive++;" in objectives,
        "BytesEqual(patched, PatchScript(relative, patched))" in objectives,
        "changed != ScriptPaths.Length" not in objectives,
    ))
    if not objective_validation_accepts_active:
        errors.append(
            "Objective validation no longer accepts a mixed active/pending game"
        )

    czech2_uses_commercial_hostility_sequence = all((
        '"Missions/CZECH2/actors.bin"' in czech2_carnage,
        '"Missions/CZECH2/scene2.bin"' not in czech2_carnage,
        "HUMAN_Suspend\\s*\\(\\s*0\\s*\\)" in czech2_carnage,
        "SetAlarmType\\s*\\(\\s*1023\\s*,\\s*1\\s*\\)" in czech2_carnage,
        "HUMAN_WeaponOnArm\\s*\\(\\s*1\\s*\\)" in czech2_carnage,
        "HUMAN_SETMODE_Crouch\\s*\\(\\s*\\)" in czech2_carnage,
        "HUMAN_SETAIMODE_Aggressive" not in czech2_carnage,
    ))
    if not czech2_uses_commercial_hostility_sequence:
        errors.append(
            "Czech 2 validation no longer follows the commercial hostility sequence"
        )

    czech2_smoke_requires_active_cleanup = all((
        '@"[\\s\\S]{0,160}^[ \\t]*FRM_DestroyIndexedParticle\\s*"'
        in czech2_smoke,
        'RegexOptions.IgnoreCase | RegexOptions.Multiline' in czech2_smoke,
    ))
    if not czech2_smoke_requires_active_cleanup:
        errors.append(
            "Czech 2 smoke detection can mistake the dormant comment for active code"
        )

    czech3_sequences_require_active_lines = all((
        czech3_sequences.count("ContainsOrderedActiveLines(text, new[]") == 2,
        "HasActiveLine(\n                    death.Groups[\"body\"].Value"
        in czech3_sequences,
        "Match found = activeLine.Match(text, offset);" in czech3_sequences,
        "CountActiveLines(text, instruction) != 1" in czech3_sequences,
    ))
    if not czech3_sequences_require_active_lines:
        errors.append(
            "Czech 3 dormant-sequence detection can mistake comments for active code"
        )

    africa5_storage_alarm_requires_active_lines = all((
        '@"\\k<indent>//[ \\t]*HUMAN_MoveToAlarm' in africa5_storage_alarm,
        '@"^[ \\t]*if\\s*\\(\\s*Atype' in africa5_storage_alarm,
        africa5_storage_alarm.count(
            '@"[\\s\\S]{0,180}^[ \\t]*HUMAN_'
        ) == 2,
        '@"[\\s\\S]{0,100}^[ \\t]*\\}[ \\t]*(?=\\r?$)"'
        in africa5_storage_alarm,
    ))
    if not africa5_storage_alarm_requires_active_lines:
        errors.append(
            "Africa 5 storage-alarm detection can mistake comments for active code"
        )

    africa5_schumann_requires_active_handlers = all((
        '@"^[ \\t]*OnCutscene\\s*\\(\\s*20' in africa5_schumann,
        '@"[\\s\\S]{0,160}?^[ \\t]*OnCutsceneDone' in africa5_schumann,
        '@"^[ \\t]*EndScript\\s*\\(\\s*\\)\\s*;"' in africa5_schumann,
        '@"(?m)^[ \\t]*HUMAN_Move\\s*"' in africa5_schumann,
        "RegexOptions.IgnoreCase | RegexOptions.Multiline" in africa5_schumann,
    ))
    if not africa5_schumann_requires_active_handlers:
        errors.append(
            "Africa 5 Schumann detection can mistake commented handlers for active code"
        )

    maps_archive_key = all((
        "identifier == 0xB438AB00U" in dta_archive,
        "key = 0xF26527FAB438D0A5UL;" in dta_archive,
        'Path.Combine(gamePath, "Maps.dta")' in africa5_dormant_actors,
    ))
    if not maps_archive_key:
        errors.append(
            "The installer cannot verify the preserved Africa 5 face in Maps.dta"
        )

    language_archive_key = all((
        "identifier == 0xA0A0B100U" in dta_archive,
        "key = 0xA0A0A0A0A0A0A0A0UL;" in dta_archive,
    ))
    if not language_archive_key:
        errors.append(
            "The installer cannot verify preserved dialogue in LangEnglish.dta"
        )

    remaining_commercial_archive_keys = all((
        "identifier == 0xB038DD00U" in dta_archive,
        "key = 0xF26520FAB038D1A1UL;" in dta_archive,
        "identifier == 0x5D804E00U" in dta_archive,
        "key = 0x10ACB2525D805259UL;" in dta_archive,
        "identifier == 0xEA859B00U" in dta_archive,
        "key = 0x65F7AB23EA85902AUL;" in dta_archive,
        "identifier == 0x4FE84300U" in dta_archive,
        "key = 0x8D2965CA4FE85106UL;" in dta_archive,
        "identifier == 0xA0A0A000U" in dta_archive,
        "key = 0xA0A0A0A0A0A0A0A2UL;" in dta_archive,
    ))
    if not remaining_commercial_archive_keys:
        errors.append("One or more installed commercial archive keys are missing")

    burgundy3_guard32_requires_active_patrol = all((
        '@"^[ \\t]*Label\\s+ACTIVITY_LOOP' in burgundy3_guard32,
        burgundy3_guard32.count(
            '@"[\\s\\S]{0,100}^[ \\t]*HUMAN_Move\\s*"'
        ) == 2,
        '@"[\\s\\S]{0,100}^[ \\t]*goto\\s+ACTIVITY_LOOP'
        in burgundy3_guard32,
    ))
    if not burgundy3_guard32_requires_active_patrol:
        errors.append(
            "Burgundy 3 guard-32 detection can mistake commented moves for a patrol"
        )

    africa3_mechanic_requires_active_cover = all((
        '@"^[ \\t]*if\\s*\\(\\s*Atype\\s*==\\s*64' in africa3_mechanic,
        '@"[\\s\\S]{0,500}^[ \\t]*below_car' in africa3_mechanic,
        '@"[\\s\\S]{0,50}^[ \\t]*\\}[ \\t]*(?=\\r?$)"'
        in africa3_mechanic,
    ))
    if not africa3_mechanic_requires_active_cover:
        errors.append(
            "Africa 3 mechanic detection can mistake its commented cover branch for code"
        )

    africa1_cards_require_complete_active_loop = all((
        '@"^[ \\t]*HUMAN_ACTIVITY_Card' in africa1_cards,
        '@"^[ \\t]*goto[ \\t]+END\\s*;"' in africa1_cards,
        'Label[ \\t]+LOOP[ \\t]*:|Delay' in africa1_cards,
        "RegexOptions.IgnoreCase | RegexOptions.Multiline" in africa1_cards,
    ))
    if not africa1_cards_require_complete_active_loop:
        errors.append(
            "Africa 1 card-player detection can mistake its commented loop for code"
        )

    africa1_ambient_routes_accept_mixed_active_state = all((
        "if (!BytesEqual(mechanic, patchedMechanic)) pending++;"
        in africa1_ambient_routes,
        "if (!BytesEqual(patrol, patchedPatrol)) pending++;"
        in africa1_ambient_routes,
        "|| BytesEqual(patrol, patchedPatrol)" not in africa1_ambient_routes,
    ))
    africa1_patrol_requires_active_route = all((
        '@"^[ \\t]*OnAlarmDone' in africa1_ambient_routes,
        '@"^[ \\t]*Label[ \\t]+LOOP' in africa1_ambient_routes,
        africa1_ambient_routes.count('@"^[ \\t]*HUMAN_Move') >= 4,
        '@"^[ \\t]*goto[ \\t]+LOOP' in africa1_ambient_routes,
        "RegexOptions.IgnoreCase | RegexOptions.Multiline"
        in africa1_ambient_routes,
    ))
    if not africa1_ambient_routes_accept_mixed_active_state:
        errors.append("Africa 1 route validation rejects a mixed active state")
    if not africa1_patrol_requires_active_route:
        errors.append(
            "Africa 1 patrol detection can mistake its commented route for code"
        )

    africa2_excludes_missing_guard03_actor = all((
        '"Scripts/AFRICA2/AF2_01_cardet.scr"' not in africa2_guard_signals,
        "PatchGuard03Connections" not in africa2_guard_signals,
        "PatchRegistry" not in africa2_guard_signals,
        "WriteRegistryField" not in africa2_guard_signals,
        'return ReplaceSignal(data, "af2_02", 5, 20);'
        in africa2_guard_signals,
        'return ReplaceSignal(data, "en05", 20, 5);'
        in africa2_guard_signals,
        "AF2_03 reste exclu car son acteur commercial est absent"
        in africa2_guard_signals,
    ))
    if not africa2_excludes_missing_guard03_actor:
        errors.append(
            "Africa 2 can reconnect AF2_03 even though its commercial actor is absent"
        )

    alps1_civil_uses_actor_registry = all((
        '"Missions/ALPS1/scene2.bin", MissionArchives,' in alps1_civil_alarm,
        'new[] { "ci03alarmer", "ci03alarmer1" });' in alps1_civil_alarm,
        '"Missions/ALPS1/actors.bin", MissionArchives,' in alps1_civil_alarm,
        'new[] { "ci_03" });' in alps1_civil_alarm,
        'new[] { "ci03alarmer", "ci03alarmer1", "ci_03" }'
        not in alps1_civil_alarm,
    ))
    if not alps1_civil_uses_actor_registry:
        errors.append("Alps 1 civil validation does not use the actor registry")

    later_actor_validations_use_actor_registries = all((
        '"Missions/AFRICA3/scene2.bin", MissionArchives,' in africa3_vehicle,
        'new[] { "AF3a_obj2" });' in africa3_vehicle,
        '"Missions/AFRICA3/actors.bin", MissionArchives,' in africa3_vehicle,
        'new[] { "La_OpelAf2", "AF3a_21" });' in africa3_vehicle,
        '"Missions/ARCTIC3/actors.bin", MissionArchives,' in arctic3_car_hit,
        '"Missions/ARCTIC3/scene2.bin", MissionArchives,' not in arctic3_car_hit,
    ))
    if not later_actor_validations_use_actor_registries:
        errors.append(
            "Africa 3 or Arctic 3 actor validation still targets scene2.bin"
        )

    co_libye1_end_signals_use_script_variables = all((
        "dialogue.VariableA," in co_libye1_dialogues,
        "dialogue.VariableB" in co_libye1_dialogues,
        "dialogue.ActorA.ToLowerInvariant()" not in co_libye1_dialogues,
        "dialogue.ActorB.ToLowerInvariant()" not in co_libye1_dialogues,
    ))
    if not co_libye1_end_signals_use_script_variables:
        errors.append(
            "Co_Libye1 dialogue completion checks actor names instead of script variables"
        )

    co_libye1_controller_uses_scene_registry = all((
        '"Missions/Co_Libye1/actors.bin"' in co_libye1_dialogues,
        '"Missions/Co_Libye1/scene2.bin"' in co_libye1_dialogues,
        "ContainsNullTerminated(actors, dialogue.Controller)"
        not in co_libye1_dialogues,
        "ContainsNullTerminated(scene, dialogue.Controller)"
        in co_libye1_dialogues,
    ))
    if not co_libye1_controller_uses_scene_registry:
        errors.append(
            "Co_Libye1 dialogue controller is not validated in scene2.bin"
        )

    arctic4_dog_patrol_requires_active_walk = all((
        arctic4_dog_patrol.count(
            '@"^[ \\t]*Label\\s+DeAlarm'
        ) == 2,
        arctic4_dog_patrol.count(
            '@"^[ \\t]*HUMAN_SETMODE_Walk'
        ) == 2,
        arctic4_dog_patrol.count(
            '@"[\\s\\S]{0,100}^[ \\t]*Label\\s+loop'
        ) == 2,
    ))
    if not arctic4_dog_patrol_requires_active_walk:
        errors.append(
            "Arctic 4 dog-patrol detection can mistake the test comment for walking"
        )

    arctic4_ice_fall_requires_active_explosion = all((
        '@"^[ \\t]*OnSignal\\s*\\(\\s*1' in arctic4_ice_fall,
        '@"^[ \\t]*MakeExplosion\\s*"' in arctic4_ice_fall,
        '@"[\\s\\S]{0,140}^[ \\t]*SetActorState\\s*"'
        in arctic4_ice_fall,
    ))
    if not arctic4_ice_fall_requires_active_explosion:
        errors.append(
            "Arctic 4 ice-fall detection can mistake its commented explosion for code"
        )

    czech5_weather_accepts_mixed_active_state = all((
        "int pending = 0;" in czech5_weather,
        "BytesEqual(weatherOriginal, weatherPatched)) pending++;"
        in czech5_weather,
        "BytesEqual(lightningOriginal, lightningPatched)) pending++;"
        in czech5_weather,
        "|| BytesEqual(lightningOriginal, lightningPatched)" not in czech5_weather,
    ))
    czech5_lightning_requires_active_loop = all((
        '@"(?m)^[ \\t]*integer\\s+time' in czech5_weather,
        '@"^[ \\t]*frame\\s+lightning' in czech5_weather,
        '@"[\\s\\S]{0,120}^[ \\t]*THUNDERSTORM_SetOn\\s*"'
        in czech5_weather,
        '@"[\\s\\S]{0,100}^[ \\t]*goto\\s+loop\\s*;"'
        in czech5_weather,
    ))
    if not czech5_weather_accepts_mixed_active_state:
        errors.append("Czech 5 weather validation rejects a mixed active state")
    if not czech5_lightning_requires_active_loop:
        errors.append(
            "Czech 5 lightning detection can mistake the commented loop for code"
        )

    historical_icon = (
        icon_path.is_file()
        and hashlib.sha256(icon_path.read_bytes()).hexdigest().upper()
        == HISTORICAL_ICON_SHA256
    )
    artifact_identity = all((
        historical_icon,
        "installer\\assets\\hd2-heritage-icon.ico" in build,
        '"/win32icon:$icon"' in build,
        "H-D2-Heritage-Pack-Setup.exe" in build,
        'AssemblyTitle("H&D2 Heritage Pack Installer")' in assembly,
        'AssemblyProduct("H&D2 Heritage Pack")' in assembly,
        'Text = "Hidden & Dangerous 2 - Heritage Pack"' in main_form,
    ))
    if not artifact_identity:
        errors.append(
            "Final setup name, historical icon or Windows identity is not wired"
        )

    version_match = re.search(
        r'public const string Version\s*=\s*"([^"]+)"', config
    )
    assembly_match = re.search(
        r'AssemblyFileVersion\("([^"]+)"\)', assembly
    )
    readme_match = re.search(
        r"(?:La version|Version)\s+\*{0,2}([0-9.]+)\*{0,2}", readme
    )
    version = version_match.group(1) if version_match else None
    expected_assembly = version + ".0" if version else None
    version_consistency = bool(
        version
        and assembly_match
        and assembly_match.group(1) == expected_assembly
        and readme_match
        and readme_match.group(1) == version
        and runtime_validation.get("milestone") == version
        and f"Révision {version}" in report_builder
        and f"Edition {version}" in player_guide_builder
    )
    if not version_consistency:
        errors.append(
            "Installer, assembly, README, runtime register and PDF sources "
            "do not share the same version"
        )

    declared_options = set(re.findall(r"public bool ([A-Za-z0-9_]+)\s*=", config))
    expected_options = set(OPTION_MAP)
    if declared_options != expected_options:
        missing = sorted(expected_options - declared_options)
        extra = sorted(declared_options - expected_options)
        if missing:
            errors.append("Expected InstallOptions missing: " + ", ".join(missing))
        if extra:
            errors.append("Unmapped InstallOptions: " + ", ".join(extra))
    detected_block = between(
        main_form,
        "private void ApplyDetectedState(string diagnostic)",
        "private void AppendLog(string message)",
        main_form_path,
    )
    busy_block = main_form[main_form.find("private void SetBusy(bool busy)") :]
    for option, checkbox in OPTION_MAP.items():
        if not re.search(
            rf"\b{re.escape(option)}\s*=\s*{re.escape(checkbox)}\.Checked\b",
            main_form,
        ):
            errors.append(f"{option} is not assigned from {checkbox}.Checked")
        if not re.search(rf"\boptions\.{re.escape(option)}\b", core):
            errors.append(f"{option} is not consumed by InstallerCore")
        if not re.search(rf"\b{re.escape(checkbox)}\.Checked\s*=", detected_block):
            errors.append(f"{checkbox} is not refreshed by detected state")
        if not re.search(rf"\b{re.escape(checkbox)}\.Checked\s*=\s*true\s*;", main_form):
            errors.append(f"{checkbox} has no enabled default")
        if not re.search(rf"\b{re.escape(checkbox)}\.Enabled\s*=\s*!busy\s*;", busy_block):
            errors.append(f"{checkbox} is not locked while the installer is busy")
    browse_block = between(
        main_form,
        "private void BrowseClick(object sender, EventArgs e)",
        "private async void InstallClick(object sender, EventArgs e)",
        main_form_path,
    )
    if "RunDiagnostic();" not in browse_block:
        errors.append("Choosing another game folder does not refresh detected state")

    return {
        "ok": not errors,
        "local_self_tests": len(local),
        "full_self_tests": len(full),
        "install_calls": len(installed),
        "dormant_status_checks": status_checks,
        "dormant_status_total": declared_total,
        "status_installer_classes": len(set(status_classes)),
        "mutation_sources": len(mutation_sources),
        "unhashed_mutation_sources": unhashed_mutation_sources,
        "interface_options": len(OPTION_MAP),
        "exploration_postpass": exploration_postpass,
        "safe_update_preflight": safe_update_preflight,
        "native_resolution_policy": native_resolution_policy,
        "graphics_integer_encoding": graphics_integer_encoding,
        "adaptive_quality_policy": adaptive_quality_policy,
        "widescreen_before_resolution": widescreen_before_resolution,
        "africa4_exact_bindings": africa4_exact_bindings,
        "boundary_object_policy": boundary_object_policy,
        "objective_validation_accepts_active": objective_validation_accepts_active,
        "czech2_uses_commercial_hostility_sequence": (
            czech2_uses_commercial_hostility_sequence
        ),
        "czech2_smoke_requires_active_cleanup": (
            czech2_smoke_requires_active_cleanup
        ),
        "czech3_sequences_require_active_lines": (
            czech3_sequences_require_active_lines
        ),
        "africa5_storage_alarm_requires_active_lines": (
            africa5_storage_alarm_requires_active_lines
        ),
        "africa5_schumann_requires_active_handlers": (
            africa5_schumann_requires_active_handlers
        ),
        "maps_archive_key": maps_archive_key,
        "language_archive_key": language_archive_key,
        "remaining_commercial_archive_keys": remaining_commercial_archive_keys,
        "burgundy3_guard32_requires_active_patrol": (
            burgundy3_guard32_requires_active_patrol
        ),
        "africa3_mechanic_requires_active_cover": (
            africa3_mechanic_requires_active_cover
        ),
        "africa1_cards_require_complete_active_loop": (
            africa1_cards_require_complete_active_loop
        ),
        "africa1_ambient_routes_accept_mixed_active_state": (
            africa1_ambient_routes_accept_mixed_active_state
        ),
        "africa1_patrol_requires_active_route": (
            africa1_patrol_requires_active_route
        ),
        "africa2_excludes_missing_guard03_actor": (
            africa2_excludes_missing_guard03_actor
        ),
        "alps1_civil_uses_actor_registry": alps1_civil_uses_actor_registry,
        "later_actor_validations_use_actor_registries": (
            later_actor_validations_use_actor_registries
        ),
        "co_libye1_end_signals_use_script_variables": (
            co_libye1_end_signals_use_script_variables
        ),
        "co_libye1_controller_uses_scene_registry": (
            co_libye1_controller_uses_scene_registry
        ),
        "arctic4_dog_patrol_requires_active_walk": (
            arctic4_dog_patrol_requires_active_walk
        ),
        "arctic4_ice_fall_requires_active_explosion": (
            arctic4_ice_fall_requires_active_explosion
        ),
        "czech5_weather_accepts_mixed_active_state": (
            czech5_weather_accepts_mixed_active_state
        ),
        "czech5_lightning_requires_active_loop": (
            czech5_lightning_requires_active_loop
        ),
        "historical_icon": historical_icon,
        "artifact_identity": artifact_identity,
        "version": version,
        "version_consistency": version_consistency,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of tools)",
    )
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.root.resolve())
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
