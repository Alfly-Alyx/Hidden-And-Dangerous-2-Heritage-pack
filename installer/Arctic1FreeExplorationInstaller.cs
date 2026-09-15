using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Arctic1FreeExplorationInstaller
    {
        private const string ScriptPath =
            "Scripts/ARCTIC1/R_Arc1A_Rebel_Dabing.scr";
        private const string GuidePath = "Scripts/ARCTIC1/R_Arc1A_rebel.scr";
        private const string RegistryPath = "Missions/ARCTIC1/scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, ScriptPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "La protection d'exploration Arctic 1 semble deja active.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La protection d'exploration Arctic 1 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Exploration Arctic 1 verifiee : aucun avertissement ni echec en suivant Albert.";
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
                "Suppression des avertissements de limite dans Arctic 1...");
            DormantSource source = ResolveSource(
                gamePath, ScriptPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Les avertissements de limite Arctic 1 sont deja neutralises.");
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
                "Arctic 1 : avertissements et echec de poursuite d'Albert neutralises.");
            InstallerCore.Report(progress,
                "Arctic 1 peut etre exploree sans avertissement ni echec en suivant Albert.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = DisableBackDetector(text, 30);
            text = DisableBackDetector(text, 31);
            return ansi.GetBytes(text);
        }

        private static string DisableBackDetector(string text, int signal)
        {
            string start = @"OnSignal\s*\(\s*" + signal
                + @"\s*\)\s*\{[\s\S]{0,180}?SetWhenever\s*"
                + @"\(\s*Back\s*,\s*";
            Regex disabled = new Regex(
                @"(" + start + @")false(\s*\)\s*;)",
                RegexOptions.IgnoreCase);
            if (disabled.Matches(text).Count == 1) return text;

            Regex enabled = new Regex(
                @"(" + start + @")true(\s*\)\s*;)",
                RegexOptions.IgnoreCase);
            if (enabled.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Activation de la limite Arctic 1 absente ou ambigue : signal "
                    + signal + ".");
            return enabled.Replace(text, "${1}false${2}", 1);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            foreach (int signal in new[] { 30, 31 })
            {
                Require(text,
                    @"OnSignal\s*\(\s*" + signal + @"\s*\)\s*\{"
                    + @"[\s\S]{0,180}?SetWhenever\s*"
                    + @"\(\s*Back\s*,\s*false\s*\)\s*;",
                    "Desactivation de la limite Arctic 1 incomplete : signal "
                        + signal + ".");
                Reject(text,
                    @"OnSignal\s*\(\s*" + signal + @"\s*\)\s*\{"
                    + @"[\s\S]{0,180}?SetWhenever\s*"
                    + @"\(\s*Back\s*,\s*true\s*\)\s*;",
                    "Une limite Arctic 1 reste active : signal " + signal + ".");
            }

            Require(text,
                @"Whenever[ \t]+Back\s*\(\s*_PlayerInRange\s*\(\s*6\s*\)"
                + @"[\s\S]{0,1500}01990269[\s\S]{0,900}01990270"
                + @"[\s\S]{0,900}01990271[\s\S]{0,1200}01990272"
                + @"[\s\S]{0,500}SendSignal\s*\(\s*OBJ\s*,\s*14\s*\)",
                "Branche de limite historique Arctic 1 incomplete.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "dummy_rebel_dabing",
                "R_Arc1A_Rebel_Dabing.scr"))
                throw new InvalidDataException(
                    "Liaison des avertissements Arctic 1 absente.");

            string guide = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath, GuidePath, ScriptArchives)));
            Require(guide,
                @"Label[ \t]+Back\s*:[\s\S]{0,900}"
                + @"SendSignal\s*\(\s*Dabing\s*,\s*30\s*\)",
                "Retour par la route Arctic 1 absent.");
            Require(guide,
                @"Label[ \t]+back_swamp\s*:[\s\S]{0,500}"
                + @"SendSignal\s*\(\s*Dabing\s*,\s*31\s*\)",
                "Retour par le marais Arctic 1 absent.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Arctic 1 trop court.");
            int offset = 6;
            while (offset < data.Length)
            {
                string actor = ReadRegistryField(data, ref offset);
                string script = ReadRegistryField(data, ref offset);
                if (String.Equals(actor, wantedActor,
                        StringComparison.OrdinalIgnoreCase)
                    && String.Equals(script, wantedScript,
                        StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException(
                    "Registre de scripts Arctic 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Arctic 1.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static void Reject(
            string text, string pattern, string message)
        {
            if (Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static DormantSource ResolveSource(
            string gamePath, string relative, string[] archiveNames)
        {
            InstallerCore.ValidateGamePath(gamePath);
            DormantSource result = null;
            foreach (string archiveName in archiveNames)
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

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}