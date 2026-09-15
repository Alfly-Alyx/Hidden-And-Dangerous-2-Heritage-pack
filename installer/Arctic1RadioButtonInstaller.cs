using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Arctic1RadioButtonInstaller
    {
        private const string ScriptPath = "Scripts/ARCTIC1/R_Arc1A_Radio.scr";
        private const string RegistryPath = "Missions/ARCTIC1/scripts.dta";
        private const string ScenePath = "Missions/ARCTIC1/scene2.bin";
        private const string ReferencePath = "Scripts/ARCTIC3/R_Ar3_Radio.scr";

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
                    "Le bouton de la radio Arctic 1 semble deja actif.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration de la radio Arctic 1 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Arctic 1 verifie : le bouton de la radio est restaure a sa destruction.";
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
                "Restauration du bouton de la radio dans Arctic 1...");
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
                    "Le bouton de la radio Arctic 1 est deja restaure.");
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
                "Arctic 1 : visibilite du bouton radio restauree.");
            InstallerCore.Report(progress,
                "Le bouton utilisable de la radio Arctic 1 disparait de nouveau avec elle.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = ActivateDormant(text,
                @"FRM_SetOn\s*\(\s*CUDLIK\s*,\s*true\s*\)\s*;");
            text = ActivateDormant(text,
                @"FRM_SetOn\s*\(\s*CUDLIK\s*,\s*false\s*\)\s*;");
            return ansi.GetBytes(text);
        }

        private static string ActivateDormant(
            string text, string statementPattern)
        {
            Regex active = StatementRegex(statementPattern, false);
            Regex dormant = StatementRegex(statementPattern, true);
            if (active.Matches(text).Count == 1
                && dormant.Matches(text).Count == 0)
                return text;
            if (active.Matches(text).Count != 0
                || dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Etat du bouton radio Arctic 1 absent ou ambigu.");
            return dormant.Replace(text, "$1$2$3", 1);
        }

        private static Regex StatementRegex(
            string statementPattern, bool dormant)
        {
            string prefix = dormant
                ? @"([ \t]*)//[ \t]*(" : @"[ \t]*";
            string suffix = dormant ? @")([ \t]*\r?)" : @"[ \t]*\r?";
            return new Regex(
                @"(?m)^" + prefix + statementPattern + suffix + @"$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireCounts(text,
                @"FRM_SetOn\s*\(\s*CUDLIK\s*,\s*true\s*\)\s*;", 1, 0,
                "Initialisation du bouton radio Arctic 1 incomplete.");
            RequireCounts(text,
                @"FRM_SetOn\s*\(\s*CUDLIK\s*,\s*false\s*\)\s*;", 1, 0,
                "Masquage du bouton radio Arctic 1 incomplet.");
            Require(text,
                @"FRM_SetOn\s*\(\s*Radio_sound_1\s*,\s*true\s*\)"
                + @"[\s\S]{0,160}FRM_SetOn\s*\(\s*CUDLIK\s*,\s*true\s*\)"
                + @"[\s\S]{0,180}OnDeath\s*\(\s*\)"
                + @"[\s\S]{0,260}FRM_SetOn\s*\(\s*CUDLIK\s*,\s*false\s*\)"
                + @"[\s\S]{0,100}SendSignal\s*\(\s*CUDLIK\s*,\s*1\s*\)",
                "Cycle complet du bouton radio Arctic 1 absent.");
            Require(text,
                @"(?m)^[ \t]*//[ \t]*frame[ \t]+objimka\b",
                "Le support absent de la radio Arctic 1 a ete active a tort.");
        }

        private static void RequireCounts(
            string text, string statementPattern,
            int activeCount, int dormantCount, string message)
        {
            if (StatementRegex(statementPattern, false).Matches(text).Count
                    != activeCount
                || StatementRegex(statementPattern, true).Matches(text).Count
                    != dormantCount)
                throw new InvalidDataException(message);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "m_radiog_", "R_Arc1A_Radio.scr")
                || !HasBinding(registry, "m_radiog_.tlac_hide",
                    "R_Arc1A_Radio_cudlik.scr"))
                throw new InvalidDataException(
                    "Liaisons officielles de la radio Arctic 1 absentes.");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            if (CountAscii(scene, "m_radiog_.tlac_hide") != 1)
                throw new InvalidDataException(
                    "Bouton de radio Arctic 1 absent ou ambigu dans la scene.");
            if (CountAscii(scene, "m_radiog_.objimka") != 0)
                throw new InvalidDataException(
                    "Le support radio Arctic 1 n'est plus absent comme attendu.");

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(
                    gamePath, ReferencePath, ScriptArchives)));
            Require(reference,
                @"FRM_SetOn\s*\(\s*CUDLIK\s*,\s*True\s*\)"
                + @"[\s\S]{0,280}OnDeath\s*\(\s*\)"
                + @"[\s\S]{0,260}FRM_SetOn\s*\(\s*CUDLIK\s*,\s*false\s*\)"
                + @"[\s\S]{0,120}SendSignal\s*\(\s*CUDLIK\s*,\s*1\s*\)",
                "Radio commerciale de reference Arctic 3 incomplete.");
        }

        private static int CountAscii(byte[] data, string value)
        {
            byte[] needle = Encoding.ASCII.GetBytes(value);
            int count = 0;
            for (int start = 0; start <= data.Length - needle.Length; start++)
            {
                int index = 0;
                while (index < needle.Length
                    && ToLowerAscii(data[start + index])
                        == ToLowerAscii(needle[index]))
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
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Arctic 1 trop court.");
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
                    "Registre de scripts Arctic 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Arctic 1.");
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