using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Burgundy3SasDialogueInstaller
    {
        private const string ScriptPath = "Scripts/BURGUNDY3/bur3_sas01.scr";
        private const string CoopScriptPath = "Scripts/Co_Burgundy3/bur3_sas01.scr";
        private const string RegistryPath = "Missions/Burgundy3/Scripts.dta";

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
                    "La premiere replique SAS Burgundy 3 semble deja active dans l'archive source.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du dialogue SAS Burgundy 3 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Burgundy 3 verifiee : le premier SAS retrouve la replique "
                + "59990052, conservee active dans la variante cooperative.";
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
                "Restauration de la premiere replique SAS de Burgundy 3...");
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
                    "La premiere replique SAS de Burgundy 3 est deja active.");
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
                "Burgundy 3 : premiere replique SAS 59990052 restauree.");
            InstallerCore.Report(progress,
                "Le dialogue du premier SAS de Burgundy 3 retrouve sa phrase d'ouverture.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatched(text)) return data;

            Regex dormant = new Regex(
                @"(?m)^([ \t]*)//[ \t]*(FRM_MorphSpeechDelayed\s*\(\s*this\s*,\s*59990052\s*,\s*8\s*,\s*20\s*\)\s*;)[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Replique dormante 59990052 de Burgundy 3 introuvable.");
            return ansi.GetBytes(dormant.Replace(text, "${1}${2}", 1));
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"(?m)^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*this\s*,\s*59990052\s*,\s*8\s*,\s*20\s*\)\s*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!Regex.IsMatch(text,
                @"FRM_MorphSpeechDelayed\s*\(\s*this\s*,\s*59990052\s*,\s*8\s*,\s*20\s*\)\s*;"
                + @"[\s\S]{0,120}FRM_MorphSpeechDelayed\s*\(\s*this\s*,\s*59990053\s*,\s*8\s*,\s*20\s*\)\s*;"
                + @"[\s\S]{0,120}FRM_MorphSpeechDelayed\s*\(\s*this\s*,\s*59990054\s*,\s*8\s*,\s*20\s*\)\s*;",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "La replique 59990052 n'est pas replacee au debut du dialogue SAS Burgundy 3.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "BUR03_SAS01", "bur3_sas01.scr"))
                throw new InvalidDataException(
                    "La liaison du premier SAS Burgundy 3 est absente.");

            string coop = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, CoopScriptPath, ScriptArchives)));
            if (!Regex.IsMatch(coop,
                @"FRM_MorphSpeechDelayed\s*\(\s*this\s*,\s*59990052\s*,\s*8\s*,\s*20\s*\)\s*;"
                + @"[\s\S]{0,120}FRM_MorphSpeechDelayed\s*\(\s*this\s*,\s*59990053\s*,",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "La preuve cooperative du dialogue 59990052 est absente.");

            string[] languageArchives = Directory.GetFiles(gamePath, "Lang*.dta");
            bool soundFound = false;
            bool lipsyncFound = false;
            foreach (string archivePath in languageArchives)
            {
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                    {
                        string name = entry.Name.Replace((char)92, '/');
                        if (String.Equals(name, "Sounds/59990052.wav",
                            StringComparison.OrdinalIgnoreCase))
                            soundFound = true;
                        if (String.Equals(name, "Tables/Dabing/59990052.dat",
                            StringComparison.OrdinalIgnoreCase))
                            lipsyncFound = true;
                    }
            }
            if (!soundFound || !lipsyncFound)
                throw new InvalidDataException(
                    "La voix ou le lipsync 59990052 de Burgundy 3 est absent de la langue installee.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Burgundy 3 trop court.");
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
                    "Registre de scripts Burgundy 3 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Burgundy 3.");
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
