using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Normandy2BlueCounterfireInstaller
    {
        private const string RegistryPath = "Missions/NORMANDY2/Scripts.dta";
        private const string ActorsPath = "Missions/NORMANDY2/actors.bin";
        private const string ScenePath = "Missions/NORMANDY2/scene2.bin";

        private static readonly int[] SoldierNumbers = {
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 17
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (int number in SoldierNumbers)
            {
                string relative = ScriptPath(number);
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(original);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "La riposte Blue " + number
                        + " semble deja corrigee dans les archives.");
                ValidatePatched(patched, number);
                if (!BytesEqual(patched, PatchScript(patched)))
                    throw new InvalidDataException(
                        "La correction des ripostes Blue n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Normandy 2 verifie : les quinze soldats Blue presents "
                + "conservent la cible Ally 5 dans leur cinquieme riposte.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (int number in SoldierNumbers)
                {
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, ScriptPath(number));
                    if (!File.Exists(target)) return false;
                    ValidatePatched(File.ReadAllBytes(target), number);
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
                "Correction des ripostes des defenseurs Blue de Normandy 2...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (int number in SoldierNumbers)
            {
                string relative = ScriptPath(number);
                DormantSource source = ResolveSource(
                    gamePath, relative, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(original);
                ValidatePatched(patched, number);
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
                "Normandy 2 : " + changed
                + " ripostes Blue vers Ally 5 corrigees.");
            InstallerCore.Report(progress,
                "Les defenseurs Blue conservent maintenant leur cinquieme cible.");
        }

        private static string ScriptPath(int number)
        {
            return "Scripts/NORMANDY2/R_N2_Blue_" + number + ".scr";
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Match signal = Regex.Match(text,
                @"\bOnSignal\s*\(\s*5\s*\)", RegexOptions.IgnoreCase);
            if (!signal.Success || Regex.Matches(text,
                @"\bOnSignal\s*\(\s*5\s*\)",
                RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(
                    "Branche Ally 5 absente ou ambigue dans un script Blue.");
            Match nextHandler = Regex.Match(text.Substring(signal.Index),
                @"(?m)^\s*On(?:Alarm|AlarmDone|Death)\s*\(",
                RegexOptions.IgnoreCase);
            if (!nextHandler.Success)
                throw new InvalidDataException(
                    "Fin de la branche Ally 5 introuvable dans un script Blue.");
            int end = signal.Index + nextHandler.Index;
            string branch = text.Substring(signal.Index, end - signal.Index);
            if (!Regex.IsMatch(branch,
                @"\bLabel\s+loop_A5\s*:", RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Boucle Ally 5 absente dans un script Blue.");

            Regex correct = new Regex(
                @"(?m)^(\s*goto\s+)loop_A5(\s*;\s*)$",
                RegexOptions.IgnoreCase);
            Regex wrong = new Regex(
                @"(?m)^(\s*goto\s+)loop_A1(\s*;\s*)$",
                RegexOptions.IgnoreCase);
            int correctCount = correct.Matches(branch).Count;
            int wrongCount = wrong.Matches(branch).Count;
            if (correctCount == 1 && wrongCount == 0) return data;
            if (correctCount != 0 || wrongCount != 1)
                throw new InvalidDataException(
                    "Saut final Ally 5 absent ou ambigu dans un script Blue.");
            branch = wrong.Replace(branch, "${1}loop_A5${2}", 1);
            return ansi.GetBytes(text.Substring(0, signal.Index)
                + branch + text.Substring(end));
        }

        private static void ValidatePatched(byte[] data, int number)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Match signal = Regex.Match(text,
                @"\bOnSignal\s*\(\s*5\s*\)", RegexOptions.IgnoreCase);
            Match nextHandler = signal.Success
                ? Regex.Match(text.Substring(signal.Index),
                    @"(?m)^\s*On(?:Alarm|AlarmDone|Death)\s*\(",
                    RegexOptions.IgnoreCase)
                : Match.Empty;
            if (!signal.Success || !nextHandler.Success)
                throw new InvalidDataException(
                    "Branche Ally 5 invalide pour Blue " + number + ".");
            string branch = text.Substring(
                signal.Index, nextHandler.Index);
            if (!Regex.IsMatch(branch,
                    @"\bLabel\s+loop_A5\s*:", RegexOptions.IgnoreCase)
                || Regex.Matches(branch,
                    @"(?m)^\s*goto\s+loop_A5\s*;\s*$",
                    RegexOptions.IgnoreCase).Count != 1
                || Regex.IsMatch(branch,
                    @"(?m)^\s*goto\s+loop_A1\s*;\s*$",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "La riposte Ally 5 reste incorrecte pour Blue "
                    + number + ".");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            string actors = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, ActorsPath, MissionArchives)));
            string scene = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, ScenePath, MissionArchives)));
            foreach (int number in SoldierNumbers)
            {
                string actor = "Blue_" + number;
                string script = "R_N2_Blue_" + number + ".scr";
                if (!HasBinding(registry, actor, script))
                    throw new InvalidDataException(
                        "Liaison officielle absente pour " + actor + ".");
                string marker = actor + "\0";
                if (actors.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0
                    && scene.IndexOf(marker,
                        StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Acteur commercial absent pour " + actor + ".");
            }
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
