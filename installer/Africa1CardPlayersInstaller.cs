using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa1CardPlayersInstaller
    {
        private static readonly string[] ScriptPaths = {
            "Scripts/AFRICA1/AF1_24.scr",
            "Scripts/AFRICA1/AF1_25.scr"
        };

        private const string RegistryPath = "Missions/AFRICA1/scripts.dta";
        private const string ActorsPath = "Missions/AFRICA1/actors.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (string relative in ScriptPaths)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(original, relative);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "La partie de cartes semble deja active : " + relative);
                ValidatePatched(patched, relative);
                if (!BytesEqual(patched, PatchScript(patched, relative)))
                    throw new InvalidDataException(
                        "La restauration des cartes n'est pas idempotente : "
                        + relative);
            }
            ValidateAssets(gamePath);
            return "Africa 1 verifie : les soldats 24 et 25 jouent de nouveau "
                + "aux cartes dans le hangar.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string relative in ScriptPaths)
                {
                    string target = InstallerCore.SafeGameTarget(gamePath, relative);
                    if (!File.Exists(target)) return false;
                    ValidatePatched(File.ReadAllBytes(target), relative);
                }
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
                "Restauration de la partie de cartes du hangar d'Africa 1...");
            ValidateAssets(gamePath);
            foreach (string relative in ScriptPaths)
            {
                DormantSource source = ResolveSource(
                    gamePath, relative, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(original, relative);
                ValidatePatched(patched, relative);
                if (BytesEqual(original, patched)) continue;

                InstallerCore.PrepareTarget(
                    gamePath, relative, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, patched);
                    File.Copy(temporary, target, true);
                    journal.RecordHash(
                        relative, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
            }
            InstallerCore.Log(
                "Africa 1 : boucle de cartes des soldats 24 et 25 reactivee.");
            InstallerCore.Report(progress,
                "Les deux soldats du hangar d'Africa 1 jouent de nouveau aux cartes.");
        }

        private static byte[] PatchScript(byte[] data, string relative)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (ActiveSequenceRegex().Matches(text).Count == 1)
            {
                ValidatePatched(data, relative);
                return data;
            }

            Regex dormant = new Regex(
                @"(?ms)^(?<indent>[ \t]*)//[ \t]*"
                + @"HUMAN_ACTIVITY_Card\s*\(\s*1\s*\)\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*Label[ \t]+LOOP[ \t]*:[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*HUMAN_ACTIVITY_Card\s*"
                + @"\(\s*2\s*\)\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*Delay\s*\(\s*1500\s*\)\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*goto[ \t]+LOOP\s*;[ \t]*\r?\n"
                + @"\k<indent>//[ \t]*goto[ \t]+END\s*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Match match = dormant.Match(text);
            if (!match.Success || dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Boucle de cartes commentee absente ou ambigue : " + relative);

            string uncommented = Regex.Replace(match.Value,
                @"(?m)^(?<indent>[ \t]*)//[ \t]?", "${indent}");
            text = text.Substring(0, match.Index) + uncommented
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(text);
        }

        private static Regex ActiveSequenceRegex()
        {
            return new Regex(
                @"^[ \t]*HUMAN_ACTIVITY_Card\s*\(\s*1\s*\)\s*;"
                + @"[\s\S]{0,80}?^[ \t]*Label[ \t]+LOOP[ \t]*:"
                + @"[\s\S]{0,100}?^[ \t]*HUMAN_ACTIVITY_Card\s*"
                + @"\(\s*2\s*\)\s*;[\s\S]{0,80}?"
                + @"^[ \t]*Delay\s*\(\s*1500\s*\)\s*;[\s\S]{0,80}?"
                + @"^[ \t]*goto[ \t]+LOOP\s*;[\s\S]{0,80}?"
                + @"^[ \t]*goto[ \t]+END\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data, string relative)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveSequenceRegex().Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Boucle de cartes incomplete : " + relative);
            RequireCount(text,
                @"(?m)^[ \t]*//[ \t]*(?:HUMAN_ACTIVITY_Card\s*\(\s*[12]\s*\)\s*;|"
                + @"Label[ \t]+LOOP[ \t]*:|Delay\s*\(\s*1500\s*\)\s*;|"
                + @"goto[ \t]+(?:LOOP|END)\s*;)",
                0, "Une commande de cartes reste desactivee : " + relative);
            RequireCount(text,
                @"OnAlarm\s*\([^\)]*\)\s*\{[\s\S]{0,180}?"
                + @"HUMAN_SetAnim\s*\(\s*""""",
                1, "L'interruption d'alarme du joueur de cartes est alteree.");
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
            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            foreach (string actor in new[] { "AF1_24", "AF1_25" })
            {
                if (!HasBinding(registry, actor, actor + ".scr"))
                    throw new InvalidDataException(
                        "Liaison Africa 1 absente pour " + actor + ".");
                if (CountTypedString(actors, actor) != 1)
                    throw new InvalidDataException(
                        "Acteur Africa 1 absent ou ambigu : " + actor + ".");
            }

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/CZECH3/R_cz3_nosic1.scr", ScriptArchives)));
            RequireCount(reference,
                @"HUMAN_ACTIVITY_Card\s*\(\s*1\s*\)", 1,
                "La commande active Card(1) de reference est absente.");
            RequireCount(reference,
                @"HUMAN_ACTIVITY_Card\s*\(\s*2\s*\)", 1,
                "La commande active Card(2) de reference est absente.");
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
                    "Registre de scripts Africa 1 trop court.");
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
                    "Registre de scripts Africa 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 1.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Africa 1.");
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
