using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Alps2AlarmVoiceInstaller
    {
        private const string ScriptPath = "Scripts/ALPS2/al2_36.scr";
        private const string RegistryPath = "Missions/ALPS2/Scripts.dta";
        private const string ReferencePath = "Scripts/ALPS1/ge_14.scr";

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
                    "La reaction vocale d'Alpes 2 semble deja restauree.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration vocale d'Alpes 2 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Alpes 2 verifie : le garde 36 retrouve son alerte vocale officielle.";
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
                "Restauration de l'alerte vocale du garde 36 dans Alpes 2...");
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
                    "L'alerte vocale du garde 36 d'Alpes 2 est deja active.");
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
            InstallerCore.Log("Alpes 2 : alerte vocale restauree pour AL2_36.");
            InstallerCore.Report(progress,
                "Le garde 36 d'Alpes 2 donne de nouveau son alerte vocale.");
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

            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*PlaySound\s*"
                + @"\(\s*9\s*,\s*49\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Alerte vocale dormante d'AL2_36 introuvable.");
            text = dormant.Replace(text, match =>
                match.Groups["indent"].Value + "PlaySound(9,49);", 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"OnAlarm\s*\(\s*\)\s*\{[\s\S]{0,220}"
                + @"SendSignal\s*\(\s*alarm\s*,\s*6\s*\)\s*;[\s\S]{0,80}"
                + @"(?m)^[ \t]*PlaySound\s*\(\s*9\s*,\s*49\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Require(text,
                @"OnAlarm\s*\(\s*\)\s*\{[\s\S]{0,220}"
                + @"DisableWhenevers\s*\(\s*1\s*\)\s*;[\s\S]{0,80}"
                + @"SendSignal\s*\(\s*alarm\s*,\s*6\s*\)\s*;[\s\S]{0,80}"
                + @"(?m)^[ \t]*PlaySound\s*\(\s*9\s*,\s*49\s*\)\s*;[ \t]*(?=\r?$)",
                "La reaction d'alarme restauree d'AL2_36 est incomplete.");
            Require(text,
                @"OnDeath\s*\(\s*\)\s*\{[\s\S]{0,240}"
                + @"Mission_SetUniformDisguise\s*\(\s*0\s*\)\s*;[\s\S]{0,80}"
                + @"SendSignal\s*\(\s*alarm\s*,\s*6\s*\)\s*;",
                "La reaction de mort officielle d'AL2_36 a ete alteree.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AL2_36", "al2_36.scr"))
                throw new InvalidDataException(
                    "Liaison officielle AL2_36 vers al2_36.scr absente.");

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(
                    gamePath, ReferencePath, ScriptArchives)));
            Require(reference,
                @"OnAlarm\s*\(\s*\)\s*\{[\s\S]{0,520}"
                + @"PlaySound\s*\(\s*9\s*,\s*49\s*\)\s*;",
                "Le precedent officiel actif du son 9/49 dans Alpes 1 est absent.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Alpes 2 trop court.");
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
                    "Registre de scripts Alpes 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Alpes 2.");
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