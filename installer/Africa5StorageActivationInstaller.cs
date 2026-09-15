using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa5StorageActivationInstaller
    {
        private const string ScriptPath = "Scripts/AFRICA5/AF4_sklad04.scr";
        private const string RegistryPath = "Missions/AFRICA5/Scripts.dta";

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
                    "Le mecanicien 04 d'Africa 5 semble deja reactive.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du mecanicien Africa 5 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 5 verifie : le mecanicien 04 reagit de nouveau "
                + "a l'ouverture du magasin.";
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
                "Restauration du mecanicien 04 du magasin dans Africa 5...");
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
                    "Le mecanicien 04 d'Africa 5 est deja reactive.");
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
                "Africa 5 : gestionnaire 1 restaure pour AF4_sklad04.");
            InstallerCore.Report(progress,
                "Le septieme homme du magasin reagit de nouveau avec son groupe.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex anyHandler = new Regex(
                @"OnSignal\s*\(\s*1\s*\)", RegexOptions.IgnoreCase);
            int handlers = anyHandler.Matches(text).Count;
            if (handlers == 1)
            {
                ValidatePatched(data);
                return data;
            }
            if (handlers != 0)
                throw new InvalidDataException(
                    "Nombre inattendu de gestionnaires 1 dans AF4_sklad04.scr.");

            Regex marker = new Regex(
                @"(?m)^(\s*Whenever\s+inrange\s*\(\s*_PlayerInRange\s*\(\s*20\s*\)\s*\)\s*\{)",
                RegexOptions.IgnoreCase);
            if (marker.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Point d'insertion du mecanicien Africa 5 introuvable.");
            string eol = text.IndexOf("\r\n", StringComparison.Ordinal) >= 0
                ? "\r\n" : "\n";
            string handler = "OnSignal(1){" + eol
                + "  SetAlarmType(2, true);" + eol
                + "  goto ACTIVATE;" + eol
                + "}" + eol + eol;
            return ansi.GetBytes(marker.Replace(text, handler + "$1", 1));
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireCount(text, @"OnSignal\s*\(\s*1\s*\)", 1,
                "Le gestionnaire 1 d'AF4_sklad04 n'est pas unique.");
            Require(text,
                @"OnSignal\s*\(\s*1\s*\)\s*\{[\s\S]{0,100}"
                + @"SetAlarmType\s*\(\s*2\s*,\s*true\s*\)\s*;[\s\S]{0,100}"
                + @"goto\s+ACTIVATE\s*;[\s\S]{0,40}\}",
                "Le reveil du mecanicien 04 est incomplet.");
            Require(text, @"Label\s+ACTIVATE\s*:[\s\S]{0,180}"
                + @"HUMAN_Suspend\s*\(\s*false\s*\)",
                "Le label ACTIVATE d'AF4_sklad04 est incomplet.");
            Require(text, @"Whenever\s+inrange\s*\(\s*_PlayerInRange\s*\(\s*20\s*\)",
                "Le detecteur de proximite d'AF4_sklad04 a ete altere.");
        }

        private static void ValidateAssets(string gamePath)
        {
            string activator = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA5/AF4_sklad_activator.scr", ScriptArchives));
            Require(activator,
                @"FRM_FindFrame\s*\(\s*af4_sklad04\s*,\s*""AF4_sklad04""\s*\)",
                "Le mecanicien 04 est absent de l'activateur du magasin.");
            Require(activator,
                @"SendSignal\s*\(\s*af4_sklad04\s*,\s*1\s*\)",
                "Le signal officiel vers le mecanicien 04 est absent.");

            foreach (string neighbor in new[] { "02", "03", "05", "06", "07" })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA5/AF4_sklad" + neighbor + ".scr",
                    ScriptArchives));
                Require(script,
                    @"OnSignal\s*\(\s*1\s*\)\s*\{[\s\S]{0,160}"
                    + @"SetAlarmType\s*\(\s*2\s*,\s*true\s*\)\s*;[\s\S]{0,160}"
                    + @"goto\s+ACTIVATE\s*;",
                    "Reaction de reference absente chez AF4_sklad" + neighbor + ".");
            }

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF4_sklad04", "AF4_sklad04.scr")
                || !HasBinding(registry,
                    "Box03", "AF4_sklad_activator.scr"))
                throw new InvalidDataException(
                    "Liaisons officielles du magasin Africa 5 incompletes.");
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static void RequireCount(
            string text, string pattern, int expected, string message)
        {
            if (Regex.Matches(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline).Count != expected)
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 5 trop court.");
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
                    "Registre de scripts Africa 5 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 5.");
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