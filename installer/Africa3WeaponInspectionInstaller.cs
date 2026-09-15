using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa3WeaponInspectionInstaller
    {
        private const string ScriptPath = "Scripts/AFRICA3/AF3a_08.scr";
        private const string RegistryPath = "Missions/AFRICA3/Scripts.dta";

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
                    "L'inspection d'arme d'Africa 3 semble deja restauree.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration de l'inspection d'arme Africa 3 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 3 verifie : la ronde 08 inspecte de nouveau son arme "
                + "aux deux temps prevus.";
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
                "Restauration des inspections d'arme de la ronde 08 dans Africa 3...");
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
                    "Les inspections d'arme d'Africa 3 sont deja restaurees.");
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
                "Africa 3 : deux inspections d'arme restaurees dans AF3a_08.");
            InstallerCore.Report(progress,
                "La ronde 08 d'Africa 3 inspecte de nouveau son arme.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            int active = ActiveCount(text);
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*HUMAN_ACTIVITY_CheckWeapon\s*\(\s*\)\s*;[^\r\n]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            int dormantCount = dormant.Matches(text).Count;
            if (active == 2 && dormantCount == 0)
            {
                ValidatePatched(data);
                return data;
            }
            if (active != 0 || dormantCount != 2)
                throw new InvalidDataException(
                    "Etat inattendu des inspections d'arme dans AF3a_08.scr.");

            text = dormant.Replace(text,
                match => match.Groups["indent"].Value
                    + "HUMAN_ACTIVITY_CheckWeapon();");
            return ansi.GetBytes(text);
        }

        private static int ActiveCount(string text)
        {
            return Regex.Matches(text,
                @"(?m)^[ \t]*HUMAN_ACTIVITY_CheckWeapon\s*\(\s*\)\s*;",
                RegexOptions.IgnoreCase).Count;
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveCount(text) != 2)
                throw new InvalidDataException(
                    "Les deux inspections d'arme d'AF3a_08 ne sont pas actives.");
            Require(text,
                @"Label\s+PATH_CWEAPON\s*:[\s\S]{0,220}"
                + @"HUMAN_ACTIVITY_Sit\s*\(\s*sit\s*\)\s*;[\s\S]{0,100}"
                + @"Delay\s*\(\s*2000\s*\)\s*;[\s\S]{0,100}"
                + @"HUMAN_ACTIVITY_CheckWeapon\s*\(\s*\)\s*;[\s\S]{0,100}"
                + @"Delay\s*\(\s*3000\s*\)\s*;[\s\S]{0,100}"
                + @"HUMAN_ACTIVITY_CheckWeapon\s*\(\s*\)\s*;[\s\S]{0,100}"
                + @"Delay\s*\(\s*5000\s*\)\s*;[\s\S]{0,100}"
                + @"HUMAN_SETMODE_Stand\s*\(\s*\)\s*;",
                "La sequence d'inspection d'arme d'AF3a_08 est incomplete.");
            if (Regex.IsMatch(text,
                @"(?m)^[ \t]*//[ \t]*HUMAN_ACTIVITY_CheckWeapon\s*\(",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Une inspection d'arme d'AF3a_08 reste desactivee.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF3a_08", "AF3a_08.scr"))
                throw new InvalidDataException(
                    "La liaison officielle AF3a_08 est absente du registre Africa 3.");

            foreach (string reference in new[] {
                "Scripts/AFRICA2/AF2_06.scr",
                "Scripts/AFRICA2/AF2_09.scr",
                "Scripts/AFRICA2/AF2_11.scr"
            })
            {
                string script = Encoding.GetEncoding(1252).GetString(
                    ReadSource(ResolveSource(gamePath, reference, ScriptArchives)));
                Require(script,
                    @"(?m)^[ \t]*HUMAN_ACTIVITY_CheckWeapon\s*\(\s*\)\s*;",
                    "La commande officielle d'inspection d'arme n'est pas confirmee dans "
                    + reference + ".");
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
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