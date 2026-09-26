"""Wiring checks for the eleven Heritage Pack solo adaptations."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SoloAdaptationIntegrationTests(unittest.TestCase):
    def test_builder_defines_eleven_unique_packages_and_targets(self):
        source = (ROOT / "solo-mission-pack/SoloMissionPackBuilder.cs").read_text(
            encoding="utf-8")
        ids = re.findall(r'Id = "(heritage\.solo\.[^"]+)"', source)
        targets = re.findall(r'TargetMission = "(HP_Solo_[^"]+)"', source)
        self.assertEqual(len(ids), 11)
        self.assertEqual(len(set(ids)), 11)
        self.assertEqual(len(targets), 11)
        self.assertEqual(len(set(targets)), 11)

    def test_main_installer_builds_the_converter_into_the_custom_manager(self):
        build = (ROOT / "build-custom-mission-manager.ps1").read_text(
            encoding="utf-8")
        program = (ROOT / "custom-mission-tool/Program.cs").read_text(
            encoding="utf-8")
        core = (ROOT / "installer/InstallerCore.cs").read_text(encoding="utf-8")
        self.assertIn("solo-mission-pack\\SoloMissionPackBuilder.cs", build)
        self.assertIn("--export-heritage-solo", program)
        self.assertIn("SoloMissionAdaptationInstaller.Install", core)

    def test_no_standalone_commercial_archive_builder_remains(self):
        self.assertFalse((ROOT / "build-solo-mission-pack.ps1").exists())
        self.assertFalse((ROOT / "solo-mission-pack/Program.cs").exists())

    def test_menu_integration_uses_the_installed_custom_library(self):
        installer = (ROOT / "installer/CustomMissionManagerInstaller.cs").read_text(
            encoding="utf-8")
        self.assertIn('"--list-install-targets", library', installer)
        self.assertIn('"--integrate", library, gamePath, gamePath', installer)
        self.assertNotIn("HD2-Heritage-empty-menu", installer)

    def test_catalogue_templates_include_base_game_and_sabre_squadron(self):
        core = (ROOT / "custom-mission-tool/MissionPackageCore.cs").read_text(
            encoding="utf-8")
        self.assertIn("MissionTemplates(source, originalSource)", core)
        self.assertIn('ReadArchiveEntry(originalGame, "GameData\\\\Gamedata00.gdt")', core)


if __name__ == "__main__":
    unittest.main()
