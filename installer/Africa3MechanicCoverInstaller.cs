using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa3MechanicCoverInstaller
    {
        private const string ScriptPath = "Scripts/AFRICA3/AF3a_21.scr";
        private const string RegistryPath = "Missions/AFRICA3/Scripts.dta";
        private const string CheckpointsPath = "Missions/AFRICA3/check2.bin";

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
                    "La mise a couvert du mecanicien Africa 3 semble deja active.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La mise a couvert du mecanicien Africa 3 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 3 verifie : le mecanicien 21 peut de nouveau se "
                + "refugier sous l'Opel lorsqu'il est blesse.";
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
                "Restauration de la mise a couvert du mecanicien Africa 3...");
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
                    "La mise a couvert du mecanicien Africa 3 est deja active.");
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
                "Africa 3 : branche de couverture du mecanicien AF3a_21 reactivee.");
            InstallerCore.Report(progress,
                "Le mecanicien 21 d'Africa 3 peut de nouveau se mettre a couvert.");
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
                @"(?ms)^(?<indent>[ \t]*)//[ \t]*if[ \t]*\([ \t]*Atype[ \t]*==[ \t]*64[ \t]*\)[ \t]*\{[ \t]*\r?\n"
                + @"(?<body>(?:\k<indent>//[^\r\n]*\r?\n)+?)"
                + @"\k<indent>//[ \t]*\}[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Match match = dormant.Match(text);
            if (!match.Success || dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Branche de couverture commentee d'AF3a_21 introuvable.");

            string uncommented = Regex.Replace(match.Value,
                @"(?m)^(?<indent>[ \t]*)//[ \t]?", "${indent}");
            text = text.Substring(0, match.Index) + uncommented
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(text);
        }

        private static Regex ActiveBranchRegex()
        {
            return new Regex(
                @"^[ \t]*if\s*\(\s*Atype\s*==\s*64\s*\)\s*\{[ \t]*(?=\r?$)"
                + @"[\s\S]{0,500}^[ \t]*below_car\s*=\s*1\s*;"
                + @"[\s\S]{0,300}^[ \t]*HUMAN_Move\s*\([^\r\n]*AF3a_21_01"
                + @"[\s\S]{0,300}^[ \t]*HUMAN_SETMODE_Lie\s*\(\s*\)\s*;"
                + @"[\s\S]{0,150}^[ \t]*HUMAN_Move\s*\([^\r\n]*AF3a_21_bcar"
                + @"[\s\S]{0,100}^[ \t]*goto\s+END\s*;"
                + @"[\s\S]{0,50}^[ \t]*\}[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveBranchRegex().Matches(text).Count != 1)
                throw new InvalidDataException(
                    "La branche de couverture d'AF3a_21 est incomplete.");
            Require(text,
                @"SetAlarmType\s*\(\s*323\s*,\s*true\s*\)",
                "L'alarme de blessure du mecanicien Africa 3 n'est plus active.");
            Require(text,
                @"if\s*\(\s*below_car\s*==\s*1\s*\)[\s\S]{0,260}"
                + @"HUMAN_Move\s*\([^\r\n]*AF3a_21_below[\s\S]{0,180}"
                + @"HUMAN_Move\s*\([^\r\n]*AF3a_21_01",
                "La sortie de couverture existante d'AF3a_21 a ete alteree.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF3a_21", "AF3a_21.scr"))
                throw new InvalidDataException(
                    "La liaison officielle AF3a_21 -> AF3a_21.scr est absente.");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            foreach (string checkpoint in new[] {
                "AF3a_21_01", "AF3a_21_02", "AF3a_21_bcar", "AF3a_21_below"
            })
                if (CountAscii(checkpoints, checkpoint) != 1)
                    throw new InvalidDataException(
                        "Point Africa 3 absent ou ambigu : " + checkpoint + ".");
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

        private static void Require(string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
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
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 3.");
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
