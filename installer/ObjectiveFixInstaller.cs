using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal sealed class ObjectiveScriptSource
    {
        public string ArchivePath;
        public int EntryIndex;
        public string RelativePath;
    }

    internal static class ObjectiveFixInstaller
    {
        private static readonly string[] ScriptPaths = {
            "Scripts/AFRICA1/AF1_obj_carnage.scr",
            "Scripts/AFRICA2/AF2_tank1_01.scr",
            "Scripts/ARCTIC3/R_Ar3_objectives.scr",
            "Scripts/ARCTIC2/R_Arc1B_objective5.scr",
            "Scripts/NORMANDY2/R_N2_OBJECTIVES.scr",
            "Scripts/LIBYE3/dummy_objectives.scr",
            "Scripts/AFRICA6/AF5_obj.scr",
            "Scripts/AFRICA5/AF4_letadla_organizer.scr",
            "Scripts/Burgundy1/bu1_objective_01.scr",
            "Scripts/Co_Burgundy3/bur3_objectives.scr",
            "Scripts/Co_Burgundy3/bur3_obj3.scr",
            "Scripts/CZECH2/R_Cz2_objectives.scr"
        };

        private static readonly string[] ArchiveNames = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            Dictionary<string, ObjectiveScriptSource> sources = ResolveSources(gamePath);
            int pending = 0;
            int alreadyActive = 0;
            foreach (string relative in ScriptPaths)
            {
                ObjectiveScriptSource source = sources[relative];
                using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                {
                    byte[] original = archive.Read(archive.Entries[source.EntryIndex]);
                    byte[] patched = PatchScript(relative, original);
                    if (BytesEqual(original, patched)) alreadyActive++;
                    else pending++;
                    ValidatePatched(relative, patched);
                    if (!BytesEqual(patched, PatchScript(relative, patched)))
                        throw new InvalidDataException(
                            "Un correctif d'objectif n'est pas idempotent : " + relative);
                }
            }
            return "Objectifs verifies : 11 ensembles reproductibles, "
                + pending + " a activer et " + alreadyActive + " deja actifs "
                + "(Carnage Africa 1, Arctic 3, cinq charges Arctic 2, Africa 2, Normandy 2, "
                + "Libye 3, survie dans Africa 6, "
                + "compteur des cinq avions Africa 5, second sabotage de Burgundy 1, "
                + "chaine des prisonniers de Burgundy 3 cooperatif et sortie de Czech 2).";
        }

        public static int CountActiveObjectives(string gamePath)
        {
            Dictionary<string, ObjectiveScriptSource> sources = ResolveSources(gamePath);
            int active = 0;
            bool burgundyObjectives = false;
            bool burgundyPrisoners = false;
            foreach (string relative in ScriptPaths)
            {
                bool ready = IsCurrentOrOfficialActive(
                    gamePath, relative, sources[relative]);
                if (relative.EndsWith("Co_Burgundy3/bur3_objectives.scr",
                    StringComparison.OrdinalIgnoreCase))
                    burgundyObjectives = ready;
                else if (relative.EndsWith("Co_Burgundy3/bur3_obj3.scr",
                    StringComparison.OrdinalIgnoreCase))
                    burgundyPrisoners = ready;
                else if (ready) active++;
            }
            if (burgundyObjectives && burgundyPrisoners) active++;
            return active;
        }

        private static bool IsCurrentOrOfficialActive(
            string gamePath, string relative, ObjectiveScriptSource source)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] current;
                if (File.Exists(target)) current = File.ReadAllBytes(target);
                else
                    using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                        current = archive.Read(archive.Entries[source.EntryIndex]);
                return BytesEqual(current, PatchScript(relative, current));
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
                "Reparation des objectifs optionnels jamais validables...");
            Dictionary<string, ObjectiveScriptSource> sources = ResolveSources(gamePath);
            int changed = 0;
            foreach (string relative in ScriptPaths)
            {
                ObjectiveScriptSource source = sources[relative];
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original;
                if (File.Exists(target))
                    original = File.ReadAllBytes(target);
                else
                    using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                        original = archive.Read(archive.Entries[source.EntryIndex]);
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
                    journal.RecordHash(relative, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                changed++;
            }
            InstallerCore.Log("Objectifs optionnels : " + changed + " scripts corriges.");
            InstallerCore.Report(progress, "Objectifs repares : Carnage Africa 1, Arctic 3, "
                + "cinq charges Arctic 2, Africa 2, Normandy 2, Libye 3, "
                + "survie de l'equipe dans Africa 6, "
                + "compteur des cinq avions Africa 5, second sabotage de Burgundy 1, "
                + "chaine des prisonniers de Burgundy 3 cooperatif et sortie de Czech 2.");
        }

        private static Dictionary<string, ObjectiveScriptSource> ResolveSources(
            string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);
            Dictionary<string, ObjectiveScriptSource> result =
                new Dictionary<string, ObjectiveScriptSource>(StringComparer.OrdinalIgnoreCase);
            foreach (string archiveName in ArchiveNames)
            {
                string archivePath = Path.Combine(gamePath, archiveName);
                if (!File.Exists(archivePath))
                    throw new FileNotFoundException("Archive de scripts manquante.", archivePath);
                using (DtaArchive archive = new DtaArchive(archivePath))
                {
                    foreach (DtaEntry entry in archive.Entries)
                    {
                        string normalized = entry.Name.Replace((char)92, '/');
                        foreach (string relative in ScriptPaths)
                            if (String.Equals(normalized, relative,
                                StringComparison.OrdinalIgnoreCase))
                                result[relative] = new ObjectiveScriptSource {
                                    ArchivePath = archivePath,
                                    EntryIndex = entry.Index,
                                    RelativePath = relative
                                };
                    }
                }
            }
            foreach (string relative in ScriptPaths)
                if (!result.ContainsKey(relative))
                    throw new InvalidDataException(
                        "Script officiel introuvable : " + relative);
            return result;
        }

        private static byte[] PatchScript(string relative, byte[] source)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(source);
            if (relative.EndsWith("AFRICA1/AF1_obj_carnage.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchAfrica1Carnage(text);
            else if (relative.IndexOf("AF2_tank1_01", StringComparison.OrdinalIgnoreCase) >= 0)
                text = PatchAfrica2(text);
            else if (relative.IndexOf("R_Ar3_objectives", StringComparison.OrdinalIgnoreCase) >= 0)
                text = PatchArctic3(text);
            else if (relative.EndsWith("ARCTIC2/R_Arc1B_objective5.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchArctic2FiveCharges(text);
            else if (relative.IndexOf("R_N2_OBJECTIVES", StringComparison.OrdinalIgnoreCase) >= 0)
                text = PatchNormandy2(text);
            else if (relative.IndexOf("dummy_objectives", StringComparison.OrdinalIgnoreCase) >= 0
                && relative.IndexOf("LIBYE3", StringComparison.OrdinalIgnoreCase) >= 0)
                text = PatchLibye3(text);
            else if (relative.EndsWith("AFRICA6/AF5_obj.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchAfrica6Survival(text);
            else if (relative.EndsWith("AFRICA5/AF4_letadla_organizer.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchAfrica5AircraftCounter(text);
            else if (relative.EndsWith("Burgundy1/bu1_objective_01.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchBurgundy1FuelObjective(text);
            else if (relative.EndsWith("Co_Burgundy3/bur3_objectives.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchCoBurgundy3Objectives(text);
            else if (relative.EndsWith("Co_Burgundy3/bur3_obj3.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchCoBurgundy3RemainingPrisoners(text);
            else if (relative.EndsWith("CZECH2/R_Cz2_objectives.scr",
                StringComparison.OrdinalIgnoreCase))
                text = PatchCzech2ExitObjective(text);
            else
                throw new InvalidDataException("Correctif inconnu : " + relative);
            return ansi.GetBytes(text);
        }

        private static string PatchAfrica1Carnage(string text)
        {
            if (Regex.IsMatch(text,
                @"INTEGER\s+game_type\s*=\s*_SPGetGameType\s*\(\s*\)\s*;[\s\S]{0,900}Whenever\s+alldead[\s\S]{0,900}SetObjectiveStatus\s*\(\s*8\s*,\s*1\s*\)[\s\S]{0,600}SetObjectiveStatus\s*\(\s*8\s*,\s*0\s*\)",
                RegexOptions.IgnoreCase))
                return text;

            Regex variable = new Regex(
                @"(?m)^//\s*INTEGER\s+game_type\s*=\s*_SPGetGameType\s*\(\s*\)\s*;\s*$",
                RegexOptions.IgnoreCase);
            Regex completion = new Regex(
                @"(?ms)^//Whenever\s+alldead\s*\([^\r\n]+\)\s*\{.*?(?=^//\s*-{20,}\s*$)",
                RegexOptions.IgnoreCase);
            Regex activation = new Regex(
                @"(?ms)^//if\s*\(\(game_type\s*==\s*3\).*?(?=^Label\s+END\s*:)",
                RegexOptions.IgnoreCase);
            if (variable.Matches(text).Count != 1
                || completion.Matches(text).Count != 1
                || activation.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue de l'objectif Carnage Africa 1.");
            text = variable.Replace(text, "INTEGER game_type = _SPGetGameType();", 1);
            text = completion.Replace(text,
                match => Regex.Replace(match.Value, @"(?m)^//", String.Empty), 1);
            text = activation.Replace(text,
                match => Regex.Replace(match.Value, @"(?m)^//", String.Empty), 1);
            return text;
        }
        private static string PatchAfrica2(string text)
        {
            if (Regex.IsMatch(text,
                @"OnDeath\s*\(\s*\)\s*\{[^}]*SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)",
                RegexOptions.IgnoreCase))
                return text;
            Regex empty = new Regex(
                @"OnDeath\s*\(\s*\)\s*\{\s*EndScript\s*\(\s*\)\s*;\s*\}",
                RegexOptions.IgnoreCase);
            if (empty.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du script Africa 2.");
            string replacement =
                "OnDeath(){\r\n"
                + "  SUBTITLES_SetOn(true);\r\n"
                + "  SUBTITLES_SetText(06011205);\r\n"
                + "  Delay(2000);\r\n"
                + "  SetObjectiveStatus(2, 1);\r\n"
                + "  SUBTITLES_SetOn(false);\r\n"
                + "  EndScript();\r\n"
                + "}";
            return empty.Replace(text, replacement, 1);
        }

        private static string PatchArctic3(string text)
        {
            string wrong = "FRM_FindFrame(US2, \"Amik_2\")";
            string correct = "FRM_FindFrame(US2, \"Amik_1\")";
            if (text.IndexOf(correct, StringComparison.OrdinalIgnoreCase) >= 0)
                return text;
            int first = text.IndexOf(wrong, StringComparison.OrdinalIgnoreCase);
            if (first < 0 || text.IndexOf(wrong, first + wrong.Length,
                StringComparison.OrdinalIgnoreCase) >= 0)
                throw new InvalidDataException(
                    "Structure inattendue du script Arctic 3.");
            return text.Substring(0, first) + correct
                + text.Substring(first + wrong.Length);
        }

        private static string PatchNormandy2(string text)
        {
            if (Regex.IsMatch(text,
                @"counter\s*=\s*0\s*;[\s\S]{0,700}If\s*\(\s*counter\s*==\s*5\s*\)",
                RegexOptions.IgnoreCase))
                return text;
            Regex marker = new Regex(
                @"(?m)^[ \t]*If\s*\(\s*counter\s*==\s*5\s*\)",
                RegexOptions.IgnoreCase);
            Match match = marker.Match(text);
            if (!match.Success || marker.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du script Normandy 2.");
            string counter =
                "  counter = 0;\r\n"
                + "  If (( _ACTOR_GetState(Ally1) == 1 ))    { counter = counter + 1; }\r\n"
                + "  If (( _ACTOR_GetState(Ally2) == 1 ))    { counter = counter + 1; }\r\n"
                + "  If (( _ACTOR_GetState(Ally3) == 1 ))    { counter = counter + 1; }\r\n"
                + "  If (( _ACTOR_GetState(Ally4) == 1 ))    { counter = counter + 1; }\r\n"
                + "  If (( _ACTOR_GetState(Ally5) == 1 ))    { counter = counter + 1; }\r\n";
            return text.Insert(match.Index, counter);
        }

        private static string PatchLibye3(string text)
        {
            if (Regex.IsMatch(text,
                @"OnSignal\s*\(\s*3\s*\)\s*\{[\s\S]{0,500}_IsTeamMemberDead\s*\(\s*\)[\s\S]{0,300}SetObjectiveStatus\s*\(\s*4\s*,\s*1\s*\)",
                RegexOptions.IgnoreCase))
                return text;
            Regex marker = new Regex(
                @"(?m)^(\s*)SetObjectiveStatus\s*\(\s*3\s*,\s*1\s*\)\s*;",
                RegexOptions.IgnoreCase);
            Match match = marker.Match(text);
            if (!match.Success || marker.Matches(text).Count != 1
                || text.LastIndexOf("OnSignal(3)", match.Index,
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Structure inattendue du script Libye 3.");
            string indent = match.Groups[1].Value;
            string survival = indent
                + "If (( !_IsTeamMemberDead()) and (_SPGetGameType() != 2 ))\r\n"
                + indent + "  { SetObjectiveStatus(4, 1); }\r\n\r\n";
            return text.Insert(match.Index, survival);
        }

        private static string PatchBurgundy1FuelObjective(string text)
        {
            if (Regex.IsMatch(text,
                @"(?m)^[ \t]*if\s*\(\s*_LoadGameValue\s*\(\s*53\s*\)\s*!=\s*1\s*\)[\s\S]{0,160}^[ \t]*SetObjectiveStatus\s*\(\s*3\s*,\s*0\s*\)",
                RegexOptions.IgnoreCase))
                return text;
            Regex block = new Regex(
                @"(?m)^[ \t]*//\s*if\s*\(\s*_LoadGameValue\s*\(\s*53\s*\)\s*!=\s*1\s*\)\s*\r?\n"
                + @"[ \t]*//\s*\{\s*\r?\n"
                + @"[ \t]*//\s*SetObjectiveStatus\s*\(\s*3\s*,\s*0\s*\)\s*;\s*\r?\n"
                + @"[ \t]*//\s*\}\s*$",
                RegexOptions.IgnoreCase);
            if (block.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue de l'objectif du depot de carburant Burgundy 1.");
            string newline = text.Contains("\r\n") ? "\r\n" : "\n";
            string replacement = "  if(_LoadGameValue(53) != 1)" + newline
                + "  {" + newline
                + "    SetObjectiveStatus(3, 0);" + newline
                + "  }";
            return block.Replace(text, replacement, 1);
        }

        private static string PatchAfrica6Survival(string text)
        {
            if (Regex.IsMatch(text,
                @"Label\s+OBJ1COMPLETE\s*:[\s\S]{0,400}(?m:^[ \t]*if\s*\(\s*\(\s*!_IsTeamMemberDead\s*\(\s*\)\s*\)[\s\S]{0,180}^[ \t]*SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\))",
                RegexOptions.IgnoreCase))
                return text;
            Regex block = new Regex(
                @"(?m)^(\s*)//\s*if\s*\(\s*\(\s*!_IsTeamMemberDead\s*\(\s*\)\s*\)\s*AND\s*\(\s*_SPGetGameType\s*\(\s*\)\s*!=\s*2\s*\)\s*\)\s*\r?\n"
                + @"\1//\s*\{\s*\r?\n"
                + @"\1//\s*SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)\s*;\s*\r?\n"
                + @"\1//\s*\}\s*$",
                RegexOptions.IgnoreCase);
            Match match = block.Match(text);
            if (!match.Success || block.Matches(text).Count != 1
                || text.LastIndexOf("Label OBJ1COMPLETE", match.Index,
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Structure inattendue de l'objectif de survie Africa 6.");
            string newline = text.Contains("\r\n") ? "\r\n" : "\n";
            string indent = match.Groups[1].Value;
            string replacement = indent
                + "if((!_IsTeamMemberDead()) AND (_SPGetGameType() != 2))" + newline
                + indent + "{" + newline
                + indent + "  SetObjectiveStatus(2, 1);" + newline
                + indent + "}";
            return block.Replace(text, replacement, 1);
        }

        private static string PatchArctic2FiveCharges(string text)
        {
            if (Regex.IsMatch(text,
                @"If\s*\(\s*counter\s*==\s*5\s*\)\s*\{[\s\S]{0,180}SaveGameValue\s*\(\s*6\s*,\s*99\s*\)",
                RegexOptions.IgnoreCase))
                return text;

            Regex wrong = new Regex(
                @"(If\s*\(\s*counter\s*==\s*5\s*\)\s*\{[\s\S]{0,180}?SaveGameValue\s*\(\s*)5(\s*,\s*99\s*\)\s*;)",
                RegexOptions.IgnoreCase);
            Match match = wrong.Match(text);
            if (!match.Success || wrong.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du compteur des cinq charges Arctic 2.");
            return text.Substring(0, match.Index)
                + match.Groups[1].Value + "6" + match.Groups[2].Value
                + text.Substring(match.Index + match.Length);
        }
        private static string PatchAfrica5AircraftCounter(string text)
        {
            if (Regex.IsMatch(text,
                @"SaveGameValue\s*\(\s*21\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*22\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*23\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*24\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*25\s*,\s*1\s*\)\s*;",
                RegexOptions.IgnoreCase))
                return text;

            Regex duplicate = new Regex(
                @"SaveGameValue\s*\(\s*24\s*,\s*1\s*\)\s*;",
                RegexOptions.IgnoreCase);
            MatchCollection matches = duplicate.Matches(text);
            if (matches.Count != 2
                || Regex.IsMatch(text,
                    @"SaveGameValue\s*\(\s*25\s*,\s*1\s*\)\s*;",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Structure inattendue du compteur des avions Africa 5.");
            Match second = matches[1];
            return text.Substring(0, second.Index)
                + "SaveGameValue(25, 1);"
                + text.Substring(second.Index + second.Length);
        }
        private static string PatchCoBurgundy3Objectives(string text)
        {
            if (text.IndexOf("SetObjectiveStatus(1, 0);",
                    StringComparison.OrdinalIgnoreCase) >= 0
                && Regex.Matches(text,
                    @"(?m)^[ \t]*SetObjectiveStatus\s*\(\s*1\s*,\s*1\s*\)\s*;",
                    RegexOptions.IgnoreCase).Count == 5
                && Regex.IsMatch(text,
                    @"(?m)^[ \t]*SetObjectiveStatus\s*\(\s*1\s*,\s*2\s*\)\s*;",
                    RegexOptions.IgnoreCase)
                && Regex.IsMatch(text,
                    @"OnSignal\s*\(\s*13\s*\)[\s\S]{0,120}vsetci\s*=\s*0",
                    RegexOptions.IgnoreCase))
                return text;

            Regex activation = new Regex(
                @"SetObjectiveStatus\s*\(\s*1\s*,\s*4\s*\)\s*;",
                RegexOptions.IgnoreCase);
            Regex completion = new Regex(
                @"(?m)^(\s*)//\s*SetObjectiveStatus\s*\(\s*1\s*,\s*1\s*\)\s*;\s*$",
                RegexOptions.IgnoreCase);
            Regex failure = new Regex(
                @"(?m)^(\s*)//\s*SetObjectiveStatus\s*\(\s*1\s*,\s*2\s*\)\s*;\s*$",
                RegexOptions.IgnoreCase);
            if (activation.Matches(text).Count != 1
                || completion.Matches(text).Count != 5
                || failure.Matches(text).Count != 1
                || Regex.IsMatch(text, @"OnSignal\s*\(\s*13\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Structure inattendue de la chaine des prisonniers Burgundy 3 cooperatif.");

            string newline = text.Contains("\r\n") ? "\r\n" : "\n";
            text = activation.Replace(text, "SetObjectiveStatus(1, 0);", 1);
            text = completion.Replace(text,
                match => match.Groups[1].Value + "SetObjectiveStatus(1, 1);");
            text = failure.Replace(text,
                match => match.Groups[1].Value + "SetObjectiveStatus(1, 2);", 1);
            return text.TrimEnd() + newline + newline
                + "OnSignal(13)  // one of the four remaining prisoners died" + newline
                + "{" + newline
                + "  vsetci=0;" + newline
                + "}" + newline;
        }

        private static string PatchCoBurgundy3RemainingPrisoners(string text)
        {
            string anyAlive = "If((_ACTOR_GetState(zajatec01)) OR "
                + "(_ACTOR_GetState(zajatec02)) OR (_ACTOR_GetState(zajatec03)) "
                + "OR (_ACTOR_GetState(zajatec04)))";
            string allDead = "Whenever obj3_failed ((!_ACTOR_GetState(zajatec01)) "
                + "AND (!_ACTOR_GetState(zajatec02)) AND (!_ACTOR_GetState(zajatec03)) "
                + "AND (!_ACTOR_GetState(zajatec04)))";
            if (text.IndexOf(anyAlive, StringComparison.OrdinalIgnoreCase) >= 0
                && text.IndexOf(allDead, StringComparison.OrdinalIgnoreCase) >= 0
                && text.IndexOf("SendSignal(obj, 13);",
                    StringComparison.OrdinalIgnoreCase) >= 0)
                return text;

            Regex successCondition = new Regex(
                @"If\s*\(\s*\(\s*_ACTOR_GetState\s*\(\s*zajatec01\s*\)\s*\)\s*AND\s*\(\s*_ACTOR_GetState\s*\(\s*zajatec02\s*\)\s*\)\s*OR\s*\(\s*_ACTOR_GetState\s*\(\s*zajatec03\s*\)\s*\)\s*AND\s*\(\s*_ACTOR_GetState\s*\(\s*zajatec04\s*\)\s*\)\s*\)",
                RegexOptions.IgnoreCase);
            Regex failureCondition = new Regex(
                @"Whenever\s+obj3_failed\s*\(\s*\(\s*!_ACTOR_GetState\s*\(\s*zajatec01\s*\)\s*\)\s*AND\s*\(\s*!_ACTOR_GetState\s*\(\s*zajatec02\s*\)\s*\)\s*OR\s*\(\s*!_ACTOR_GetState\s*\(\s*zajatec03\s*\)\s*\)\s*AND\s*\(\s*!_ACTOR_GetState\s*\(\s*zajatec04\s*\)\s*\)\s*\)",
                RegexOptions.IgnoreCase);
            Regex successSignal = new Regex(
                @"(?m)^(\s*)SendSignal\s*\(\s*obj\s*,\s*5\s*\)\s*;",
                RegexOptions.IgnoreCase);
            if (successCondition.Matches(text).Count != 1
                || failureCondition.Matches(text).Count != 1
                || successSignal.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du groupe de prisonniers Burgundy 3 cooperatif.");

            string newline = text.Contains("\r\n") ? "\r\n" : "\n";
            text = successCondition.Replace(text, anyAlive, 1);
            text = failureCondition.Replace(text, allDead, 1);
            text = successSignal.Replace(text, match =>
                match.Groups[1].Value
                + "If((!_ACTOR_GetState(zajatec01)) OR (!_ACTOR_GetState(zajatec02)) "
                + "OR (!_ACTOR_GetState(zajatec03)) OR (!_ACTOR_GetState(zajatec04)))" + newline
                + match.Groups[1].Value + "{" + newline
                + match.Groups[1].Value + "  SendSignal(obj, 13);" + newline
                + match.Groups[1].Value + "}" + newline
                + match.Groups[1].Value + "SendSignal(obj, 5);", 1);
            return text;
        }
        private static string PatchCzech2ExitObjective(string text)
        {
            bool activated = Regex.IsMatch(text,
                @"SetObjectiveStatus\s*\(\s*2\s*,\s*0\s*\)",
                RegexOptions.IgnoreCase);
            bool completed = Regex.IsMatch(text,
                @"OnSignal\s*\(\s*2\s*\)\s*\{[\s\S]{0,180}SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)",
                RegexOptions.IgnoreCase);
            if (activated && completed) return text;
            if (activated || completed)
                throw new InvalidDataException(
                    "Correction partielle de l'objectif de sortie Czech 2.");

            Regex captureComplete = new Regex(
                @"(?m)^([ \t]*)SetObjectiveStatus\s*\(\s*1\s*,\s*1\s*\)[ \t]*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Regex deathHandler = new Regex(
                @"(?m)^[ \t]*Whenever\s+det\s*\(\s*_SignalReceived\s*\(\s*3\s*\)\s*\)[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            if (captureComplete.Matches(text).Count != 1
                || deathHandler.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue de l'objectif de sortie Czech 2.");

            string newline = text.Contains("\r\n") ? "\r\n" : "\n";
            text = captureComplete.Replace(text, match =>
                match.Groups[1].Value + "SetObjectiveStatus(2, 0);" + newline
                + match.Value, 1);
            text = deathHandler.Replace(text,
                "OnSignal(2)" + newline
                + "{" + newline
                + "  SetObjectiveStatus(2, 1);" + newline
                + "  goto end;" + newline
                + "}" + newline + newline
                + "$0", 1);
            return text;
        }
        private static void ValidatePatched(string relative, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (relative.EndsWith("AFRICA1/AF1_obj_carnage.scr",
                StringComparison.OrdinalIgnoreCase)
                && !Regex.IsMatch(text,
                    @"INTEGER\s+game_type\s*=\s*_SPGetGameType\s*\(\s*\)\s*;[\s\S]{0,900}Whenever\s+alldead[\s\S]{0,900}SetObjectiveStatus\s*\(\s*8\s*,\s*1\s*\)[\s\S]{0,600}SetObjectiveStatus\s*\(\s*8\s*,\s*0\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Objectif Carnage Africa 1 non repare.");
            if (relative.IndexOf("AF2_tank1_01", StringComparison.OrdinalIgnoreCase) >= 0
                && !Regex.IsMatch(text,
                    @"OnDeath\s*\(\s*\)\s*\{[^}]*SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException("Objectif Africa 2 non repare.");
            if (relative.IndexOf("R_Ar3_objectives", StringComparison.OrdinalIgnoreCase) >= 0
                && text.IndexOf("FRM_FindFrame(US2, \"Amik_1\")",
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException("Objectif Arctic 3 non repare.");
            if (relative.EndsWith("ARCTIC2/R_Arc1B_objective5.scr",
                StringComparison.OrdinalIgnoreCase)
                && !Regex.IsMatch(text,
                    @"If\s*\(\s*counter\s*==\s*5\s*\)\s*\{[\s\S]{0,180}SaveGameValue\s*\(\s*6\s*,\s*99\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Objectif des cinq charges Arctic 2 non repare.");
            if (relative.IndexOf("R_N2_OBJECTIVES", StringComparison.OrdinalIgnoreCase) >= 0
                && !Regex.IsMatch(text,
                    @"counter\s*=\s*0\s*;[\s\S]{0,700}If\s*\(\s*counter\s*==\s*5\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException("Objectif Normandy 2 non repare.");
            if (relative.IndexOf("dummy_objectives", StringComparison.OrdinalIgnoreCase) >= 0
                && relative.IndexOf("LIBYE3", StringComparison.OrdinalIgnoreCase) >= 0
                && !Regex.IsMatch(text,
                    @"OnSignal\s*\(\s*3\s*\)\s*\{[\s\S]{0,500}_IsTeamMemberDead\s*\(\s*\)[\s\S]{0,300}SetObjectiveStatus\s*\(\s*4\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException("Objectif Libye 3 non repare.");
            if (relative.EndsWith("AFRICA6/AF5_obj.scr",
                StringComparison.OrdinalIgnoreCase)
                && !Regex.IsMatch(text,
                    @"Label\s+OBJ1COMPLETE\s*:[\s\S]{0,400}(?m:^[ \t]*if\s*\(\s*\(\s*!_IsTeamMemberDead\s*\(\s*\)\s*\)[\s\S]{0,180}^[ \t]*SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\))",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Objectif de survie Africa 6 non repare.");
            if (relative.EndsWith("AFRICA5/AF4_letadla_organizer.scr",
                StringComparison.OrdinalIgnoreCase)
                && !Regex.IsMatch(text,
                    @"SaveGameValue\s*\(\s*21\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*22\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*23\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*24\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*25\s*,\s*1\s*\)\s*;",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Compteur des avions Africa 5 non repare.");
            if (relative.EndsWith("Burgundy1/bu1_objective_01.scr",
                StringComparison.OrdinalIgnoreCase)
                && !Regex.IsMatch(text,
                    @"(?m)^[ \t]*if\s*\(\s*_LoadGameValue\s*\(\s*53\s*\)\s*!=\s*1\s*\)[\s\S]{0,160}^[ \t]*SetObjectiveStatus\s*\(\s*3\s*,\s*0\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Objectif du depot de carburant Burgundy 1 non repare.");
            if (relative.EndsWith("Co_Burgundy3/bur3_objectives.scr",
                StringComparison.OrdinalIgnoreCase)
                && (text.IndexOf("SetObjectiveStatus(1, 0);",
                        StringComparison.OrdinalIgnoreCase) < 0
                    || Regex.Matches(text,
                        @"(?m)^[ \t]*SetObjectiveStatus\s*\(\s*1\s*,\s*1\s*\)\s*;",
                        RegexOptions.IgnoreCase).Count != 5
                    || !Regex.IsMatch(text,
                        @"(?m)^[ \t]*SetObjectiveStatus\s*\(\s*1\s*,\s*2\s*\)\s*;",
                        RegexOptions.IgnoreCase)
                    || !Regex.IsMatch(text,
                        @"OnSignal\s*\(\s*13\s*\)[\s\S]{0,120}vsetci\s*=\s*0",
                        RegexOptions.IgnoreCase)))
                throw new InvalidDataException(
                    "Objectif principal Burgundy 3 cooperatif non repare.");
            if (relative.EndsWith("Co_Burgundy3/bur3_obj3.scr",
                StringComparison.OrdinalIgnoreCase)
                && (text.IndexOf("SendSignal(obj, 13);",
                        StringComparison.OrdinalIgnoreCase) < 0
                    || text.IndexOf("Whenever obj3_failed ((!_ACTOR_GetState(zajatec01)) AND (!_ACTOR_GetState(zajatec02)) AND (!_ACTOR_GetState(zajatec03)) AND (!_ACTOR_GetState(zajatec04)))",
                        StringComparison.OrdinalIgnoreCase) < 0))
                throw new InvalidDataException(
                    "Groupe de prisonniers Burgundy 3 cooperatif non repare.");
            if (relative.EndsWith("CZECH2/R_Cz2_objectives.scr",
                StringComparison.OrdinalIgnoreCase)
                && (!Regex.IsMatch(text,
                    @"SetObjectiveStatus\s*\(\s*2\s*,\s*0\s*\)",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(text,
                    @"OnSignal\s*\(\s*2\s*\)\s*\{[\s\S]{0,180}SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase)))
                throw new InvalidDataException(
                    "Objectif de sortie Czech 2 non repare.");
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
