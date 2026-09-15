using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Libye3DetailedRouteInstaller
    {
        private const string ScriptPath =
            "Scripts/Libye3/Li3_German_3.scr";
        private const string RegistryPath =
            "Missions/Libye3/Scripts.dta";
        private const string CheckpointsPath =
            "Missions/Libye3/check2.bin";

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
                    "Le trajet detaille G3 de Libye 3 semble deja actif.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du trajet G3 de Libye 3 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Libye 3 verifiee : le remplacant du mitrailleur peut "
                + "reprendre les cinq etapes G3_02 a G3_06 de sa route officielle.";
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
                "Restauration du trajet detaille du mitrailleur de Libye 3...");
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
                    "Le trajet detaille G3 de Libye 3 est deja actif.");
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
                "Libye 3 : etapes G3_02 a G3_06 restaurees pour Li3_German_3.");
            InstallerCore.Report(progress,
                "Le remplacant du mitrailleur de Libye 3 emprunte de nouveau sa route complete.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (ActiveRouteRegex().Matches(text).Count == 1)
            {
                ValidatePatched(data);
                return data;
            }

            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*HUMAN_Move\s*\(\s*""G3_02""\s*\)\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*HUMAN_Move\s*\(\s*""G3_03""\s*\)\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*HUMAN_Move\s*\(\s*""G3_04""\s*\)\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*HUMAN_Move\s*\(\s*""G3_05""\s*\)\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*HUMAN_Move\s*\(\s*""G3_06""\s*\)\s*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Match match = dormant.Match(text);
            if (!match.Success || dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Les cinq etapes commentees de la route G3 sont introuvables.");

            string uncommented = Regex.Replace(match.Value,
                @"(?m)^(?<indent>[ \t]*)//[ \t]?", "${indent}");
            text = text.Substring(0, match.Index) + uncommented
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(text);
        }

        private static Regex ActiveRouteRegex()
        {
            return new Regex(
                @"^\s*OnSignal\s*\(\s*1\s*\)[\s\S]{0,300}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""G3_01""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""G3_02""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""G3_03""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""G3_04""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""G3_05""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""G3_06""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""G3_07""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_Move\s*\(\s*""MG_1""\s*\)[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_BoardVehicle\s*\(\s*""w_mg42Lie_1""\s*,\s*1\s*,\s*0\s*\)",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveRouteRegex().Matches(text).Count != 1)
                throw new InvalidDataException(
                    "La route G3 restauree de Libye 3 est incomplete.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry,
                    "Li3_German_3", "Li3_German_3.scr"))
                throw new InvalidDataException(
                    "La liaison officielle de Li3_German_3 est absente.");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            foreach (string checkpoint in new[] {
                "G3_01", "G3_02", "G3_03", "G3_04", "G3_05",
                "G3_06", "G3_07", "MG_1"
            })
                if (CountAscii(checkpoints, checkpoint) != 1)
                    throw new InvalidDataException(
                        "Point Libye 3 absent ou ambigu : " + checkpoint + ".");
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

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Libye 3 trop court.");
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
                    "Registre de scripts Libye 3 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Libye 3.");
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

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}
