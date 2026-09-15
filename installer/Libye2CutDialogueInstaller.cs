using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Libye2CutDialogueInstaller
    {
        private const string SoloScriptPath =
            "Scripts/Libye2/AF2_16_17_speech.scr";
        private const string CoopScriptPath =
            "Scripts/Co_Libye2/AF2_16_17_speech.scr";
        private const string SoloRegistryPath =
            "Missions/Libye2/Scripts.dta";
        private const string CoopRegistryPath =
            "Missions/Co_Libye2/mpscripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            ValidateSource(gamePath, SoloScriptPath);
            ValidateSource(gamePath, CoopScriptPath);
            ValidateAssets(gamePath);
            return "Libye 2 verifiee : les repliques 53990012 et 53990013 "
                + "peuvent completer la conversation des deux soldats, en solo et en cooperation.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                return IsTargetActive(gamePath, SoloScriptPath)
                    && IsTargetActive(gamePath, CoopScriptPath);
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
                "Restauration du dialogue coupe de Libye 2...");
            ValidateAssets(gamePath);
            InstallScript(gamePath, SoloScriptPath, journal, prepared);
            InstallScript(gamePath, CoopScriptPath, journal, prepared);
            InstallerCore.Log(
                "Libye 2 : repliques 53990012 et 53990013 restaurees en solo et en cooperation.");
            InstallerCore.Report(progress,
                "La conversation des deux soldats de Libye 2 retrouve ses deux dernieres repliques.");
        }

        private static void ValidateSource(string gamePath, string relative)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, relative, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "Le dialogue coupe de Libye 2 semble deja actif dans l'archive source.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du dialogue Libye 2 n'est pas idempotente.");
        }

        private static bool IsTargetActive(string gamePath, string relative)
        {
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            if (!File.Exists(target)) return false;
            ValidatePatched(File.ReadAllBytes(target));
            return true;
        }

        private static void InstallScript(
            string gamePath, string relative, StateJournal journal,
            HashSet<string> prepared)
        {
            DormantSource source = ResolveSource(
                gamePath, relative, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            if (BytesEqual(original, patched)) return;

            InstallerCore.PrepareTarget(
                gamePath, relative, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatched(text)) return data;

            Regex dormant12 = DormantLine(53990012, "af2_17");
            Regex dormant13 = DormantLine(53990013, "af2_16");
            if (dormant12.Matches(text).Count != 1
                || dormant13.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Les deux repliques dormantes de Libye 2 sont introuvables.");
            text = dormant12.Replace(text, "${1}${2}", 1);
            text = dormant13.Replace(text, "${1}${2}", 1);
            return ansi.GetBytes(text);
        }

        private static Regex DormantLine(int voice, string actor)
        {
            return new Regex(
                @"(?m)^([ \t]*)//[ \t]*(FRM_MorphSpeechDelayed\s*\(\s*"
                + Regex.Escape(actor) + @"\s*,\s*" + voice
                + @"\s*,\s*2\s*,\s*41\s*\)\s*;)[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"(?m)^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*af2_17\s*,\s*53990012\s*,\s*2\s*,\s*41\s*\)\s*;[ \t]*\r?$",
                RegexOptions.IgnoreCase)
                && Regex.IsMatch(text,
                @"(?m)^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*af2_16\s*,\s*53990013\s*,\s*2\s*,\s*41\s*\)\s*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!Regex.IsMatch(text,
                @"^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*af2_16\s*,\s*53990009\s*,[\s\S]{0,160}"
                + @"^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*af2_17\s*,\s*53990010\s*,[\s\S]{0,160}"
                + @"^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*af2_16\s*,\s*53990011\s*,[\s\S]{0,160}"
                + @"^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*af2_17\s*,\s*53990012\s*,[\s\S]{0,160}"
                + @"^[ \t]*FRM_MorphSpeechDelayed\s*\(\s*af2_16\s*,\s*53990013\s*,",
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(
                    "Les repliques 53990012 et 53990013 ne completent pas la sequence attendue de Libye 2.");
        }

        private static void ValidateAssets(string gamePath)
        {
            ValidateRegistry(gamePath, SoloRegistryPath);
            ValidateRegistry(gamePath, CoopRegistryPath);

            string[] languageArchives = Directory.GetFiles(gamePath, "Lang*.dta");
            HashSet<string> found = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            foreach (string archivePath in languageArchives)
            {
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                    {
                        string name = entry.Name.Replace((char)92, '/');
                        if (String.Equals(name, "Sounds/53990012.wav",
                                StringComparison.OrdinalIgnoreCase)
                            || String.Equals(name, "Sounds/53990013.wav",
                                StringComparison.OrdinalIgnoreCase)
                            || String.Equals(name, "Tables/Dabing/53990012.dat",
                                StringComparison.OrdinalIgnoreCase)
                            || String.Equals(name, "Tables/Dabing/53990013.dat",
                                StringComparison.OrdinalIgnoreCase))
                            found.Add(name);
                    }
            }
            string[] required = {
                "Sounds/53990012.wav", "Sounds/53990013.wav",
                "Tables/Dabing/53990012.dat", "Tables/Dabing/53990013.dat"
            };
            foreach (string name in required)
                if (!found.Contains(name))
                    throw new InvalidDataException(
                        "Ressource de dialogue Libye 2 absente : " + name);
        }

        private static void ValidateRegistry(string gamePath, string relative)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, relative, MissionArchives));
            if (!HasBinding(registry,
                    "AF2_16_17_speech", "AF2_16_17_speech.scr")
                || !HasBinding(registry, "AF2_16", "AF2_16.scr")
                || !HasBinding(registry, "AF2_17", "AF2_17.scr"))
                throw new InvalidDataException(
                    "Les liaisons d'acteurs du dialogue Libye 2 sont incompletes : "
                    + relative);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Libye 2 trop court.");
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
                    "Registre de scripts Libye 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Libye 2.");
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
