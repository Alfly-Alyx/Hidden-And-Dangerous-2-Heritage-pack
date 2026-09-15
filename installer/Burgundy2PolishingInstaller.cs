using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Burgundy2PolishingInstaller
    {
        private const string ScriptPath = "Scripts/BURGUNDY2/ge_dilna.scr";
        private static readonly string[] Archives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(gamePath, ScriptPath));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "Le polissage de Burgundy 2 semble deja restaure.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du polissage Burgundy 2 n'est pas idempotente.");
            ValidateSender(gamePath);
            return "Burgundy 2 verifie : le polisseur reprend son animation "
                + "apres le dialogue.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
                if (!File.Exists(target)) return false;
                ValidatePatched(File.ReadAllBytes(target));
                return true;
            }
            catch
            {
                return false;
            }
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Restauration du polissage de l'atelier dans Burgundy 2...");
            DormantSource source = ResolveSource(gamePath, ScriptPath);
            string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateSender(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Le polissage de Burgundy 2 est deja restaure.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, ScriptPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    ScriptPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Burgundy 2 : reprise du polissage restauree apres le dialogue.");
            InstallerCore.Report(progress,
                "Le polisseur de Burgundy 2 reprend de nouveau son travail.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatched(text))
            {
                ValidatePatched(data);
                return data;
            }

            Regex legacy = new Regex(
                @"(?<head>Whenever\s+lesti\s*\(\s*_SignalReceived\s*\(\s*)2"
                + @"(?<middle>\s*\)\s*\)\s*\{\s*//\s*animace\s+lesteni\s+qeru)"
                + @"(?<tail>\s*goto\s+end\s*;\s*\})",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
            if (legacy.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Gestionnaire dormant du polissage Burgundy 2 introuvable.");
            string eol = text.IndexOf("\r\n", StringComparison.Ordinal) >= 0
                ? "\r\n" : "\n";
            text = legacy.Replace(text, match =>
                match.Groups["head"].Value + "3"
                + match.Groups["middle"].Value + eol
                + "HUMAN_SetAnim(\"%%lestisamopal\", 500,500,1);"
                + match.Groups["tail"].Value, 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"Whenever\s+lesti\s*\(\s*_SignalReceived\s*\(\s*3\s*\)\s*\)"
                + @"\s*\{[\s\S]{0,180}HUMAN_SetAnim\s*\(\s*""%%lestisamopal""",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireCount(text,
                @"Whenever\s+lesti\s*\(\s*_SignalReceived\s*\(\s*3\s*\)\s*\)",
                1, "Le gestionnaire de reprise Burgundy 2 n'est pas unique.");
            Require(text,
                @"Whenever\s+lesti\s*\(\s*_SignalReceived\s*\(\s*3\s*\)\s*\)"
                + @"\s*\{[\s\S]{0,180}HUMAN_SetAnim\s*\(\s*""%%lestisamopal"""
                + @"\s*,\s*500\s*,\s*500\s*,\s*1\s*\)\s*;",
                "La reprise du polissage Burgundy 2 est incomplete.");
            Require(text,
                @"Whenever\s+kec\s*\(\s*_SignalReceived\s*\(\s*2\s*\)\s*\)"
                + @"\s*\{[\s\S]{0,120}HUMAN_SetAnim\s*\(\s*""""",
                "L'arret officiel du polissage Burgundy 2 a ete altere.");
            Require(text,
                @"HUMAN_ACTIVITY_Sit\s*\(\s*sit\s*\)\s*;[\s\S]{0,100}"
                + @"HUMAN_SetAnim\s*\(\s*""%%lestisamopal""",
                "L'initialisation officielle du polisseur est incomplete.");
        }

        private static void ValidateSender(string gamePath)
        {
            string sender = ReadText(ResolveSource(
                gamePath, "Scripts/BURGUNDY2/ge_motorka.scr"));
            Require(sender,
                @"SendSignal\s*\(\s*ge_dilna\s*,\s*2\s*\)\s*;\s*//\s*nelesti",
                "Le signal officiel d'arret du polissage est absent.");
            Require(sender,
                @"SendSignal\s*\(\s*ge_dilna\s*,\s*3\s*\)\s*;\s*//\s*lesti",
                "Le signal officiel de reprise du polissage est absent.");
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static void RequireCount(
            string text, string pattern, int expected, string message)
        {
            if (Regex.Matches(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline).Count != expected)
                throw new InvalidDataException(message);
        }

        private static DormantSource ResolveSource(
            string gamePath, string relative)
        {
            InstallerCore.ValidateGamePath(gamePath);
            DormantSource result = null;
            foreach (string archiveName in Archives)
            {
                string archivePath = Path.Combine(gamePath, archiveName);
                if (!File.Exists(archivePath))
                    throw new FileNotFoundException(
                        "Archive officielle manquante.", archivePath);
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                        if (String.Equals(
                            entry.Name.Replace((char)92, '/'), relative,
                            StringComparison.OrdinalIgnoreCase))
                            result = new DormantSource {
                                ArchivePath = archivePath,
                                EntryIndex = entry.Index
                            };
            }
            if (result == null)
                throw new InvalidDataException(
                    "Donnee officielle introuvable : " + relative);
            return result;
        }

        private static byte[] ReadSource(DormantSource source)
        {
            using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                return archive.Read(archive.Entries[source.EntryIndex]);
        }

        private static string ReadText(DormantSource source)
        {
            return Encoding.GetEncoding(1252).GetString(ReadSource(source));
        }

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}
