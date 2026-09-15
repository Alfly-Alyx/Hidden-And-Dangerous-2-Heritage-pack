using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class FeatureStatusDetector
    {
        public static string BuildReport(string gamePath)
        {
            StringBuilder text = new StringBuilder();
            text.AppendLine("CMP 2.6.5 : " + DetectCmp(gamePath));
            text.AppendLine("Exploration libre : " + OfficialContentInstaller.DetectStatus(gamePath));
            text.AppendLine("Objectifs optionnels : " + DetectObjectives(gamePath));
            text.AppendLine("Guidages, routes et scripts officiels : " + DetectDormantGuidance(gamePath));
            text.AppendLine("Easter eggs Africa 1 et Africa 4 : " + DetectEasterEggs(gamePath));
            text.AppendLine("Vestiges Normandy3 Zone et Africa5 Prototype : "
                + DetectExperimentalVestiges(gamePath));
            text.AppendLine("Guides PDF : " + DetectGuides(gamePath));
            text.AppendLine(MissionUnlockInstaller.DescribeStatus(gamePath));
            return text.ToString().TrimEnd();
        }

        private static string DetectCmp(string gamePath)
        {
            string path = Path.Combine(gamePath, "cmp_info", "cmp_Maplist.txt");
            if (!File.Exists(path)) return "a installer";
            try
            {
                int maps = Regex.Matches(
                    File.ReadAllText(path, Encoding.GetEncoding(1252)),
                    @"<MAP\b", RegexOptions.IgnoreCase).Count;
                if (maps >= 156) return "deja installee (" + maps + " cartes et missions)";
                return "partielle (" + maps + " entrees)";
            }
            catch (Exception ex) { return "indeterminee (" + ex.Message + ")"; }
        }

        private static string DetectObjectives(string gamePath)
        {
            int ready = 0;
            string africa1Carnage = ReadOptional(gamePath,
                "Scripts/AFRICA1/AF1_obj_carnage.scr");
            if (Regex.IsMatch(africa1Carnage,
                @"INTEGER\s+game_type\s*=\s*_SPGetGameType\s*\(\s*\)\s*;[\s\S]{0,900}Whenever\s+alldead[\s\S]{0,900}SetObjectiveStatus\s*\(\s*8\s*,\s*1\s*\)[\s\S]{0,600}SetObjectiveStatus\s*\(\s*8\s*,\s*0\s*\)",
                RegexOptions.IgnoreCase)) ready++;
            string africa2 = ReadOptional(gamePath, "Scripts/AFRICA2/AF2_tank1_01.scr");
            if (Regex.IsMatch(africa2,
                @"OnDeath\s*\(\s*\)\s*\{[^}]*SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)",
                RegexOptions.IgnoreCase)) ready++;
            string arctic3 = ReadOptional(gamePath, "Scripts/ARCTIC3/R_Ar3_objectives.scr");
            if (arctic3.IndexOf("FRM_FindFrame(US2, \"Amik_1\")",
                StringComparison.OrdinalIgnoreCase) >= 0) ready++;
            string arctic2Charges = ReadOptional(gamePath,
                "Scripts/ARCTIC2/R_Arc1B_objective5.scr");
            if (Regex.IsMatch(arctic2Charges,
                @"If\s*\(\s*counter\s*==\s*5\s*\)\s*\{[\s\S]{0,180}SaveGameValue\s*\(\s*6\s*,\s*99\s*\)",
                RegexOptions.IgnoreCase)) ready++;
            string normandy2 = ReadOptional(gamePath, "Scripts/NORMANDY2/R_N2_OBJECTIVES.scr");
            if (Regex.IsMatch(normandy2,
                @"counter\s*=\s*0\s*;[\s\S]{0,700}If\s*\(\s*counter\s*==\s*5\s*\)",
                RegexOptions.IgnoreCase)) ready++;
            string libye3 = ReadOptional(gamePath, "Scripts/LIBYE3/dummy_objectives.scr");
            if (Regex.IsMatch(libye3,
                @"OnSignal\s*\(\s*3\s*\)\s*\{[\s\S]{0,500}_IsTeamMemberDead\s*\(\s*\)[\s\S]{0,300}SetObjectiveStatus\s*\(\s*4\s*,\s*1\s*\)",
                RegexOptions.IgnoreCase)) ready++;
            string africa6 = ReadOptional(gamePath, "Scripts/AFRICA6/AF5_obj.scr");
            if (Regex.IsMatch(africa6,
                @"Label\s+OBJ1COMPLETE\s*:[\s\S]{0,400}(?m:^[ \t]*if\s*\(\s*\(\s*!_IsTeamMemberDead\s*\(\s*\)\s*\)[\s\S]{0,180}^[ \t]*SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\))",
                RegexOptions.IgnoreCase)) ready++;
            string africa5Planes = ReadOptional(gamePath,
                "Scripts/AFRICA5/AF4_letadla_organizer.scr");
            if (Regex.IsMatch(africa5Planes,
                @"SaveGameValue\s*\(\s*21\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*22\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*23\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*24\s*,\s*1\s*\)\s*;[\s\S]{0,400}SaveGameValue\s*\(\s*25\s*,\s*1\s*\)\s*;",
                RegexOptions.IgnoreCase)) ready++;
            string burgundy1 = ReadOptional(gamePath,
                "Scripts/Burgundy1/bu1_objective_01.scr");
            if (Regex.IsMatch(burgundy1,
                @"(?m)^[ \t]*if\s*\(\s*_LoadGameValue\s*\(\s*53\s*\)\s*!=\s*1\s*\)[\s\S]{0,160}^[ \t]*SetObjectiveStatus\s*\(\s*3\s*,\s*0\s*\)",
                RegexOptions.IgnoreCase)) ready++;
            string burgundy3Objectives = ReadOptional(gamePath,
                "Scripts/Co_Burgundy3/bur3_objectives.scr");
            string burgundy3Prisoners = ReadOptional(gamePath,
                "Scripts/Co_Burgundy3/bur3_obj3.scr");
            if (burgundy3Objectives.IndexOf("SetObjectiveStatus(1, 0);",
                    StringComparison.OrdinalIgnoreCase) >= 0
                && Regex.Matches(burgundy3Objectives,
                    @"(?m)^[ \t]*SetObjectiveStatus\s*\(\s*1\s*,\s*1\s*\)\s*;",
                    RegexOptions.IgnoreCase).Count == 5
                && Regex.IsMatch(burgundy3Objectives,
                    @"OnSignal\s*\(\s*13\s*\)[\s\S]{0,120}vsetci\s*=\s*0",
                    RegexOptions.IgnoreCase)
                && burgundy3Prisoners.IndexOf("SendSignal(obj, 13);",
                    StringComparison.OrdinalIgnoreCase) >= 0
                && burgundy3Prisoners.IndexOf("Whenever obj3_failed ((!_ACTOR_GetState(zajatec01)) AND (!_ACTOR_GetState(zajatec02)) AND (!_ACTOR_GetState(zajatec03)) AND (!_ACTOR_GetState(zajatec04)))",
                    StringComparison.OrdinalIgnoreCase) >= 0) ready++;
            string czech2Objectives = ReadOptional(gamePath,
                "Scripts/CZECH2/R_Cz2_objectives.scr");
            if (Regex.IsMatch(czech2Objectives,
                    @"SetObjectiveStatus\s*\(\s*2\s*,\s*0\s*\)",
                    RegexOptions.IgnoreCase)
                && Regex.IsMatch(czech2Objectives,
                    @"OnSignal\s*\(\s*2\s*\)\s*\{[\s\S]{0,180}SetObjectiveStatus\s*\(\s*2\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase)) ready++;
            if (CoLibye2ObjectiveInstaller.IsActive(gamePath)) ready++;
            if (CoBrestGeneratorObjectiveInstaller.IsActive(gamePath)) ready++;
            if (CoBurgundy1StealthObjectiveInstaller.IsActive(gamePath)) ready++;
            return CountStatus(ready, 14);
        }

        private static string DetectDormantGuidance(string gamePath)
        {
            int ready = 0;
            string arctic = ReadOptional(gamePath, "Scripts/ARCTIC1/R_Arc1A_rebel.scr");
            if (Regex.IsMatch(arctic, @"SKIP_CSC3\s*=\s*0\s*;", RegexOptions.IgnoreCase)
                && Regex.IsMatch(arctic, @"SKIP_CSC4\s*=\s*0\s*;", RegexOptions.IgnoreCase))
                ready++;
            if (NormandyRouteInstaller.IsActive(gamePath)) ready++;
            if (BrestRouteInstaller.IsActive(gamePath)) ready++;
            if (CoBrestHintInstaller.IsActive(gamePath)) ready++;
            if (Czech4ZoneDoorInstaller.IsActive(gamePath)) ready++;
            if (Czech4AlternateApproachInstaller.IsActive(gamePath)) ready++;
            if (Czech2DoorGuardInstaller.IsActive(gamePath)) ready++;
            if (Czech2CarnageFreibergInstaller.IsActive(gamePath)) ready++;
            if (Czech2CutsceneSmokeInstaller.IsActive(gamePath)) ready++;
            if (Czech3DormantSequencesInstaller.IsTruckActive(gamePath)) ready++;
            if (Czech3DormantSequencesInstaller.IsMechanicActive(gamePath)) ready++;
            if (Czech3DormantSequencesInstaller.IsRadioOperatorActive(gamePath)) ready++;
            if (Czech4ObjectiveCounterInstaller.IsActive(gamePath)) ready++;
            if (PairedSignalTargetInstaller.IsActive(gamePath)) ready++;
            if (Africa4RadioConsequenceInstaller.IsActive(gamePath)) ready++;
            if (Africa5StorageActivationInstaller.IsActive(gamePath)) ready++;
            if (Africa5StorageAlarmInstaller.IsActive(gamePath)) ready++;
            if (Africa5GateSmokeInstaller.IsActive(gamePath)) ready++;
            if (Africa5SchumannAmbushInstaller.IsActive(gamePath)) ready++;
            if (Burgundy2PolishingInstaller.IsActive(gamePath)) ready++;
            if (Burgundy2DormantBehaviorInstaller.IsActive(gamePath)) ready++;
            if (Burgundy3Guard32PatrolInstaller.IsActive(gamePath)) ready++;
            if (Burgundy3SasDialogueInstaller.IsActive(gamePath)) ready++;
            if (Africa3WeaponInspectionInstaller.IsActive(gamePath)) ready++;
            if (Africa3MechanicCoverInstaller.IsActive(gamePath)) ready++;
            if (Africa3Guard24SittingInstaller.IsActive(gamePath)) ready++;
            if (Africa3Guard03HeatInstaller.IsActive(gamePath)) ready++;
            if (Africa3AlarmPatrolInstaller.IsActive(gamePath)) ready++;
            if (Africa3JeepSteamInstaller.IsActive(gamePath)) ready++;
            if (CoLibye1SmokingInstaller.IsActive(gamePath)) ready++;
            if (Arctic4DogPatrolInstaller.IsActive(gamePath)) ready++;
            if (Arctic4DocumentsMarkerInstaller.IsActive(gamePath)) ready++;
            if (Arctic4IceFallInstaller.IsActive(gamePath)) ready++;
            if (Czech5WeatherInstaller.IsActive(gamePath)) ready++;
            if (Alps2AlarmVoiceInstaller.IsActive(gamePath)) ready++;
            if (NorwayEnigmaLightmapInstaller.IsActive(gamePath)) ready++;
            if (Africa1AmbientRoutesInstaller.IsActive(gamePath)) ready++;
            if (Africa1CardPlayersInstaller.IsActive(gamePath)) ready++;
            if (Africa2GuardSignalInstaller.IsActive(gamePath)) ready++;
            if (Africa1CommandAlarmInstaller.IsActive(gamePath)) ready++;
            if (Alps1CivilAlarmInstaller.IsActive(gamePath)) ready++;
            if (Alps1CombatPostsInstaller.IsActive(gamePath)) ready++;
            if (Alps2ShotAlarmInstaller.IsActive(gamePath)) ready++;
            if (Burma2DormantScenesInstaller.IsActive(gamePath)) ready++;
            if (Africa3VehicleDiscoveryInstaller.IsActive(gamePath)) ready++;
            if (Arctic3CarHitInstaller.IsActive(gamePath)) ready++;
            if (Czech5OpelEffectInstaller.IsActive(gamePath)) ready++;
            if (Normandy2Red26Installer.IsActive(gamePath)) ready++;
            if (Normandy2BlueCounterfireInstaller.IsActive(gamePath)) ready++;
            if (Burgundy1GateInstaller.IsActive(gamePath)) ready++;
            if (Burgundy1CutsceneDialogueInstaller.IsActive(gamePath)) ready++;
            if (NorwayApproachInstaller.IsActive(gamePath)) ready++;
            if (NorwayTirpitzAmbienceInstaller.IsActive(gamePath)) ready++;
            if (NorwayGuardTimerInstaller.IsActive(gamePath)) ready++;
            if (Arctic1RadioButtonInstaller.IsActive(gamePath)) ready++;
            if (Arctic2RadioInstaller.IsActive(gamePath)) ready++;
            if (Arctic2DynamicLightInstaller.IsActive(gamePath)) ready++;
            if (Sicily1AlarmButtonInstaller.IsActive(gamePath)) ready++;
            if (CrossMissionScriptInstaller.IsActive(gamePath)) ready++;
            string africa3Dialogue = ReadOptional(
                gamePath, "Scripts/AFRICA3/AF3a_rozhovor_05.scr");
            if (Regex.IsMatch(africa3Dialogue,
                    @"FRM_MorphSpeechDelayed\s*\(\s*af02\s*,\s*07991601\s*,",
                    RegexOptions.IgnoreCase)
                && Regex.IsMatch(africa3Dialogue,
                    @"FRM_MorphSpeechDelayed\s*\(\s*af02\s*,\s*07991604\s*,",
                    RegexOptions.IgnoreCase)
                && africa3Dialogue.IndexOf(
                    "079915601", StringComparison.Ordinal) < 0
                && africa3Dialogue.IndexOf(
                    "079915604", StringComparison.Ordinal) < 0)
                ready++;
            return CountStatus(ready, 60);
        }

        private static string DetectEasterEggs(string gamePath)
        {
            int ready = 0;
            string africa1 = ReadOptional(gamePath, "Scripts/AFRICA1/AF1_ee.scr");
            if (Regex.IsMatch(africa1,
                @"mrtvi_panaci\s*=\s*1\s*;", RegexOptions.IgnoreCase)) ready++;
            string africa4 = ReadOptional(gamePath,
                "Scripts/AFRICA4/AF3b_ee_activator.scr");
            if (Regex.IsMatch(africa4,
                @"goto\s+ACTIVATED\s*;", RegexOptions.IgnoreCase)) ready++;
            return CountStatus(ready, 2);
        }

        private static string DetectExperimentalVestiges(string gamePath)
        {
            string list = ReadOptional(gamePath, "mpmaplist.txt");
            bool normandy = list.IndexOf("NORMANDY3_MP_ZONE",
                StringComparison.OrdinalIgnoreCase) >= 0
                && list.IndexOf(ExperimentalContentInstaller.NormandyPrototypeName,
                    StringComparison.OrdinalIgnoreCase) >= 0;
            bool africa = list.IndexOf("AFRIKA5_MP", StringComparison.OrdinalIgnoreCase) >= 0
                && list.IndexOf(ExperimentalContentInstaller.AfricaPrototypeName,
                    StringComparison.OrdinalIgnoreCase) >= 0;
            bool normandyFiles = ExperimentalContentInstaller.IsPrototypeInstalled(
                gamePath, true);
            bool africaFiles = ExperimentalContentInstaller.IsPrototypeInstalled(
                gamePath, false);
            int ready = (normandy && normandyFiles ? 1 : 0)
                + (africa && africaFiles ? 1 : 0);
            return CountStatus(ready, 2);
        }

        private static string DetectGuides(string gamePath)
        {
            int ready = 0;
            if (File.Exists(Path.Combine(gamePath, "Guides",
                "HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf"))) ready++;
            if (File.Exists(Path.Combine(gamePath, "Guides",
                "HD2-Rapport-des-Decouvertes.pdf"))) ready++;
            return CountStatus(ready, 2);
        }

        private static string ReadOptional(string gamePath, string relative)
        {
            string path = InstallerCore.SafeGameTarget(gamePath, relative);
            return File.Exists(path)
                ? Encoding.GetEncoding(1252).GetString(File.ReadAllBytes(path))
                : String.Empty;
        }

        private static string CountStatus(int ready, int total)
        {
            if (ready == total) return "deja actifs";
            if (ready == 0) return "a activer";
            return "partiellement actifs (" + ready + "/" + total + ")";
        }
    }
}
