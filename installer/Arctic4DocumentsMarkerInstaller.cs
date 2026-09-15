using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Arctic4DocumentsMarkerInstaller
    {
        private const string ScriptPath =
            "Scripts/ARCTIC4/R_Arc3_Documents.scr";
        private const string RegistryPath =
            "Missions/ARCTIC4/Scripts.dta";
        private const string ScenePath =
            "Missions/ARCTIC4/scene2.bin";

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
                    "Le marqueur des documents d'Arctic 4 semble deja actif.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du marqueur Arctic 4 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Arctic 4 verifie : le marqueur historique des documents "
                + "reapparait a proximite puis disparait apres leur collecte.";
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
                "Restauration du marqueur des documents d'Arctic 4...");
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
                    "Le marqueur des documents d'Arctic 4 est deja actif.");
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
                "Arctic 4 : marqueur de proximite des documents reactive.");
            InstallerCore.Report(progress,
                "Le repere historique des documents d'Arctic 4 est restaure.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = ActivateLine(text, true, 1);
            text = ActivateLine(text, false, 2);
            return ansi.GetBytes(text);
        }

        private static string ActivateLine(
            string text, bool enabled, int finalActiveCount)
        {
            string value = enabled ? "True" : "False";
            string expression = @"FRM_SetOn\s*\(\s*MyFRM\s*,\s*"
                + value + @"\s*\)\s*;";
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
            if (activeCount != finalActiveCount - 1 || dormantCount != 1)
                throw new InvalidDataException(
                    "Commande du marqueur Arctic 4 absente ou ambigue : "
                    + value + ".");
            return dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            }, 1);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireCount(text,
                @"(?m)^[ \t]*FRM_SetOn\s*\(\s*MyFRM\s*,\s*True\s*\)\s*;[ \t]*\r?$",
                1, "L'apparition du marqueur Arctic 4 est incomplete.");
            RequireCount(text,
                @"(?m)^[ \t]*FRM_SetOn\s*\(\s*MyFRM\s*,\s*False\s*\)\s*;[ \t]*\r?$",
                2, "Le masquage du marqueur Arctic 4 est incomplet.");
            RequireCount(text,
                @"(?m)^[ \t]*//[ \t]*FRM_SetOn\s*\(\s*MyFRM\s*,",
                0, "Une commande du marqueur Arctic 4 reste desactivee.");
            RequireCount(text,
                @"Whenever\s+Near\s*\([^\)]*_PlayerInRange\s*"
                + @"\(\s*10\s*\)[\s\S]{0,180}?"
                + @"FRM_SetOn\s*\(\s*MyFRM\s*,\s*True\s*\)",
                1, "Le declencheur de proximite des documents est altere.");
            RequireCount(text,
                @"Whenever\s+X\s*\([^\)]*_IsInInventory\s*"
                + @"\(\s*254\s*\)[\s\S]{0,320}?"
                + @"FRM_SetOn\s*\(\s*MyFRM\s*,\s*False\s*\)",
                1, "Le masquage apres collecte des documents est altere.");
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
            if (!HasBinding(registry,
                    "k_vykricnik_", "R_Arc3_Documents.scr"))
                throw new InvalidDataException(
                    "Le marqueur des documents Arctic 4 n'est plus relie.");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            if (CountAscii(scene, "k_vykricnik_") != 1)
                throw new InvalidDataException(
                    "Le cadre k_vykricnik_ est absent ou ambigu dans Arctic 4.");

            string objective = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/ARCTIC4/R_arc3_objectives.scr",
                    ScriptArchives)));
            RequireCount(objective,
                @"OnSignal\s*\(\s*24\s*\)[\s\S]{0,180}?"
                + @"SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)",
                1, "Le recepteur de collecte des documents Arctic 4 est altere.");

            string assigner = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/ARCTIC4/R_Arc3_KRVEPROLITI.scr",
                    ScriptArchives)));
            RequireCount(assigner,
                @"ScriptAssign\s*\(\s*OBJ\s*,\s*"
                + @"""R_Arc3_Objectives""\s*\)",
                1, "Le controleur d'objectifs Arctic 4 n'est plus assigne.");
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

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Arctic 4 trop court.");
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
                    "Registre de scripts Arctic 4 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Arctic 4.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Arctic 4.");
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
