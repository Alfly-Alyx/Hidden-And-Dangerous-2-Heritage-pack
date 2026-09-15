using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class NorwayEnigmaLightmapInstaller
    {
        private const string ScriptPath = "Scripts/NORWAY/R_Nor_OBJ_3.scr";
        private const string RegistryPath = "Missions/NORWAY/Scripts.dta";
        private const string TreePath = "Missions/NORWAY/tree.klz";

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
                    "Le troisieme eclairage de l'Enigma semble deja restaure.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration de l'eclairage Norway n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Norway verifie : les trois elements de l'Enigma retrouvent leur changement d'eclairage officiel.";
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
                "Restauration du troisieme eclairage de l'Enigma dans Norway...");
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
                    "Le troisieme eclairage de l'Enigma est deja actif.");
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
                "Norway : troisieme eclairage de l'Enigma restaure sur Mesh46.");
            InstallerCore.Report(progress,
                "Les trois elements de l'Enigma changent de nouveau d'eclairage.");
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
                @"(?m)^(?<indent>[ \t]*)//[ \t]*FRM_SetLightMap\s*"
                + @"\(\s*LMP3\s*,\s*1\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Eclairage dormant LMP3 de Norway introuvable.");
            text = dormant.Replace(text, match =>
                match.Groups["indent"].Value + "FRM_SetLightMap(LMP3, 1);", 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"FRM_SetLightMap\s*\(\s*LMP1\s*,\s*1\s*\)\s*;[\s\S]{0,100}"
                + @"FRM_SetLightMap\s*\(\s*LMP2\s*,\s*1\s*\)\s*;[\s\S]{0,100}"
                + @"(?m)^[ \t]*FRM_SetLightMap\s*\(\s*LMP3\s*,\s*1\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Require(text,
                @"FRM_FindFrame\s*\(\s*LMP1\s*,\s*""k_tstul6\.Box04""\s*\)\s*;",
                "Premier element visuel de l'Enigma absent.");
            Require(text,
                @"FRM_FindFrame\s*\(\s*LMP2\s*,\s*""m_docum_a66\.doc""\s*\)\s*;",
                "Deuxieme element visuel de l'Enigma absent.");
            Require(text,
                @"FRM_FindFrame\s*\(\s*LMP3\s*,\s*""Mesh46""\s*\)\s*;",
                "Troisieme element visuel de l'Enigma absent.");
            if (!IsPatched(text))
                throw new InvalidDataException(
                    "La sequence des trois changements d'eclairage de l'Enigma est incomplete.");
            Require(text,
                @"SendSignal\s*\(\s*OBJ\s*,\s*7\s*\)\s*;[\s\S]{0,80}"
                + @"PlayMusic\s*\(\s*36\s*\)\s*;",
                "La validation officielle de l'objectif Enigma a ete alteree.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "r_nor_obj3", "R_Nor_OBJ_3.scr"))
                throw new InvalidDataException(
                    "Liaison officielle r_nor_obj3 absente.");

            byte[] tree = ReadSource(ResolveSource(
                gamePath, TreePath, MissionArchives));
            if (!TreeHasObject(tree, "Mesh46"))
                throw new InvalidDataException(
                    "Objet de scene Mesh46 absent de Norway.");
        }

        private static bool TreeHasObject(byte[] data, string wanted)
        {
            if (data == null || data.Length < 24
                || BitConverter.ToUInt32(data, 0) != 0x43666947)
                throw new InvalidDataException("Scene Norway tree.klz invalide.");
            uint count = BitConverter.ToUInt32(data, 12);
            if (count > (data.Length - 24) / 4)
                throw new InvalidDataException("Index d'objets Norway invalide.");
            for (uint index = 0; index < count; index++)
            {
                long raw = BitConverter.ToUInt32(data, checked(24 + (int)index * 4));
                long start = raw + 4;
                if (start < 0 || start >= data.Length)
                    throw new InvalidDataException("Objet Norway hors fichier.");
                int end = checked((int)start);
                while (end < data.Length && data[end] != 0) end++;
                if (end >= data.Length)
                    throw new InvalidDataException("Nom d'objet Norway non termine.");
                string name = Encoding.ASCII.GetString(
                    data, checked((int)start), end - checked((int)start));
                if (String.Equals(name, wanted, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException("Registre de scripts Norway trop court.");
            int offset = 6;
            while (offset < data.Length)
            {
                string actor = ReadRegistryField(data, ref offset);
                string script = ReadRegistryField(data, ref offset);
                if (String.Equals(actor, wantedActor, StringComparison.OrdinalIgnoreCase)
                    && String.Equals(script, wantedScript, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException("Registre de scripts Norway tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException("Champ invalide dans le registre Norway.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
        }

        private static void Require(string text, string pattern, string message)
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