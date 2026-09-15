using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Czech4AlternateApproachInstaller
    {
        private const string DetectorPath = "Scripts/CZECH4/CZ4_Detector_04.scr";
        private const string ReferencePath = "Scripts/CZECH4/CZ4_Detector_03.scr";
        private const string RegistryPath = "Missions/CZECH4/Scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, DetectorPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "L'approche alternative de Czech 4 semble deja corrigee dans les archives.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La correction de l'approche Czech 4 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Czech 4 verifie : les soldats Plazzars 02 et 03 peuvent "
                + "rejoindre la seconde approche avec leur comportement officiel.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, DetectorPath);
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
                "Restauration de la seconde approche dans Czech 4...");
            DormantSource source = ResolveSource(
                gamePath, DetectorPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, DetectorPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Seconde approche de Czech 4 deja active pour les trois soldats.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, DetectorPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    DetectorPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Czech 4 : Plazzars 02 et 03 relies a la seconde approche.");
            InstallerCore.Report(progress,
                "Les trois soldats de Czech 4 reagissent de nouveau a la seconde approche.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = new Regex(
                @"(?m)^\s*SendSignal\s*\(\s*CZ4_Plazzars_0[23]\s*,\s*3\s*\)\s*;\s*$",
                RegexOptions.IgnoreCase);
            Regex wrong = new Regex(
                @"(?m)^(\s*SendSignal\s*\(\s*CZ4_Plazzars_0[23]\s*,\s*)4(\s*\)\s*;\s*)$",
                RegexOptions.IgnoreCase);
            if (active.Matches(text).Count == 2
                && wrong.Matches(text).Count == 0)
                return data;
            if (active.Matches(text).Count != 0
                || wrong.Matches(text).Count != 2)
                throw new InvalidDataException(
                    "Structure inattendue du detecteur 4 dans Czech 4.");
            return ansi.GetBytes(wrong.Replace(text, "${1}3${2}"));
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            foreach (string actor in new[] {
                "CZ4_Plazzars_02", "CZ4_Plazzars_03"
            })
            {
                if (!Regex.IsMatch(text,
                    @"SendSignal\s*\(\s*" + Regex.Escape(actor)
                    + @"\s*,\s*3\s*\)", RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Signal de seconde approche absent pour " + actor + ".");
                if (Regex.IsMatch(text,
                    @"SendSignal\s*\(\s*" + Regex.Escape(actor)
                    + @"\s*,\s*4\s*\)", RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Ancien signal incompatible encore present pour " + actor + ".");
            }
            if (!Regex.IsMatch(text,
                @"SendSignal\s*\(\s*CZ4_Plazzars_01\s*,\s*4\s*\)",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le comportement distinct de Plazzars 01 a ete altere.");
        }

        private static void ValidateAssets(string gamePath)
        {
            string reference = ReadText(ResolveSource(
                gamePath, ReferencePath, ScriptArchives));
            foreach (string actor in new[] {
                "CZ4_Plazzars_02", "CZ4_Plazzars_03"
            })
                if (!Regex.IsMatch(reference,
                    @"SendSignal\s*\(\s*" + Regex.Escape(actor)
                    + @"\s*,\s*3\s*\)", RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Comportement de reference absent pour " + actor + ".");

            foreach (string actor in new[] {
                "CZ4_Plazzars_02", "CZ4_Plazzars_03"
            })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/CZECH4/" + actor + ".scr", ScriptArchives));
                if (!Regex.IsMatch(script,
                    @"OnSignal\s*\(\s*3\s*\)", RegexOptions.IgnoreCase)
                    || Regex.IsMatch(script,
                        @"OnSignal\s*\(\s*4\s*\)", RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Contrat de signal inattendu pour " + actor + ".");
            }

            string first = ReadText(ResolveSource(gamePath,
                "Scripts/CZECH4/CZ4_Plazzars_01.scr", ScriptArchives));
            if (!Regex.IsMatch(first,
                @"OnSignal\s*\(\s*4\s*\)", RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le comportement distinct de Plazzars 01 est absent.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "Detector_04", "CZ4_Detector_04.scr")
                || !HasBinding(registry, "CZ4_Plazzars_01", "CZ4_Plazzars_01.scr")
                || !HasBinding(registry, "CZ4_Plazzars_02", "CZ4_Plazzars_02.scr")
                || !HasBinding(registry, "CZ4_Plazzars_03", "CZ4_Plazzars_03.scr"))
                throw new InvalidDataException(
                    "Liaisons officielles de l'approche Czech 4 incompletes.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Czech 4 trop court.");
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
                    "Registre de scripts Czech 4 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Czech 4.");
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

        private static string ReadText(DormantSource source)
        {
            return Encoding.GetEncoding(1252).GetString(ReadSource(source));
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