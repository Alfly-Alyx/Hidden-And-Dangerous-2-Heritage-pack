"""Integration checks for automatic H&D2 error reports and player guides."""
from pathlib import Path
import hashlib
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DiagnosticReportingTests(unittest.TestCase):
    def test_monitor_lifetime_is_tied_to_the_exact_game_process(self):
        monitor = (ROOT / "diagnostic-monitor/Program.cs").read_text(encoding="utf-8")
        menu = (ROOT / "native-custom-menu/CustomMenu.c").read_text(encoding="utf-8")
        self.assertIn('args[0] == "--watch-pid"', monitor)
        self.assertIn("Process.GetProcessById(watchedPid)", monitor)
        self.assertIn("CompleteSession(session, gamePath);", monitor)
        self.assertNotIn("CurrentVersion\\Run", monitor)
        self.assertIn("StartDiagnostics();", menu)
        self.assertIn("--watch-pid %lu", menu)
        self.assertIn("CreateProcessA", menu)
        self.assertIn('if (!stricmp(name, "HD2.exe")) return 1;', menu)

    def test_reports_cover_crashes_hangs_logs_context_and_manual_capture(self):
        monitor = (ROOT / "diagnostic-monitor/Program.cs").read_text(encoding="utf-8")
        for marker in (
            'new EventLog("Application")',
            '"CrashDumps"',
            '"Jeu bloque ou ne repondant plus depuis 20 secondes"',
            "Ctrl+Maj+F12",
            '"HD2.CustomMenu.log"',
            '"CUSTOM_MISSIONS_INSTALL.json"',
            "ZipFile.CreateFromDirectory",
            '"Envoi reseau : aucun"',
        ):
            self.assertIn(marker, monitor)

    def test_installer_embeds_and_tracks_the_monitor_and_wer_settings(self):
        build = (ROOT / "build.ps1").read_text(encoding="utf-8")
        core = (ROOT / "installer/InstallerCore.cs").read_text(encoding="utf-8")
        installer = (ROOT / "installer/DiagnosticMonitorInstaller.cs").read_text(
            encoding="utf-8")
        journal = (ROOT / "installer/StateJournal.cs").read_text(encoding="utf-8")
        self.assertIn("build-diagnostic-monitor.ps1", build)
        self.assertIn("HD2CommunityInstaller.DiagnosticMonitor.exe", build)
        self.assertIn("DiagnosticMonitorInstaller.Install", core)
        self.assertIn("DiagnosticMonitorInstaller.Uninstall", core)
        self.assertIn('key.SetValue("DumpType", 1', installer)
        self.assertIn('key.SetValue("DumpCount", 10', installer)
        self.assertIn("%LOCALAPPDATA%", installer)
        self.assertIn("DIAGNOSTIC_WER", journal)

    def test_downloaded_guide_hashes_match_the_published_local_pdfs(self):
        source = (ROOT / "installer/GuideDownloader.cs").read_text(encoding="utf-8")
        entries = re.findall(
            r'FileName = "([^"]+\.pdf)",\s*Sha256 = "([0-9A-F]{64})"',
            source,
        )
        self.assertEqual(len(entries), 4)
        for filename, expected in entries:
            with self.subTest(filename=filename):
                actual = hashlib.sha256((ROOT / "output/pdf" / filename).read_bytes())
                self.assertEqual(actual.hexdigest().upper(), expected)
        self.assertIn("CurrentUICulture.TwoLetterISOLanguageName", source)
        self.assertIn("Environment.SpecialFolder.DesktopDirectory", source)
        self.assertIn("raw.githubusercontent.com/Alfly-Alyx", source)
        self.assertNotIn("/master/output/pdf/", source)

    def test_custom_mission_report_maps_catalogue_rows_to_missions(self):
        source = (ROOT / "custom-mission-tool/MissionPackageCore.cs").read_text(
            encoding="utf-8")
        menu = (ROOT / "native-custom-menu/CustomMenu.c").read_text(encoding="utf-8")
        self.assertIn('report["mission_entries"]', source)
        self.assertIn('entry["catalogue"]', source)
        self.assertIn('entry["row"]', source)
        self.assertIn("mission-context catalogue=%u row=%u view=%u", menu)


if __name__ == "__main__":
    unittest.main()
