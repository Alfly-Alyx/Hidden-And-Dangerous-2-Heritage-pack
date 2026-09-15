using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa5GateSmokeInstaller
    {
        private const string ScriptPath = "Scripts/AFRICA5/AF4_03.scr";
        private const string RegistryPath = "Missions/AFRICA5/Scripts.dta";
        private const string CheckpointsPath = "Missions/AFRICA5/check2.bin";

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
                    "Le garde fumeur d'Africa 5 semble deja reactive.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du garde fumeur d'Africa 5 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 5 verifie : le garde d'entree reprend sa cigarette "
                + "apres avoir autorise le passage.";
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
                "Restauration de la cigarette du garde d'entree d'Africa 5...");
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
                    "Le garde fumeur d'Africa 5 est deja reactive.");
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
                "Africa 5 : cigarette du garde AF4_03 reactivee apres le passage.");
            InstallerCore.Report(progress,
                "Le garde d'entree d'Africa 5 reprend de nouveau sa cigarette.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex dormant = new Regex(
                @"(?m)^(\s*)//\s*(HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)\s*;)\s*\r?\n"
                + @"\1//\s*(Delay\s*\(\s*1000\s*\)\s*;)\s*$",
                RegexOptions.IgnoreCase);
            Regex active = new Regex(
                @"(?m)^\s*HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)\s*;\s*\r?\n"
                + @"\s*Delay\s*\(\s*1000\s*\)\s*;\s*$",
                RegexOptions.IgnoreCase);

            int dormantCount = dormant.Matches(text).Count;
            int activeCount = active.Matches(text).Count;
            if (dormantCount == 0 && activeCount == 1)
            {
                ValidatePatched(data);
                return data;
            }
            if (dormantCount != 1 || activeCount != 0)
                throw new InvalidDataException(
                    "Structure inattendue de la cigarette d'AF4_03.scr.");
            string eol = text.IndexOf("\r\n", StringComparison.Ordinal) >= 0
                ? "\r\n" : "\n";
            text = dormant.Replace(text,
                "${1}${2}" + eol + "${1}${3}", 1);
            return ansi.GetBytes(text);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireCount(text,
                @"(?m)^\s*HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)\s*;\s*$",
                1, "Le demarrage de cigarette d'AF4_03 n'est pas unique.");
            RequireCount(text,
                @"(?m)^\s*HUMAN_Activity_Smoke\s*\(\s*false\s*\)\s*;\s*$",
                1, "L'arret de cigarette d'AF4_03 a ete altere.");
            Require(text,
                @"OnSignal\s*\(\s*1\s*\)\s*\{[\s\S]{0,800}"
                + @"HUMAN_SetAnim\s*\([^\r\n]*couvani[\s\S]{0,300}"
                + @"HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)[\s\S]{0,100}"
                + @"Delay\s*\(\s*1000\s*\)[\s\S]{0,100}"
                + @"HUMAN_Move\s*\([^\r\n]*AF4_03_04",
                "La sequence de reprise de cigarette d'AF4_03 est incomplete.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF4_03", "AF4_03.scr"))
                throw new InvalidDataException(
                    "La liaison officielle AF4_03 -> AF4_03.scr est absente.");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            if (CountAscii(checkpoints, "AF4_03_04") != 1)
                throw new InvalidDataException(
                    "Le point officiel AF4_03_04 est absent ou ambigu.");

            foreach (string neighbor in new[] {
                "AF4_09.scr", "AF4_24.scr", "AF4_25.scr", "AF4_26.scr",
                "AF4_27.scr", "AF4_28.scr", "AF4_29.scr", "AF4_30.scr"
            })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA5/" + neighbor, ScriptArchives));
                Require(script,
                    @"HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)",
                    "Activite de cigarette de reference absente dans " + neighbor + ".");
                Require(script,
                    @"HUMAN_Activity_Smoke\s*\(\s*false\s*\)",
                    "Arret de cigarette de reference absent dans " + neighbor + ".");
            }
        }

        private static int CountAscii(byte[] data, string value)
        {
            byte[] needle = Encoding.ASCII.GetBytes(value);
            int count = 0;
            for (int start = 0; start <= data.Length - needle.Length; start++)
            {
                int index = 0;
                while (index < needle.Length
                    && ToLowerAscii(data[start + index]) == ToLowerAscii(needle[index]))
                    index++;
                if (index == needle.Length) count++;
            }
            return count;
        }

        private static byte ToLowerAscii(byte value)
        {
            return value >= (byte)'A' && value <= (byte)'Z'
                ? (byte)(value + 32) : value;
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

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 5 trop court.");
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
                    "Registre de scripts Africa 5 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 5.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
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