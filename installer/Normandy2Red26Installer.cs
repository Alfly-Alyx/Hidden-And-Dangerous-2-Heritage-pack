using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Normandy2Red26Installer
    {
        private const string ScriptPath = "Scripts/NORMANDY2/R_N2_Red_26.scr";
        private const string DetectorPath = "Scripts/NORMANDY2/R_N2_Detector_7.scr";
        private const string RegistryPath = "Missions/NORMANDY2/Scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            DormantSource source = ResolveSource(
                gamePath, ScriptPath, ScriptArchives);
            byte[] original = ReadSource(source);
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "Le groupe Red 26 semble deja corrige dans les archives.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La correction Red 26 de Normandy 2 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Normandy 2 verifie : Red 26 retrouve le signal 7 envoye "
                + "au reste de son groupe.";
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
                "Reactivation du soldat Red 26 dans la vague 7 de Normandy 2...");
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
                    "Soldat Red 26 de Normandy 2 deja rattache a la vague 7.");
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
                "Normandy 2 : Red 26 rattache au signal 7 de son groupe.");
            InstallerCore.Report(progress,
                "Le soldat Red 26 rejoint de nouveau la vague 7 de Normandy 2.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = new Regex(
                @"(?m)^\s*Onsignal\s*\(\s*7\s*\)\s*$",
                RegexOptions.IgnoreCase);
            if (active.Matches(text).Count == 1)
                return data;

            Regex wrong = new Regex(
                @"(?m)^(\s*Onsignal\s*\(\s*)6(\s*\)\s*)$",
                RegexOptions.IgnoreCase);
            if (wrong.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du signal de Red 26 dans Normandy 2.");
            return ansi.GetBytes(wrong.Replace(text, "${1}7${2}", 1));
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!Regex.IsMatch(text,
                @"Onsignal\s*\(\s*7\s*\)\s*\{[\s\S]{0,180}HUMAN_Suspend\s*\(\s*False\s*\)",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le signal 7 de Red 26 n'a pas ete restaure.");
        }

        private static void ValidateAssets(string gamePath)
        {
            string detector = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, DetectorPath, ScriptArchives)));
            if (!Regex.IsMatch(detector,
                @"FRM_FindFrame\s*\(\s*Red_26\s*,\s*""Red_26""\s*\)",
                RegexOptions.IgnoreCase)
                || !Regex.IsMatch(detector,
                    @"SendSignal\s*\(\s*Red_26\s*,\s*7\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le detecteur 7 officiel ne cible pas Red 26 comme attendu.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "Red_26", "R_N2_Red_26.scr")
                || !HasBinding(registry, "detector_7", "R_N2_Detector_7.scr"))
                throw new InvalidDataException(
                    "Les liaisons officielles Red 26/detecteur 7 sont absentes.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Normandy 2 trop court.");
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
                    "Registre de scripts Normandy 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Normandy 2.");
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