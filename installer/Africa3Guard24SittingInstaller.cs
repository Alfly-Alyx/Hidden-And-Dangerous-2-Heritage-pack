using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa3Guard24SittingInstaller
    {
        private const string ScriptPath = "Scripts/AFRICA3/AF3a_24.scr";
        private const string RegistryPath = "Missions/AFRICA3/scripts.dta";
        private const string ActorsPath = "Missions/AFRICA3/actors.bin";
        private const string CheckpointsPath = "Missions/AFRICA3/check2.bin";
        private const string ScenePath = "Missions/AFRICA3/scene2.bin";

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
                    "Le repos assis du garde 24 semble deja actif.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du garde 24 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 3 verifie : le garde 24 s'assoit de nouveau "
                + "a son poste et y retourne apres l'alarme.";
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
                "Restauration du repos assis du garde 24 d'Africa 3...");
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
                    "Le repos assis du garde 24 d'Africa 3 est deja actif.");
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
                "Africa 3 : repos assis et retour du garde 24 reactives.");
            InstallerCore.Report(progress,
                "Le garde 24 d'Africa 3 retrouve son activite assise.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = ActivateLine(text,
                @"HUMAN_Move\s*\(\s*""AF3a_24_sit""\s*\)\s*;",
                1, "retour au siege");
            text = ActivateLine(text,
                @"HUMAN_ACTIVITY_Sit\s*\(\s*sit\s*\)\s*;",
                2, "activites assises");
            return ansi.GetBytes(text);
        }

        private static string ActivateLine(
            string text, string expression, int finalActiveCount,
            string description)
        {
            Regex active = new Regex(
                @"(?m)^[ \t]*" + expression + @"[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>"
                + expression + @")[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == finalActiveCount && dormantCount == 0)
                return text;
            int expectedDormant = finalActiveCount - activeCount;
            if (activeCount < 0 || expectedDormant <= 0
                || dormantCount != expectedDormant)
                throw new InvalidDataException(
                    "Commande du garde 24 absente ou ambigue : "
                    + description + ".");
            return dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            });
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireCount(text,
                @"(?m)^[ \t]*HUMAN_Move\s*\(\s*""AF3a_24_sit""\s*\)\s*;[ \t]*\r?$",
                1, "Le retour au siege du garde 24 est incomplet.");
            RequireCount(text,
                @"(?m)^[ \t]*HUMAN_ACTIVITY_Sit\s*\(\s*sit\s*\)\s*;[ \t]*\r?$",
                2, "Les activites assises du garde 24 sont incompletes.");
            RequireCount(text,
                @"(?m)^[ \t]*//[ \t]*(?:HUMAN_Move\s*"
                + @"\(\s*""AF3a_24_sit""|HUMAN_ACTIVITY_Sit\s*\(\s*sit)",
                0, "Une commande assise du garde 24 reste desactivee.");
            RequireCount(text,
                @"OnAlarmDone\s*\([^\)]*\)\s*\{[\s\S]{0,500}?"
                + @"HUMAN_Move\s*\(\s*""AF3a_24_sit""\s*\)"
                + @"[\s\S]{0,100}?HUMAN_ACTIVITY_Sit\s*\(\s*sit\s*\)",
                1, "Le retour assis apres alarme du garde 24 est altere.");
        }

        private static void RequireCount(
            string text, string pattern, int expected, string message)
        {
            if (Regex.Matches(text, pattern,
                    RegexOptions.IgnoreCase).Count != expected)
                throw new InvalidDataException(message);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF3a_24", "AF3a_24.scr"))
                throw new InvalidDataException(
                    "Le garde 24 d'Africa 3 n'est plus relie.");

            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            if (CountTypedString(actors, "AF3a_24") != 1)
                throw new InvalidDataException(
                    "L'acteur AF3a_24 est absent ou ambigu.");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            foreach (string checkpoint in new[] {
                "AF3a_24_01", "AF3a_24_sit", "AF3a_24_alert"
            })
                if (CountAscii(checkpoints, checkpoint) != 1)
                    throw new InvalidDataException(
                        "Point du garde 24 absent ou ambigu : "
                        + checkpoint + ".");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            if (CountAscii(scene, "dummy_24_sit") != 1)
                throw new InvalidDataException(
                    "Le siege dummy_24_sit est absent ou ambigu.");

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/AFRICA3/AF3a_19.scr", ScriptArchives)));
            RequireCount(reference,
                @"HUMAN_ACTIVITY_Sit\s*\(\s*chair\s*\)", 2,
                "L'activite assise de reference Africa 3 est alteree.");
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

        private static int CountTypedString(byte[] data, string wanted)
        {
            int count = 0;
            for (int offset = 0; offset + 6 <= data.Length; offset++)
            {
                if (data[offset] != 0x10 || data[offset + 1] != 0x00)
                    continue;
                uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
                if (rawTotal < 7 || rawTotal > 4096) continue;
                int total = (int)rawTotal;
                if (offset + total > data.Length
                    || data[offset + total - 1] != 0)
                    continue;
                string value = Encoding.GetEncoding(1252).GetString(
                    data, offset + 6, total - 7);
                if (String.Equals(value, wanted,
                        StringComparison.OrdinalIgnoreCase))
                    count++;
            }
            return count;
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 3 trop court.");
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
                    "Registre de scripts Africa 3 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 3.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Africa 3.");
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
