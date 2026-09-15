using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa3Guard03HeatInstaller
    {
        private const string ScriptPath = "Scripts/AFRICA3/AF3a_03.scr";
        private const string RegistryPath = "Missions/AFRICA3/scripts.dta";
        private const string ActorsPath = "Missions/AFRICA3/actors.bin";

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
                    "Le geste de chaleur du garde 03 semble deja actif.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du garde 03 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 3 verifie : le garde 03 retrouve son geste "
                + "de chaleur pendant sa pause.";
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
                "Restauration du geste de chaleur du garde 03 d'Africa 3...");
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
                    "Le geste de chaleur du garde 03 est deja actif.");
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
                "Africa 3 : geste de chaleur du garde AF3a_03 reactive.");
            InstallerCore.Report(progress,
                "Le garde 03 d'Africa 3 retrouve son geste pendant sa pause.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = HeatLine(false);
            Regex dormant = HeatLine(true);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == 2 && dormantCount == 0) return data;
            if (activeCount != 1 || dormantCount != 1)
                throw new InvalidDataException(
                    "Geste de chaleur commente du garde 03 absent ou ambigu.");
            text = dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            }, 1);
            return ansi.GetBytes(text);
        }

        private static Regex HeatLine(bool dormant)
        {
            string prefix = dormant
                ? @"(?<indent>[ \t]*)//[ \t]*(?<code>"
                : @"[ \t]*";
            string suffix = dormant ? @")" : "";
            return new Regex(
                @"(?m)^" + prefix
                + @"HUMAN_ACTIVITY_Hot\s*\(\s*\)\s*;"
                + suffix + @"[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (HeatLine(false).Matches(text).Count != 2
                || HeatLine(true).Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Les gestes de chaleur du garde 03 sont incomplets.");
            if (Regex.Matches(text,
                    @"HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)"
                    + @"[\s\S]{0,180}?HUMAN_SetAnim\s*"
                    + @"\(\s*""%%sedimL""[\s\S]{0,180}?"
                    + @"HUMAN_ACTIVITY_Hot\s*\(\s*\)",
                    RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(
                    "Le geste restaure n'est plus dans la pause assise.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF3a_03", "AF3a_03.scr"))
                throw new InvalidDataException(
                    "Le garde 03 d'Africa 3 n'est plus relie.");

            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            if (CountTypedString(actors, "AF3a_03") != 1)
                throw new InvalidDataException(
                    "L'acteur AF3a_03 est absent ou ambigu.");

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/AFRICA3/AF3a_16.scr", ScriptArchives)));
            if (Regex.Matches(reference,
                    @"HUMAN_ACTIVITY_Sit\s*\(\s*sit\s*\)"
                    + @"[\s\S]{0,100}?HUMAN_ACTIVITY_Hot\s*\(\s*\)"
                    + @"[\s\S]{0,120}?HUMAN_ACTIVITY_Smoke\s*"
                    + @"\(\s*true\s*\)",
                    RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(
                    "La combinaison assise/chaleur/fumee de reference est absente.");
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
