using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Arctic2DynamicLightInstaller
    {
        private const string ScriptPath = "Scripts/ARCTIC2/R_Arc1B_Vypinac.scr";
        private const string RegistryPath = "Missions/ARCTIC2/scripts.dta";
        private const string ScenePath = "Missions/ARCTIC2/scene2.bin";

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
                    "La lumiere dynamique de l'interrupteur d'Arctic 2 semble deja active.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration de la lumiere d'Arctic 2 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Arctic 2 verifie : l'interrupteur pilote de nouveau sa lumiere "
                + "dynamique en plus des modeles et de la lightmap.";
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
                "Restauration de la lumiere dynamique de l'interrupteur d'Arctic 2...");
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
                    "La lumiere dynamique d'Arctic 2 est deja active.");
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
                "Arctic 2 : lumiere dynamique 1sut-vratnice restauree.");
            InstallerCore.Report(progress,
                "L'interrupteur d'Arctic 2 pilote de nouveau toute la lumiere prevue.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (HasCompleteActiveSequence(text))
            {
                ValidatePatched(data);
                return data;
            }

            Regex declaration = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*frame[ \t]+svetlo;[ \t]*"
                + @"FRM_FindFrame\s*\(\s*svetlo\s*,\s*""1sut-vratnice""\s*\);[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Regex toggle = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<call>FRM_SetOn\s*"
                + @"\(\s*svetlo\s*,\s*(?:True|False)\s*\);)"
                + @"(?<tail>[ \t]*(?://[^\r\n]*)?)[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            if (declaration.Matches(text).Count != 1
                || toggle.Matches(text).Count != 5)
                throw new InvalidDataException(
                    "Sequence lumineuse commentee d'Arctic 2 introuvable ou ambigue.");

            text = declaration.Replace(text,
                "${indent}frame svetlo;\t\tFRM_FindFrame(svetlo, \"1sut-vratnice\");");
            text = toggle.Replace(text, "${indent}${call}${tail}");
            return ansi.GetBytes(text);
        }

        private static bool HasCompleteActiveSequence(string text)
        {
            return Regex.Matches(text,
                    @"(?m)^[ \t]*frame[ \t]+svetlo;[ \t]*FRM_FindFrame\s*"
                    + @"\(\s*svetlo\s*,\s*""1sut-vratnice""\s*\);[ \t]*\r?$",
                    RegexOptions.IgnoreCase).Count == 1
                && Regex.Matches(text,
                    @"(?m)^[ \t]*FRM_SetOn\s*\(\s*svetlo\s*,\s*True\s*\);"
                    + @"[ \t]*(?://[^\r\n]*)?\r?$",
                    RegexOptions.IgnoreCase).Count == 2
                && Regex.Matches(text,
                    @"(?m)^[ \t]*FRM_SetOn\s*\(\s*svetlo\s*,\s*False\s*\);"
                    + @"[ \t]*(?://[^\r\n]*)?\r?$",
                    RegexOptions.IgnoreCase).Count == 3;
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!HasCompleteActiveSequence(text))
                throw new InvalidDataException(
                    "La lumiere dynamique restauree d'Arctic 2 est incomplete.");
            RequireCount(text,
                @"(?m)^[ \t]*FRM_SetOn\s*\(\s*lustrON\s*,", 5,
                "Le modele allume de l'interrupteur d'Arctic 2 a ete altere.");
            RequireCount(text,
                @"(?m)^[ \t]*FRM_SetOn\s*\(\s*lustrOFF\s*,", 5,
                "Le modele eteint de l'interrupteur d'Arctic 2 a ete altere.");
            RequireCount(text,
                @"(?m)^[ \t]*FRM_SetGroupLightMap\s*\(\s*""Blikni_si""\s*,", 4,
                "La lightmap de l'interrupteur d'Arctic 2 a ete alteree.");
            RequireCount(text,
                @"SaveGameValue\s*\(\s*21\s*,", 5,
                "L'etat sauvegarde de l'interrupteur d'Arctic 2 a ete altere.");
        }

        private static void RequireCount(
            string text, string pattern, int wanted, string message)
        {
            if (Regex.Matches(text, pattern,
                    RegexOptions.IgnoreCase).Count != wanted)
                throw new InvalidDataException(message);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "g_zasuv47", "R_Arc1B_Vypinac.scr"))
                throw new InvalidDataException(
                    "La liaison officielle de l'interrupteur d'Arctic 2 est absente.");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            if (CountTypedString(scene, "1sut-vratnice") != 1)
                throw new InvalidDataException(
                    "La lumiere 1sut-vratnice est absente ou ambigue dans Arctic 2.");
        }

        private static int CountTypedString(byte[] data, string wanted)
        {
            int count = 0;
            int offset = 0;
            while (offset + 6 <= data.Length)
            {
                if (data[offset] == 0x10 && data[offset + 1] == 0x00)
                {
                    uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
                    if (rawTotal >= 7 && rawTotal <= 4096)
                    {
                        int total = (int)rawTotal;
                        if (offset + total <= data.Length
                            && data[offset + total - 1] == 0)
                        {
                            string value = Encoding.GetEncoding(1252).GetString(
                                data, offset + 6, total - 7);
                            if (String.Equals(value, wanted,
                                    StringComparison.OrdinalIgnoreCase))
                                count++;
                        }
                    }
                }
                offset++;
            }
            return count;
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Arctic 2 trop court.");
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
                    "Registre de scripts Arctic 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Arctic 2.");
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
