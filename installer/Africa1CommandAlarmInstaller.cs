using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa1CommandAlarmInstaller
    {
        private static readonly string[] ScriptPaths = {
            "Scripts/AFRICA1/AF1_07.scr",
            "Scripts/AFRICA1/AF1_08.scr",
            "Scripts/AFRICA1/AF1_09.scr",
            "Scripts/AFRICA1/AF1_10.scr"
        };

        private const string RegistryPath = "Missions/AFRICA1/Scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            int changed = 0;
            foreach (string relative in ScriptPaths)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(relative, original);
                if (!BytesEqual(original, patched)) changed++;
                ValidatePatched(relative, patched);
                if (!BytesEqual(patched, PatchScript(relative, patched)))
                    throw new InvalidDataException(
                        "Le correctif d'alarme Africa 1 n'est pas idempotent.");
            }
            if (changed != ScriptPaths.Length)
                throw new InvalidDataException(
                    "Le groupe de commandement Africa 1 ne presente pas les quatre erreurs attendues.");
            ValidateAssets(gamePath);
            return "Africa 1 verifie : les dix alertes du groupe de commandement "
                + "rejoignent de nouveau les reactions officielles des quatre gardes.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string relative in ScriptPaths)
                {
                    string target = InstallerCore.SafeGameTarget(gamePath, relative);
                    if (!File.Exists(target)) return false;
                    ValidatePatched(relative, File.ReadAllBytes(target));
                }
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
                "Restauration des alertes du groupe de commandement Africa 1...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (string relative in ScriptPaths)
            {
                DormantSource source = ResolveSource(
                    gamePath, relative, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(relative, original);
                ValidatePatched(relative, patched);
                if (BytesEqual(original, patched)) continue;

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
                changed++;
            }
            InstallerCore.Log(
                "Africa 1 : alarmes du groupe de commandement restaurees dans "
                + changed + " scripts.");
            InstallerCore.Report(progress,
                "Les quatre gardes du commandement Africa 1 se previennent de nouveau.");
        }

        private static byte[] PatchScript(string relative, byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            foreach (string actor in Targets(relative))
            {
                Regex correct = SignalRegex(actor, 20);
                Regex wrong = SignalRegex(actor, 10);
                int correctCount = correct.Matches(text).Count;
                int wrongCount = wrong.Matches(text).Count;
                if (correctCount == 1 && wrongCount == 0) continue;
                if (correctCount != 0 || wrongCount != 1)
                    throw new InvalidDataException(
                        "Structure inattendue du signal Africa 1 vers " + actor + ".");
                text = wrong.Replace(text, "${1}20${2}", 1);
            }
            return ansi.GetBytes(text);
        }

        private static void ValidatePatched(string relative, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            foreach (string actor in Targets(relative))
                if (SignalRegex(actor, 20).Matches(text).Count != 1
                    || SignalRegex(actor, 10).Matches(text).Count != 0)
                    throw new InvalidDataException(
                        "Alerte Africa 1 invalide vers " + actor + ".");
        }

        private static string[] Targets(string relative)
        {
            string file = Path.GetFileName(relative).ToLowerInvariant();
            if (file == "af1_07.scr") return new[] { "af08", "af09" };
            if (file == "af1_08.scr") return new[] { "af07", "af09" };
            if (file == "af1_09.scr") return new[] { "af07", "af08" };
            if (file == "af1_10.scr")
                return new[] { "af07", "af08", "af09", "af12" };
            throw new InvalidDataException(
                "Script Africa 1 non pris en charge : " + relative);
        }

        private static Regex SignalRegex(string actor, int signal)
        {
            return new Regex(
                @"(?m)^(\s*SendSignal\s*\(\s*" + Regex.Escape(actor)
                + @"\s*,\s*)" + signal + @"(\s*\)\s*;\s*)$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidateAssets(string gamePath)
        {
            foreach (string actor in new[] {
                "AF1_07", "AF1_08", "AF1_09", "AF1_12"
            })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA1/" + actor + ".scr", ScriptArchives));
                if (!Regex.IsMatch(script,
                    @"OnSignal\s*\(\s*20\s*\)[\s\S]{0,80}(?:goto|Label)\s+ALERT",
                    RegexOptions.IgnoreCase)
                    || Regex.IsMatch(script,
                        @"OnSignal\s*\(\s*10\s*\)", RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Contrat d'alerte officiel incomplet pour " + actor + ".");
            }

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            foreach (string actor in new[] {
                "AF1_07", "AF1_08", "AF1_09", "AF1_10", "AF1_12"
            })
                if (!HasBinding(registry, actor, actor + ".scr"))
                    throw new InvalidDataException(
                        "Liaison officielle Africa 1 absente pour " + actor + ".");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 1 trop court.");
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
                    "Registre de scripts Africa 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 1.");
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