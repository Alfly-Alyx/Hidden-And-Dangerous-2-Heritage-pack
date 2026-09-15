using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa3AlarmPatrolInstaller
    {
        private const string ScriptPath =
            "Scripts/AFRICA3/AF3a_dummy_alarm.scr";
        private const string RegistryPath =
            "Missions/AFRICA3/scripts.dta";
        private const string ActorsPath =
            "Missions/AFRICA3/actors.bin";

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
                    "Les gardes 22 et 23 d'Africa 3 semblent deja alertes.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration d'alarme Africa 3 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 3 verifie : le distributeur d'alarme avertit "
                + "de nouveau les gardes 22 et 23.";
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
                "Restauration de l'alerte des gardes 22 et 23 dans Africa 3...");
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
                    "Les gardes 22 et 23 d'Africa 3 sont deja relies a l'alarme.");
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
                "Africa 3 : gardes 22 et 23 reconnectes a l'alarme globale.");
            InstallerCore.Report(progress,
                "Les deux gardes de la mosquee reagissent de nouveau a l'alarme globale.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = ActivateLine(text,
                @"FRAME\s+en22\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*en22\s*,\s*""AF3a_22""\s*\)\s*;",
                "declaration en22");
            text = ActivateLine(text,
                @"FRAME\s+en23\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*en23\s*,\s*""AF3a_23""\s*\)\s*;",
                "declaration en23");
            text = ActivateLine(text,
                @"SendSignal\s*\(\s*en22\s*,\s*20\s*\)\s*;",
                "signal en22");
            text = ActivateLine(text,
                @"SendSignal\s*\(\s*en23\s*,\s*20\s*\)\s*;",
                "signal en23");
            return ansi.GetBytes(text);
        }

        private static string ActivateLine(
            string text, string expression, string description)
        {
            Regex active = new Regex(
                @"(?m)^[ \t]*" + expression
                + @"[ \t]*(?://[^\r\n]*)?\r?$",
                RegexOptions.IgnoreCase);
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>"
                + expression + @")(?<tail>[ \t]*(?://[^\r\n]*)?)\r?$",
                RegexOptions.IgnoreCase);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == 1 && dormantCount == 0) return text;
            if (activeCount != 0 || dormantCount != 1)
                throw new InvalidDataException(
                    "Ligne Africa 3 absente ou ambigue : " + description + ".");
            return dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value
                    + match.Groups["tail"].Value;
            }, 1);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireOne(text,
                @"(?m)^[ \t]*FRAME\s+en22\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*en22\s*,\s*""AF3a_22""\s*\)\s*;",
                "Declaration restauree d'en22 incomplete.");
            RequireOne(text,
                @"(?m)^[ \t]*FRAME\s+en23\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*en23\s*,\s*""AF3a_23""\s*\)\s*;",
                "Declaration restauree d'en23 incomplete.");
            RequireOne(text,
                @"(?m)^[ \t]*SendSignal\s*\(\s*en22\s*,\s*20\s*\)\s*;",
                "Signal restaure vers en22 incomplet.");
            RequireOne(text,
                @"(?m)^[ \t]*SendSignal\s*\(\s*en23\s*,\s*20\s*\)\s*;",
                "Signal restaure vers en23 incomplet.");
            if (Regex.Matches(text,
                    @"(?m)^[ \t]*SendSignal\s*\([^\r\n]+,\s*20\s*\)\s*;",
                    RegexOptions.IgnoreCase).Count != 14)
                throw new InvalidDataException(
                    "La liste globale des gardes Africa 3 a ete alteree.");
            RequireOne(text,
                @"Whenever\s+globalalarm\s*\(\s*_SignalReceived\s*"
                + @"\(\s*1\s*\)\s*\)",
                "Declencheur d'alarme Africa 3 altere.");
        }

        private static void RequireOne(
            string text, string pattern, string message)
        {
            if (Regex.Matches(text, pattern,
                    RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(message);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry,
                    "dummy_alarm", "AF3a_dummy_alarm.scr"))
                throw new InvalidDataException(
                    "Le distributeur d'alarme Africa 3 n'est plus relie.");

            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            foreach (string actor in new[] { "AF3a_22", "AF3a_23" })
            {
                if (!HasBinding(registry, actor, actor + ".scr"))
                    throw new InvalidDataException(
                        "Liaison Africa 3 absente pour " + actor + ".");
                if (CountTypedString(actors, actor) != 1)
                    throw new InvalidDataException(
                        "Acteur Africa 3 absent ou ambigu : " + actor + ".");
                string behavior = Encoding.GetEncoding(1252).GetString(
                    ReadSource(ResolveSource(gamePath,
                        "Scripts/AFRICA3/" + actor + ".scr",
                        ScriptArchives)));
                if (Regex.Matches(behavior,
                        @"OnSignal\s*\(\s*20\s*\)",
                        RegexOptions.IgnoreCase).Count != 1)
                    throw new InvalidDataException(
                        "Reaction au signal 20 absente pour " + actor + ".");
            }
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
