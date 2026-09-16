using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class CoBurgundy1StealthObjectiveInstaller
    {
        private const string ScriptPath =
            "Scripts/Co_Burgundy1/bu1_objective_05.scr";
        private const string SoloScriptPath =
            "Scripts/Burgundy1/bu1_objective_05.scr";
        private const string MapListPath = "mpmaplist.txt";
        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] coop = ReadSource(ResolveSource(gamePath, ScriptPath));
            byte[] patched = PatchScript(coop);
            ValidateScript(patched);
            byte[] solo = ReadSource(ResolveSource(gamePath, SoloScriptPath));
            if (!BytesEqual(patched, solo))
                throw new InvalidDataException(
                    "Le correctif Burgundy 1 coop ne rejoint pas le script solo officiel.");
            string list = File.ReadAllText(Path.Combine(gamePath, MapListPath),
                Encoding.GetEncoding(1252));
            string updated = AddObjectives(list);
            if (!String.Equals(updated, AddObjectives(updated),
                StringComparison.Ordinal))
                throw new InvalidDataException(
                    "L'ajout des objectifs Burgundy 1 coop n'est pas idempotent.");
            return "Burgundy 1 cooperatif verifie : les objectifs 15566 et 15567 "
                + "et leur controleur solo de reference sont complets.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string script = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
                if (!File.Exists(script)) return false;
                ValidateScript(File.ReadAllBytes(script));
                string list = File.ReadAllText(
                    Path.Combine(gamePath, MapListPath), Encoding.GetEncoding(1252));
                Match map = FindMission(list);
                return map.Success && HasObjective(map.Value, "15566")
                    && HasObjective(map.Value, "15567");
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
                "Reactivation des objectifs de discretion Burgundy 1 cooperatif...");
            DormantSource source = ResolveSource(gamePath, ScriptPath);
            string scriptTarget = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
            byte[] originalScript = File.Exists(scriptTarget)
                ? File.ReadAllBytes(scriptTarget) : ReadSource(source);
            byte[] patchedScript = PatchScript(originalScript);
            ValidateScript(patchedScript);
            if (!BytesEqual(originalScript, patchedScript))
            {
                InstallerCore.PrepareTarget(
                    gamePath, ScriptPath, scriptTarget, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(scriptTarget));
                WriteBytes(scriptTarget, ScriptPath, patchedScript, journal);
            }

            string mapTarget = InstallerCore.SafeGameTarget(gamePath, MapListPath);
            string originalList = File.ReadAllText(
                mapTarget, Encoding.GetEncoding(1252));
            string updatedList = AddObjectives(originalList);
            if (!String.Equals(originalList, updatedList, StringComparison.Ordinal))
            {
                InstallerCore.PrepareTarget(
                    gamePath, MapListPath, mapTarget, journal, prepared);
                WriteText(mapTarget, MapListPath, updatedList, journal);
            }
            InstallerCore.Log(
                "Burgundy 1 coop : objectifs de discretion 5 et 6 reactives.");
            InstallerCore.Report(progress,
                "Burgundy 1 cooperatif : les deux objectifs de discretion sont actifs.");
        }

        internal static string AddObjectives(string mapList)
        {
            Match map = FindMission(mapList);
            if (!map.Success)
                throw new InvalidDataException(
                    "Entree Burgundy 1 cooperative introuvable ou ambigue.");
            bool has5 = HasObjective(map.Value, "15566");
            bool has6 = HasObjective(map.Value, "15567");
            if (has5 && has6) return mapList;
            if (has5 || has6)
                throw new InvalidDataException(
                    "Liste Burgundy 1 cooperative partiellement modifiee.");
            foreach (string textId in new[] { "15560", "15561", "15562", "15563" })
                if (!HasObjective(map.Value, textId))
                    throw new InvalidDataException(
                        "Objectif Burgundy 1 de reference manquant : " + textId + ".");
            if (Regex.Matches(map.Value, @"<OBJECTIVE\b",
                RegexOptions.IgnoreCase).Count != 4)
                throw new InvalidDataException(
                    "Structure inattendue des objectifs Burgundy 1 cooperatif.");
            Regex closing = new Regex(@"(?m)^([ \t]*)</MAP>\s*$",
                RegexOptions.IgnoreCase);
            Match close = closing.Match(map.Value);
            if (!close.Success || closing.Matches(map.Value).Count != 1)
                throw new InvalidDataException(
                    "Fin de l'entree Burgundy 1 cooperative introuvable.");
            string newline = map.Value.Contains("\r\n") ? "\r\n" : "\n";
            string indent = close.Groups[1].Value;
            string replacement = indent
                + "<OBJECTIVE allied_text=\"15566\" axis_text=\"15566\" value=\"03\"/>"
                + newline + indent
                + "<OBJECTIVE allied_text=\"15567\" axis_text=\"15567\" value=\"03\"/>"
                + newline + indent + "</MAP>";
            string updated = closing.Replace(map.Value, replacement, 1);
            return mapList.Substring(0, map.Index) + updated
                + mapList.Substring(map.Index + map.Length);
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (Regex.IsMatch(text,
                @"Whenever\s+obj6done[\s\S]{0,500}SetObjectiveStatus\s*\(\s*6\s*,\s*1\s*\)",
                RegexOptions.IgnoreCase))
                return data;
            Regex wrong = new Regex(
                @"(Whenever\s+obj6done[\s\S]{0,500}?SetObjectiveStatus\s*\(\s*)5(\s*,\s*1\s*\))",
                RegexOptions.IgnoreCase);
            Match match = wrong.Match(text);
            if (!match.Success || wrong.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue de l'objectif 6 Burgundy 1 cooperatif.");
            text = text.Substring(0, match.Index) + match.Groups[1].Value
                + "6" + match.Groups[2].Value
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(text);
        }

        private static void ValidateScript(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!Regex.IsMatch(text,
                    @"Whenever\s+obj6done[\s\S]{0,500}SetObjectiveStatus\s*\(\s*6\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(text,
                    @"Whenever\s+obj5done[\s\S]{0,400}SetObjectiveStatus\s*\(\s*5\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Objectifs de discretion Burgundy 1 cooperatif non repares.");
        }

        private static Match FindMission(string mapList)
        {
            Regex pattern = new Regex(
                @"<MAP\b(?=[^>]*\bdir\s*=\s*""Co_Burgundy1"")[\s\S]*?</MAP>",
                RegexOptions.IgnoreCase);
            MatchCollection matches = pattern.Matches(mapList);
            return matches.Count == 1 ? matches[0] : Match.Empty;
        }

        private static bool HasObjective(string map, string textId)
        {
            return Regex.IsMatch(map,
                @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*""" + textId
                + @"""[^>]*\baxis_text\s*=\s*""" + textId + @"""",
                RegexOptions.IgnoreCase);
        }

        private static DormantSource ResolveSource(string gamePath, string relative)
        {
            InstallerCore.ValidateGamePath(gamePath);
            DormantSource result = null;
            foreach (string archiveName in ScriptArchives)
            {
                string archivePath = Path.Combine(gamePath, archiveName);
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                        if (String.Equals(entry.Name.Replace((char)92, '/'), relative,
                            StringComparison.OrdinalIgnoreCase))
                            result = new DormantSource {
                                ArchivePath = archivePath, EntryIndex = entry.Index };
            }
            if (result == null)
                throw new InvalidDataException(
                    "Script officiel introuvable : " + relative);
            return result;
        }

        private static byte[] ReadSource(DormantSource source)
        {
            using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                return archive.Read(archive.Entries[source.EntryIndex]);
        }

        private static void WriteBytes(
            string target, string relative, byte[] data, StateJournal journal)
        {
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, data);
                File.Copy(temporary, target, true);
                journal.RecordHash(relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        private static void WriteText(
            string target, string relative, string text, StateJournal journal)
        {
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllText(temporary, text, Encoding.GetEncoding(1252));
                File.Copy(temporary, target, true);
                journal.RecordHash(relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
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