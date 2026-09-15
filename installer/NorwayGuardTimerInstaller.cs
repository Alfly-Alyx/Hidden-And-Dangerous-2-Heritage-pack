using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class NorwayGuardTimerInstaller
    {
        private const string ScriptPath = "Scripts/Norway/R_nor_man3.scr";
        private const string TimerPath = "Scripts/Norway/small3_timer.scr";
        private const string RegistryPath = "Missions/Norway/Scripts.dta";

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
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La correction du minuteur du garde Norway n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Norway verifiee : le garde 3 peut de nouveau interrompre "
                + "son minuteur de fausse alerte lorsqu'il est blesse.";
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
                "Restauration de l'arret du minuteur du garde 3 de Norway...");
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
                    "Arret du minuteur du garde 3 deja actif.");
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
                "Norway : arret du minuteur de fausse alerte du garde 3 restaure.");
            InstallerCore.Report(progress,
                "Le garde 3 n'est plus rappele a sa ronde par un ancien minuteur apres une blessure.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatched(text)) return data;

            Regex dormant = new Regex(
                @"(?m)^[ \t]*//[ \t]*SendSignal\s*\(\s*timer\s*,\s*3\s*\)\s*;[^\r\n]*",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Ordre dormant du minuteur du garde 3 introuvable.");
            return ansi.GetBytes(dormant.Replace(
                text, "    SendSignal(timer2,3);   // stop casowace", 1));
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"(?m)^[ \t]*SendSignal\s*\(\s*timer2\s*,\s*3\s*\)\s*;",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Require(text,
                @"FRM_FindFrame\s*\(\s*timer2\s*,\s*""small3_timer""\s*\)",
                "Le controleur small3_timer n'est plus reference.");
            Require(text,
                @"If\s*\(\s*AIEvent\s*==\s*64\s*\)[\s\S]{0,180}"
                + @"SendSignal\s*\(\s*timer2\s*,\s*3\s*\)",
                "L'arret du minuteur n'est pas dans la branche de blessure.");
            if (!IsPatched(text))
                throw new InvalidDataException(
                    "L'arret du minuteur du garde 3 reste inactif.");
        }

        private static void ValidateAssets(string gamePath)
        {
            string timer = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, TimerPath, ScriptArchives)));
            Require(timer,
                @"OnSignal\s*\(\s*3\s*\)\s*\{\s*\}",
                "Le recepteur d'arret de small3_timer est absent.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "Small3", "R_nor_man3.scr")
                || !HasBinding(registry, "small3_timer", "small3_timer.scr"))
                throw new InvalidDataException(
                    "Les liaisons commerciales du garde 3 et de son minuteur sont absentes.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Norway trop court.");
            int offset = 6;
            while (offset < data.Length)
            {
                string actor = ReadRegistryField(data, ref offset);
                string script = ReadRegistryField(data, ref offset);
                if (String.Equals(
                    actor, wantedActor, StringComparison.OrdinalIgnoreCase)
                    && String.Equals(
                    script, wantedScript, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException(
                    "Registre de scripts Norway tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Norway.");
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
