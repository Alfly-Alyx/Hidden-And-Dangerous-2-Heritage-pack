using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class NorwayApproachInstaller
    {
        private const string ScriptPath = "Scripts/Norway/detect_player1.scr";
        private const string CounterpartPath = "Scripts/Norway/detect_player2.scr";
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
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "La premiere approche Norway semble deja corrigee dans les archives.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "Le correctif des approches Norway n'est pas idempotent.");
            ValidateAssets(gamePath);
            return "Norway verifie : les deux zones d'approche se desactivent "
                + "de nouveau mutuellement.";
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
                "Restauration de la paire de zones d'approche Norway...");
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
                    "Zones d'approche Norway deja reliees entre elles.");
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
                "Norway : le premier detecteur cible de nouveau detect_player2.");
            InstallerCore.Report(progress,
                "Les deux approches Norway s'excluent de nouveau correctement.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = new Regex(
                @"FRM_FindFrame\s*\(\s*detectplay2\s*,\s*""detect_player2""\s*\)\s*;",
                RegexOptions.IgnoreCase);
            if (active.Matches(text).Count == 1)
                return data;

            Regex wrong = new Regex(
                @"(FRM_FindFrame\s*\(\s*detectplay2\s*,\s*"")detect_player1(""\s*\)\s*;)",
                RegexOptions.IgnoreCase);
            if (wrong.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du premier detecteur Norway.");
            return ansi.GetBytes(wrong.Replace(text, "${1}detect_player2${2}", 1));
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!Regex.IsMatch(text,
                    @"FRM_FindFrame\s*\(\s*detectplay2\s*,\s*""detect_player2""\s*\)",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(text,
                    @"SendSignal\s*\(\s*detectplay2\s*,\s*2\s*\)",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(text,
                    @"OnSignal\s*\(\s*1\s*\)[\s\S]{0,100}SetWhenever\s*\(\s*heleho\s*,\s*false\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "La premiere zone d'approche Norway n'est pas valide.");
        }

        private static void ValidateAssets(string gamePath)
        {
            string counterpart = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, CounterpartPath, ScriptArchives)));
            if (!Regex.IsMatch(counterpart,
                    @"FRM_FindFrame\s*\(\s*detectplay1\s*,\s*""detect_player1""\s*\)",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(counterpart,
                    @"SendSignal\s*\(\s*detectplay1\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(counterpart,
                    @"OnSignal\s*\(\s*2\s*\)[\s\S]{0,100}SetWhenever\s*\(\s*heleho\s*,\s*false\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le second detecteur Norway symetrique est absent.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "detect_player1", "detect_player1.scr")
                || !HasBinding(registry, "detect_player2", "detect_player2.scr"))
                throw new InvalidDataException(
                    "Les liaisons officielles des detecteurs Norway sont absentes.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Norway trop court.");
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
