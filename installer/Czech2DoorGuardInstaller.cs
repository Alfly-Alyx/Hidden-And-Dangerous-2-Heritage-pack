using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Czech2DoorGuardInstaller
    {
        private const string SwitchPath = "Scripts/CZECH2/LMswitchdoors.scr";
        private const string RegistryPath = "Missions/CZECH2/Scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, SwitchPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "Le second garde de la porte Czech 2 semble deja reactive.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La correction de la porte Czech 2 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Czech 2 verifie : la porte previent de nouveau les soldats 24 et 25.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, SwitchPath);
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
                "Restauration du second garde de la porte dans Czech 2...");
            DormantSource source = ResolveSource(
                gamePath, SwitchPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, SwitchPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Les deux gardes de la porte Czech 2 sont deja relies.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, SwitchPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    SwitchPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Czech 2 : l'ordre de porte est transmis aux soldats 24 et 25.");
            InstallerCore.Report(progress,
                "Le second garde de Czech 2 reagit de nouveau a l'ouverture de la porte.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex ger24 = SignalRegex("ger24");
            Regex ger25 = SignalRegex("ger25");
            int count24 = ger24.Matches(text).Count;
            int count25 = ger25.Matches(text).Count;
            if (count24 == 1 && count25 == 1)
                return data;
            if (count24 != 2 || count25 != 0)
                throw new InvalidDataException(
                    "Structure inattendue des ordres de porte dans Czech 2.");

            int seen = 0;
            string patched = ger24.Replace(text, delegate(Match match) {
                seen++;
                if (seen != 2) return match.Value;
                return match.Groups[1].Value + "ger25" + match.Groups[2].Value;
            });
            return ansi.GetBytes(patched);
        }

        private static Regex SignalRegex(string variable)
        {
            return new Regex(
                @"(?m)^(\s*SendSignal\s*\(\s*)" + Regex.Escape(variable)
                + @"(\s*,\s*3\s*\)\s*;\s*)$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (SignalRegex("ger24").Matches(text).Count != 1
                || SignalRegex("ger25").Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Les deux gardes Czech 2 ne recoivent pas chacun l'ordre 3.");
            Require(text, @"FRM_FindFrame\s*\(\s*ger24\s*,\s*""ger_24""\s*\)",
                "Declaration du soldat 24 absente du script de porte Czech 2.");
            Require(text, @"FRM_FindFrame\s*\(\s*ger25\s*,\s*""ger_25""\s*\)",
                "Declaration du soldat 25 absente du script de porte Czech 2.");
        }

        private static void ValidateAssets(string gamePath)
        {
            string ger24 = ReadText(ResolveSource(gamePath,
                "Scripts/CZECH2/R_Cz2_Ger24.scr", ScriptArchives));
            string ger25 = ReadText(ResolveSource(gamePath,
                "Scripts/CZECH2/R_Cz2_Ger25.scr", ScriptArchives));
            Require(ger24,
                @"_SignalReceived\s*\(\s*3\s*\)[\s\S]{0,350}HUMAN_Move\s*\(\s*""ger24_01""\s*\)",
                "Reaction officielle du soldat 24 absente.");
            Require(ger25,
                @"_SignalReceived\s*\(\s*3\s*\)[\s\S]{0,350}HUMAN_Move\s*\(\s*""Ger25_01""\s*\)",
                "Reaction officielle du soldat 25 absente.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "dobytcak146", "LMswitchdoors.scr")
                || !HasBinding(registry, "Ger_24", "R_Cz2_Ger24.scr")
                || !HasBinding(registry, "Ger_25", "R_Cz2_Ger25.scr"))
                throw new InvalidDataException(
                    "Liaisons officielles de la porte Czech 2 incompletes.");
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Czech 2 trop court.");
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
                    "Registre de scripts Czech 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Czech 2.");
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