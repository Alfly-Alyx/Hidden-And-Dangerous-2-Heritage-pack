using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Czech4ObjectiveCounterInstaller
    {
        private const string ScriptPath = "Scripts/CZECH4/CZ4_OD.scr";
        private const string RegistryPath = "Missions/CZECH4/scripts.dta";

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
                    "Le second soldat Chatter semble deja compte dans Czech 4.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La correction du compteur Czech 4 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Czech 4 verifie : le second soldat Chatter peut etre "
                + "retabli dans le compteur de l'objectif principal.";
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
                "Correction du compteur d'ennemis de Czech 4...");
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
                    "Le second soldat Chatter est deja compte dans Czech 4.");
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
                "Czech 4 : Chatter_02 retabli dans le compteur d'ennemis.");
            InstallerCore.Report(progress,
                "Le second soldat Chatter participe de nouveau a l'objectif principal.");
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

            Regex wrongTarget = new Regex(
                @"FRM_FindFrame\s*\(\s*CZ4_Chatter_02\s*,\s*"
                + @"""CZ4_Chatter_01""\s*\)\s*;",
                RegexOptions.IgnoreCase);
            if (wrongTarget.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Cible dupliquee Chatter_01 introuvable dans Czech 4.");
            text = wrongTarget.Replace(text,
                "FRM_FindFrame(CZ4_Chatter_02, \"CZ4_Chatter_02\");", 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"Frame\s+CZ4_Chatter_01\s*;[ \t]*FRM_FindFrame\s*"
                + @"\(\s*CZ4_Chatter_01\s*,\s*""CZ4_Chatter_01""\s*\)\s*;"
                + @"[\s\S]{0,240}Frame\s+CZ4_Chatter_02\s*;[ \t]*FRM_FindFrame\s*"
                + @"\(\s*CZ4_Chatter_02\s*,\s*""CZ4_Chatter_02""\s*\)\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsPatched(text))
                throw new InvalidDataException(
                    "Declarations Chatter de Czech 4 incompletes.");
            RequireCount(text,
                @"FRM_FindFrame\s*\(\s*CZ4_Chatter_01\s*,\s*"
                + @"""CZ4_Chatter_01""\s*\)", 1,
                "Nombre inattendu de cibles Chatter_01 dans le compteur Czech 4.");
            RequireCount(text,
                @"FRM_FindFrame\s*\(\s*CZ4_Chatter_02\s*,\s*"
                + @"""CZ4_Chatter_02""\s*\)", 1,
                "Nombre inattendu de cibles Chatter_02 dans le compteur Czech 4.");
            RequireCount(text,
                @"_ACTOR_GetState\s*\(\s*CZ4_Chatter_01\s*\)", 1,
                "Chatter_01 n'est pas compte exactement une fois dans Czech 4.");
            RequireCount(text,
                @"_ACTOR_GetState\s*\(\s*CZ4_Chatter_02\s*\)", 1,
                "Chatter_02 n'est pas compte exactement une fois dans Czech 4.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "CZ4_OD", "CZ4_OD.scr")
                || !HasBinding(registry,
                    "CZ4_Chatter_01", "CZ4_Chatter_01.scr")
                || !HasBinding(registry,
                    "CZ4_Chatter_02", "CZ4_Chatter_02.scr"))
                throw new InvalidDataException(
                    "Liaisons commerciales du compteur Chatter Czech 4 absentes.");
        }

        private static void RequireCount(
            string text, string pattern, int count, string message)
        {
            if (Regex.Matches(text, pattern,
                    RegexOptions.IgnoreCase | RegexOptions.Multiline).Count != count)
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
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

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}
