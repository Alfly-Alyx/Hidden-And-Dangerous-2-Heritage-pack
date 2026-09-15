using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa5StorageAlarmInstaller
    {
        private const string ScriptPath =
            "Scripts/AFRICA5/AF4_sklad06.scr";
        private const string RegistryPath =
            "Missions/AFRICA5/Scripts.dta";

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
                    "La recherche d'alarme du garde 06 d'Africa 5 semble deja active.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La recherche d'alarme du garde 06 d'Africa 5 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 5 verifie : le garde 06 du magasin peut de nouveau "
                + "rechercher une alarme exterieure.";
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
                "Restauration de la recherche d'alarme du garde 06 d'Africa 5...");
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
                    "La recherche d'alarme du garde 06 d'Africa 5 est deja active.");
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
                "Africa 5 : recherche d'alarme restauree pour AF4_sklad06.");
            InstallerCore.Report(progress,
                "Le garde 06 du magasin d'Africa 5 recherche de nouveau les alarmes.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = ActiveBranchRegex();
            if (active.Matches(text).Count == 1)
            {
                ValidatePatched(data);
                return data;
            }

            Regex dormant = new Regex(
                @"(?ms)^(?<indent>[ \t]*)//[ \t]*if[ \t]*\([ \t]*Atype[ \t]*==[ \t]*256[ \t]*\)[ \t]*\{[ \t]*\r?\n"
                + @"(?<body>(?:\k<indent>//[^\r\n]*\r?\n)+?)"
                + @"\k<indent>//[ \t]*\}[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Match match = dormant.Match(text);
            if (!match.Success || dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Branche d'alarme commentee d'AF4_sklad06 introuvable.");

            string uncommented = Regex.Replace(match.Value,
                @"(?m)^(?<indent>[ \t]*)//[ \t]?", "${indent}");
            text = text.Substring(0, match.Index) + uncommented
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(text);
        }

        private static Regex ActiveBranchRegex()
        {
            return new Regex(
                @"if\s*\(\s*Atype\s*==\s*256\s*\)\s*\{[\s\S]{0,300}"
                + @"HUMAN_SetAlarm\s*\(\s*false\s*\)\s*;[\s\S]{0,180}"
                + @"HUMAN_SetMODE_Run\s*\(\s*\)\s*;[\s\S]{0,180}"
                + @"HUMAN_MoveToAlarm\s*\(\s*\)\s*;[\s\S]{0,100}\}",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveBranchRegex().Matches(text).Count != 1)
                throw new InvalidDataException(
                    "La branche d'alarme d'AF4_sklad06 est incomplete.");
            Require(text,
                @"SetAlarmType\s*\(\s*1023\s*,\s*true\s*\)[\s\S]{0,100}"
                + @"SetAlarmType\s*\(\s*516\s*,\s*false\s*\)",
                "Les types d'alarme officiels d'AF4_sklad06 ont ete alteres.");
            Require(text,
                @"if\s*\(\s*\(\s*Atype\s*==\s*2\s*\)\s*AND\s*"
                + @"\(\s*!at_inner_alert\s*\)\s*\)[\s\S]{0,300}"
                + @"HUMAN_Move\s*\(\s*""AF4_sklad06_al""\s*\)[\s\S]{0,120}"
                + @"at_inner_alert\s*=\s*1\s*;",
                "La reaction d'alarme interieure d'AF4_sklad06 a ete alteree.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF4_sklad06", "AF4_sklad06.scr"))
                throw new InvalidDataException(
                    "La liaison officielle d'AF4_sklad06 est absente.");

            foreach (string neighbor in new[] { "02", "03", "05", "07" })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA5/AF4_sklad" + neighbor + ".scr",
                    ScriptArchives));
                if (ActiveBranchRegex().Matches(script).Count != 1)
                    throw new InvalidDataException(
                        "Reaction de reference absente chez AF4_sklad"
                        + neighbor + ".");
            }
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
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