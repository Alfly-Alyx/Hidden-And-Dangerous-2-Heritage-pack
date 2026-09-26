using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace HD2CommunityInstaller
{
    internal static class DiagnosticMonitorInstaller
    {
        private const string ExecutableResource =
            "HD2CommunityInstaller.DiagnosticMonitor.exe";
        private const string HashResource =
            "HD2CommunityInstaller.DiagnosticMonitor.sha256";
        private const string RelativePath = "HD2-Heritage-Diagnostics.exe";
        private const string LocalDumpsPath =
            @"SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps";
        private const string DumpFolderValue =
            @"%LOCALAPPDATA%\HD2 Heritage Pack\Reports\CrashDumps";
        private static readonly string[] GameExecutables = {
            "HD2_SabreSquadron.exe", "HD2.exe"
        };

        public static string ReportsRoot
        {
            get
            {
                return Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "HD2 Heritage Pack", "Reports");
            }
        }

        public static string ValidateOnly()
        {
            byte[] executable = ReadResource(ExecutableResource);
            string expected = ExpectedHash();
            if (!String.Equals(expected, ComputeSha256(executable),
                    StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "L'empreinte du moniteur de diagnostics est invalide.");
            return "Moniteur de diagnostics verifie : lancement et arret lies au jeu, "
                + "rapports locaux et minidumps Windows.";
        }

        public static string DetectStatus(string gamePath)
        {
            string target = InstallerCore.SafeGameTarget(gamePath, RelativePath);
            if (!File.Exists(target)) return "a installer";
            try
            {
                if (!String.Equals(CmpInstaller.ComputeSha256(target), ExpectedHash(),
                        StringComparison.OrdinalIgnoreCase))
                    return "fichier modifie";
            }
            catch (Exception error) { return "indetermine (" + error.Message + ")"; }
            int configured = 0;
            foreach (string executable in GameExecutables)
                if (IsWerConfigured(executable)) configured++;
            if (configured == GameExecutables.Length)
                return "deja actif (demarre et s'arrete avec le jeu)";
            return "actif, minidumps Windows partiels (" + configured + "/"
                + GameExecutables.Length + ")";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Installation des rapports automatiques lies au jeu...");
            byte[] executable = ReadResource(ExecutableResource);
            string expected = ExpectedHash();
            if (!String.Equals(expected, ComputeSha256(executable),
                    StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "L'empreinte du moniteur de diagnostics est invalide.");

            string target = InstallerCore.SafeGameTarget(gamePath, RelativePath);
            InstallerCore.PrepareTarget(
                gamePath, RelativePath, target, journal, prepared);
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, executable);
                if (!String.Equals(expected, CmpInstaller.ComputeSha256(temporary),
                        StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "Le moniteur de diagnostics extrait est corrompu.");
                File.Copy(temporary, target, true);
                journal.RecordHash(RelativePath, expected);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }

            Directory.CreateDirectory(ReportsRoot);
            Directory.CreateDirectory(Path.Combine(ReportsRoot, "CrashDumps"));
            foreach (string name in GameExecutables)
                ConfigureWer(name, journal, progress);
            InstallerCore.Report(progress,
                "Rapports automatiques actifs uniquement pendant le jeu; "
                + "Ctrl+Maj+F12 cree un rapport manuel en mission.");
        }

        public static void Uninstall(InstallState state, Action<string> progress)
        {
            if (state.DiagnosticWerKeys.Count == 0) return;
            InstallerCore.Report(progress,
                "Retrait de la capture de minidumps ajoutee par Heritage Pack...");
            foreach (DiagnosticWerChange change in state.DiagnosticWerKeys)
                RemoveWer(change);
            InstallerCore.Report(progress,
                "Les rapports deja crees sont conserves dans " + ReportsRoot + ".");
        }

        private static void ConfigureWer(
            string executable, StateJournal journal, Action<string> progress)
        {
            RegistryView view = Environment.Is64BitOperatingSystem
                ? RegistryView.Registry64 : RegistryView.Registry32;
            using (RegistryKey root = RegistryKey.OpenBaseKey(
                RegistryHive.LocalMachine, view))
            using (RegistryKey localDumps = root.CreateSubKey(LocalDumpsPath))
            {
                using (RegistryKey existing = localDumps.OpenSubKey(executable, false))
                {
                    if (existing != null)
                    {
                        if (!MatchesWer(existing))
                            InstallerCore.Report(progress,
                                "Configuration Windows Error Reporting existante conservee pour "
                                + executable + ".");
                        return;
                    }
                }
                using (RegistryKey key = localDumps.CreateSubKey(executable))
                {
                    key.SetValue("DumpFolder", DumpFolderValue,
                        RegistryValueKind.ExpandString);
                    key.SetValue("DumpCount", 10, RegistryValueKind.DWord);
                    key.SetValue("DumpType", 1, RegistryValueKind.DWord);
                }
                journal.RecordDiagnosticWerKey(
                    view == RegistryView.Registry64 ? "64" : "32", executable);
            }
        }

        private static void RemoveWer(DiagnosticWerChange change)
        {
            RegistryView view = change.RegistryView == "64"
                ? RegistryView.Registry64 : RegistryView.Registry32;
            using (RegistryKey root = RegistryKey.OpenBaseKey(
                RegistryHive.LocalMachine, view))
            using (RegistryKey localDumps = root.OpenSubKey(LocalDumpsPath, true))
            {
                if (localDumps == null) return;
                using (RegistryKey key = localDumps.OpenSubKey(change.Executable, true))
                {
                    if (key == null) return;
                    DeleteIfUnchanged(key, "DumpFolder", DumpFolderValue);
                    DeleteIfUnchanged(key, "DumpCount", 10);
                    DeleteIfUnchanged(key, "DumpType", 1);
                    if (key.GetValueNames().Length != 0
                        || key.GetSubKeyNames().Length != 0) return;
                }
                localDumps.DeleteSubKey(change.Executable, false);
            }
        }

        private static void DeleteIfUnchanged(
            RegistryKey key, string name, object expected)
        {
            object current = key.GetValue(name, null,
                RegistryValueOptions.DoNotExpandEnvironmentNames);
            if (current != null && String.Equals(
                    Convert.ToString(current), Convert.ToString(expected),
                    StringComparison.OrdinalIgnoreCase))
                key.DeleteValue(name, false);
        }

        private static bool IsWerConfigured(string executable)
        {
            RegistryView view = Environment.Is64BitOperatingSystem
                ? RegistryView.Registry64 : RegistryView.Registry32;
            try
            {
                using (RegistryKey root = RegistryKey.OpenBaseKey(
                    RegistryHive.LocalMachine, view))
                using (RegistryKey key = root.OpenSubKey(
                    LocalDumpsPath + "\\" + executable))
                    return key != null && MatchesWer(key);
            }
            catch { return false; }
        }

        private static bool MatchesWer(RegistryKey key)
        {
            object folder = key.GetValue("DumpFolder", null,
                RegistryValueOptions.DoNotExpandEnvironmentNames);
            return String.Equals(Convert.ToString(folder), DumpFolderValue,
                    StringComparison.OrdinalIgnoreCase)
                && Convert.ToInt32(key.GetValue("DumpCount", 0)) == 10
                && Convert.ToInt32(key.GetValue("DumpType", 0)) == 1;
        }

        private static string ExpectedHash()
        {
            return Encoding.ASCII.GetString(ReadResource(HashResource)).Trim();
        }

        private static byte[] ReadResource(string name)
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(name))
            {
                if (stream == null)
                    throw new InvalidDataException("Ressource integree absente : " + name);
                using (MemoryStream copy = new MemoryStream())
                {
                    stream.CopyTo(copy);
                    return copy.ToArray();
                }
            }
        }

        private static string ComputeSha256(byte[] data)
        {
            using (SHA256 hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(data)).Replace("-", "");
        }
    }
}
