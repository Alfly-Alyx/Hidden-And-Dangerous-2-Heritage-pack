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
            int ready = ObjectiveFixInstaller.CountActiveObjectives(gamePath);
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
            if (Africa4DormantInfantryInstaller.IsActive(gamePath)) ready++;
            if (Africa5StorageActivationInstaller.IsActive(gamePath)) ready++;
            if (Africa5StorageAlarmInstaller.IsActive(gamePath)) ready++;
            if (Africa5GateSmokeInstaller.IsActive(gamePath)) ready++;
            if (Africa5SchumannAmbushInstaller.IsActive(gamePath)) ready++;
            if (Africa5DormantActorsInstaller.IsActive(gamePath)) ready++;
            if (Burgundy2PolishingInstaller.IsActive(gamePath)) ready++;
            if (Burgundy2DormantBehaviorInstaller.IsActive(gamePath)) ready++;
            if (Burgundy3Guard32PatrolInstaller.IsActive(gamePath)) ready++;
            if (Burgundy3SasDialogueInstaller.IsActive(gamePath)) ready++;
            if (Libye2CutDialogueInstaller.IsActive(gamePath)) ready++;
            if (Libye3DetailedRouteInstaller.IsActive(gamePath)) ready++;
            if (BrestDormantGuardActionsInstaller.IsActive(gamePath)) ready++;
            if (Africa3WeaponInspectionInstaller.IsActive(gamePath)) ready++;
            if (Africa3MechanicCoverInstaller.IsActive(gamePath)) ready++;
            if (Africa3Guard24SittingInstaller.IsActive(gamePath)) ready++;
            if (Africa3Guard03HeatInstaller.IsActive(gamePath)) ready++;
            if (Africa3AlarmPatrolInstaller.IsActive(gamePath)) ready++;
            if (Africa3DormantSentryInstaller.IsActive(gamePath)) ready++;
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
            if (Africa1DormantInteractionsInstaller.IsActive(gamePath)) ready++;
            if (Alps1CivilAlarmInstaller.IsActive(gamePath)) ready++;
            if (Alps1CombatPostsInstaller.IsActive(gamePath)) ready++;
            if (Alps2ShotAlarmInstaller.IsActive(gamePath)) ready++;
            if (Burma2DormantScenesInstaller.IsActive(gamePath)) ready++;
            if (Burma2RandomRadioInstaller.IsActive(gamePath)) ready++;
            if (Africa3VehicleDiscoveryInstaller.IsActive(gamePath)) ready++;
            if (Arctic3CarHitInstaller.IsActive(gamePath)) ready++;
            if (Czech5OpelEffectInstaller.IsActive(gamePath)) ready++;
            if (Normandy2Red26Installer.IsActive(gamePath)) ready++;
            if (Normandy2BlueCounterfireInstaller.IsActive(gamePath)) ready++;
            if (NormandyMpLighthouseToggleInstaller.IsActive(gamePath)) ready++;
            if (Burgundy1GateInstaller.IsActive(gamePath)) ready++;
            if (Burgundy1CutsceneDialogueInstaller.IsActive(gamePath)) ready++;
            if (NorwayApproachInstaller.IsActive(gamePath)) ready++;
            if (NorwayTirpitzAmbienceInstaller.IsActive(gamePath)) ready++;
            if (NorwayGuardTimerInstaller.IsActive(gamePath)) ready++;
            if (Arctic1RadioButtonInstaller.IsActive(gamePath)) ready++;
            if (Arctic1TransformerLightsInstaller.IsActive(gamePath)) ready++;
            if (Arctic2RadioInstaller.IsActive(gamePath)) ready++;
            if (Arctic2DynamicLightInstaller.IsActive(gamePath)) ready++;
            if (Sicily1AlarmButtonInstaller.IsActive(gamePath)) ready++;
            if (CoSicily2GunSoundInstaller.IsActive(gamePath)) ready++;
            if (CoLibye3DormantDetailsInstaller.IsActive(gamePath)) ready++;
            if (CoLibye1DormantDialoguesInstaller.IsActive(gamePath)) ready++;
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
            return CountStatus(ready, 73);
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
            if (File.Exists(Path.Combine(gamePath, "Guides",
                "HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf"))) ready++;
            if (File.Exists(Path.Combine(gamePath, "Guides",
                "HD2-Discovery-Report-EN.pdf"))) ready++;
            return CountStatus(ready, 4);
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
