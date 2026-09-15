using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Arctic4DogPatrolInstaller
    {
        private const string ScriptPath =
            "Scripts/ARCTIC4/R_Arc3_walking_guard_3.scr";
        private const string DogScriptPath =
            "Scripts/ARCTIC4/R_Arc3_dog_1.scr";
        private const string RegistryPath = "Missions/ARCTIC4/Scripts.dta";

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
                    "La marche de la patrouille au chien Arctic 4 semble deja restauree.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration de la patrouille Arctic 4 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Arctic 4 verifie : la patrouille 3 retrouve le mode marche "
                + "retire pour le test avec son chien.";
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
                "Restauration du mode marche de la patrouille au chien dans Arctic 4...");
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
                    "La patrouille au chien Arctic 4 marche deja comme prevu.");
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
                "Arctic 4 : mode marche restaure pour Walking_Guard_3.");
            InstallerCore.Report(progress,
                "La patrouille 3 d'Arctic 4 marche de nouveau avec son chien.");
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
                @"(?m)^(?<indent>[ \t]*)//[ \t]*HUMAN_SETMODE_Walk\s*"
                + @"\(\s*\)\s*;[^\r\n]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Ligne de marche dormante de Walking_Guard_3 introuvable.");
            text = dormant.Replace(text, match =>
                match.Groups["indent"].Value + "HUMAN_SETMODE_Walk();", 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"^[ \t]*Label\s+DeAlarm\s*:[ \t]*(?=\r?$)"
                + @"[\s\S]{0,100}^[ \t]*HUMAN_SETMODE_Guard\s*"
                + @"\(\s*\)\s*;[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_SETMODE_Walk\s*\(\s*\)\s*;"
                + @"[\s\S]{0,100}^[ \t]*Label\s+loop\s*:",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Require(text,
                @"^[ \t]*Label\s+DeAlarm\s*:[ \t]*(?=\r?$)"
                + @"[\s\S]{0,100}^[ \t]*HUMAN_SETMODE_Guard\s*"
                + @"\(\s*\)\s*;[\s\S]{0,100}"
                + @"^[ \t]*HUMAN_SETMODE_Walk\s*\(\s*\)\s*;"
                + @"[\s\S]{0,100}^[ \t]*Label\s+loop\s*:",
                "La reprise en marche de Walking_Guard_3 est incomplete.");
            Require(text,
                @"OnAlarmDone\s*\(\s*\)\s*\{[\s\S]{0,260}"
                + @"HUMAN_SETMODE_Walk\s*\(\s*\)\s*;[\s\S]{0,260}"
                + @"goto\s+DeAlarm\s*;",
                "La reprise officielle apres alarme a ete alteree.");
            Require(text,
                @"OnDeath\s*\(\s*\)\s*\{[\s\S]{0,100}"
                + @"SendSignal\s*\(\s*pes_1\s*,\s*1\s*\)\s*;",
                "La liaison de mort vers le chien a ete alteree.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry,
                    "Walking_Guard_3", "R_Arc3_walking_guard_3.scr")
                || !HasBinding(registry, "pes_1", "R_Arc3_dog_1.scr"))
                throw new InvalidDataException(
                    "Liaisons officielles de la patrouille au chien Arctic 4 incompletes.");

            string dog = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath, DogScriptPath, ScriptArchives)));
            Require(dog,
                @"FRM_FindFrame\s*\(\s*owner\s*,\s*""Walking_Guard_3""\s*\)",
                "Le proprietaire officiel du chien Arctic 4 est absent.");
            Require(dog,
                @"DOG_SetOwner\s*\(\s*owner\s*\)",
                "La commande officielle de proprietaire du chien est absente.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
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
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Arctic 4.");
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
