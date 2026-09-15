using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class CoLibye2ObjectiveInstaller
    {
        private const string RelativeMapList = "mpmaplist.txt";

        public static string ValidateOnly(string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);
            string path = Path.Combine(gamePath, RelativeMapList);
            string original = File.ReadAllText(path, Encoding.GetEncoding(1252));
            string patched = AddVehicleObjective(original);
            if (String.Equals(original, patched, StringComparison.Ordinal))
                throw new InvalidDataException(
                    "L'objectif de degats aux vehicules Libye 2 cooperatif semble deja declare.");
            return "Libye 2 cooperatif verifie : l'objectif optionnel 15523 possede son texte, "
                + "son detecteur et sa validation complete.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string path = Path.Combine(gamePath, RelativeMapList);
                if (!File.Exists(path)) return false;
                string mapList = File.ReadAllText(path, Encoding.GetEncoding(1252));
                Match map = FindMission(mapList);
                return map.Success
                    && Regex.IsMatch(map.Value,
                        @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*""15523""[^>]*\baxis_text\s*=\s*""15523""",
                        RegexOptions.IgnoreCase);
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
                "Reactivation de l'objectif vehicules de Libye 2 cooperatif...");
            string target = InstallerCore.SafeGameTarget(gamePath, RelativeMapList);
            string original = File.ReadAllText(target, Encoding.GetEncoding(1252));
            string patched = AddVehicleObjective(original);
            if (String.Equals(original, patched, StringComparison.Ordinal))
            {
                InstallerCore.Log(
                    "Libye 2 cooperatif : objectif vehicules deja declare.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, RelativeMapList, target, journal, prepared);
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllText(temporary, patched, Encoding.GetEncoding(1252));
                File.Copy(temporary, target, true);
                journal.RecordHash(RelativeMapList,
                    CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Libye 2 cooperatif : objectif optionnel 15523 ajoute a la liste multijoueur.");
            InstallerCore.Report(progress,
                "Libye 2 cooperatif : objectif de destruction des vehicules reactive.");
        }

        internal static string AddVehicleObjective(string mapList)
        {
            Match map = FindMission(mapList);
            if (!map.Success)
                throw new InvalidDataException(
                    "Entree Libye 2 cooperative introuvable ou ambigue dans mpmaplist.txt.");
            if (Regex.IsMatch(map.Value,
                @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*""15523""[^>]*\baxis_text\s*=\s*""15523""",
                RegexOptions.IgnoreCase))
                return mapList;
            if (!Regex.IsMatch(map.Value,
                    @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*""15520""",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(map.Value,
                    @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*""15521""",
                    RegexOptions.IgnoreCase)
                || Regex.Matches(map.Value, @"<OBJECTIVE\b",
                    RegexOptions.IgnoreCase).Count != 2)
                throw new InvalidDataException(
                    "Structure inattendue des objectifs Libye 2 cooperatif.");

            Regex closing = new Regex(@"(?m)^([ \t]*)</MAP>\s*$",
                RegexOptions.IgnoreCase);
            Match close = closing.Match(map.Value);
            if (!close.Success || closing.Matches(map.Value).Count != 1)
                throw new InvalidDataException(
                    "Fin de l'entree Libye 2 cooperative introuvable.");
            string newline = map.Value.Contains("\r\n") ? "\r\n" : "\n";
            string indentation = close.Groups[1].Value;
            string replacement = indentation
                + "<OBJECTIVE allied_text=\"15523\" axis_text=\"15523\" value=\"03\"/>"
                + newline + indentation + "</MAP>";
            string updatedMap = closing.Replace(map.Value, replacement, 1);
            return mapList.Substring(0, map.Index) + updatedMap
                + mapList.Substring(map.Index + map.Length);
        }

        private static Match FindMission(string mapList)
        {
            Regex pattern = new Regex(
                @"<MAP\b(?=[^>]*\bdir\s*=\s*""Co_Libye2"")[\s\S]*?</MAP>",
                RegexOptions.IgnoreCase);
            MatchCollection matches = pattern.Matches(mapList);
            if (matches.Count != 1) return Match.Empty;
            return matches[0];
        }
    }
}