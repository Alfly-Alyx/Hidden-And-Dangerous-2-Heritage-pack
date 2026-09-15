using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Arctic1TransformerLightsInstaller
    {
        private const string ScriptPath =
            "Scripts/Arctic1_obj/Arctic1a_mp_transformator.scr";
        private const string ReferencePath =
            "Scripts/Arctic1_obj/Arctic1a_lmg_switcher.scr";
        private const string ObjectiveRegistry =
            "Missions/Arctic1_obj/mpscripts.dta";
        private const string CommonRegistry =
            "Missions/Arctic1_obj/scripts.dta";
        private const string ScenePath =
            "Missions/Arctic1_obj/scene2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] RestoredFrames = {
            "m_svets_.Rectangle01",
            "m_svets_2.Rectangle01"
        };

        private static readonly string[] RemovedFrames = {
            "st_2",
            "light",
            "s_p16",
            "m_svets2.Rectangle01",
            "m_svets4.Rectangle01"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, ScriptPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "Les halos du transformateur Arctic 1 semblent deja actifs.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration des halos Arctic 1 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Arctic 1 objectif verifie : les deux halos encore pilotes "
                + "par le clignotement officiel sont aussi eteints avec le transformateur.";
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
                "Restauration des halos du transformateur dans Arctic 1 objectif...");
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
                    "Les halos du transformateur Arctic 1 sont deja restaures.");
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
                "Arctic 1 objectif : deux halos du transformateur restaures.");
            InstallerCore.Report(progress,
                "Les deux halos officiels s'eteignent maintenant avec le transformateur.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            foreach (string frame in RestoredFrames)
                text = ActivateDormant(text, FramePattern(frame), frame);
            return ansi.GetBytes(text);
        }

        private static string ActivateDormant(
            string text, string statementPattern, string description)
        {
            Regex active = StatementRegex(statementPattern, false);
            Regex dormant = StatementRegex(statementPattern, true);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == 1 && dormantCount == 0) return text;
            if (activeCount != 0 || dormantCount != 1)
                throw new InvalidDataException(
                    "Etat absent ou ambigu du halo Arctic 1 : " + description + ".");
            return dormant.Replace(text, "$1$2$3", 1);
        }

        private static string FramePattern(string frame)
        {
            return @"FRM_FindFrame\s*\(\s*actual\s*,\s*"""
                + Regex.Escape(frame)
                + @"""\s*\)\s*;\s*FRM_SetOn\s*\(\s*actual\s*,\s*lmg_state\s*\)\s*;";
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
            foreach (string frame in RestoredFrames)
                RequireCounts(text, FramePattern(frame), 1, 0,
                    "Halo Arctic 1 non restaure : " + frame + ".");
            foreach (string frame in RemovedFrames)
                RequireCounts(text, FramePattern(frame), 0, 1,
                    "Une reference de scene absente a ete activee : " + frame + ".");
            Require(text,
                @"OnDeath\s*\(\s*\)[\s\S]{0,220}goto\s+SWITCH_LIGHT_MAPS"
                + @"[\s\S]{0,5200}FRM_FindFrame\s*\(\s*actual\s*,\s*"""
                + Regex.Escape(RestoredFrames[0]) + @""""
                + @"[\s\S]{0,220}FRM_FindFrame\s*\(\s*actual\s*,\s*"""
                + Regex.Escape(RestoredFrames[1]) + @"""",
                "Les halos restaures ne sont plus dans la sequence de destruction.");
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
            byte[] objectiveRegistry = ReadSource(ResolveSource(
                gamePath, ObjectiveRegistry, MissionArchives));
            byte[] commonRegistry = ReadSource(ResolveSource(
                gamePath, CommonRegistry, MissionArchives));
            if (!HasBinding(objectiveRegistry, "la_A1_trans_",
                    "Arctic1a_mp_transformator.scr")
                || !HasBinding(commonRegistry, "la_A1_trans_",
                    "Arctic1a_lmg_switcher.scr"))
                throw new InvalidDataException(
                    "Double liaison officielle du transformateur Arctic 1 absente.");

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(
                    gamePath, ReferencePath, ScriptArchives)));
            foreach (string frame in RestoredFrames)
                RequireCounts(reference, FramePattern(frame), 1, 0,
                    "Le clignotement officiel ne pilote plus le halo " + frame + ".");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            if (CountAscii(scene, "m_svets_.Rectangle01") < 1
                || CountAscii(scene, "m_svets_2") < 1)
                throw new InvalidDataException(
                    "Objets de halo Arctic 1 absents de la scene.");
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
                    "Registre de scripts Arctic 1 objectif trop court.");
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
                    "Registre Arctic 1 objectif tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Arctic 1 objectif.");
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
