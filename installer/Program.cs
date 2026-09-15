using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace HD2CommunityInstaller
{
    internal static class Program
    {
        [DllImport("kernel32.dll")]
        private static extern bool AttachConsole(int processId);

        [STAThread]
        private static int Main(string[] args)
        {
            if (args.Length > 0)
            {
                AttachConsole(-1);
                try
                {
                    string command = args[0].ToLowerInvariant();
                    string game = args.Length > 1 ? args[1] : InstallerCore.DetectGamePath();
                    if (command == "--check")
                    {
                        Console.WriteLine(InstallerCore.BuildDiagnostic(game));
                        return InstallerCore.IsGamePath(game) ? 0 : 2;
                    }
                    if (command == "--self-test-local")
                    {
                        Console.WriteLine(WidescreenInstaller.ValidateOnly());
                        Console.WriteLine(GraphicsConfigurator.ValidateOnly());
                        Console.WriteLine(ExperimentalContentInstaller.ValidateOnly(game));
                        Console.WriteLine(OfficialContentInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic1FreeExplorationInstaller.ValidateOnly(game));
                        Console.WriteLine(ObjectiveFixInstaller.ValidateOnly(game));
                        Console.WriteLine(CoLibye2ObjectiveInstaller.ValidateOnly(game));
                        Console.WriteLine(CoBrestGeneratorObjectiveInstaller.ValidateOnly(game));
                        Console.WriteLine(CoBurgundy1StealthObjectiveInstaller.ValidateOnly(game));
                        Console.WriteLine(OfficialEasterEggInstaller.ValidateOnly(game));
                        Console.WriteLine(GuideInstaller.ValidateOnly());
                        Console.WriteLine(DormantContentInstaller.ValidateOnly(game));
                        Console.WriteLine(NormandyRouteInstaller.ValidateOnly(game));
                        Console.WriteLine(BrestRouteInstaller.ValidateOnly(game));
                        Console.WriteLine(CoBrestHintInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech4ZoneDoorInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech4AlternateApproachInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech2DoorGuardInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech2CarnageFreibergInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech2CutsceneSmokeInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech3DormantSequencesInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech4ObjectiveCounterInstaller.ValidateOnly(game));
                        Console.WriteLine(PairedSignalTargetInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa4RadioConsequenceInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa4DormantInfantryInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5StorageActivationInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5StorageAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5GateSmokeInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5SchumannAmbushInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5DormantActorsInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy2PolishingInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy2DormantBehaviorInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy3Guard32PatrolInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy3SasDialogueInstaller.ValidateOnly(game));
                        Console.WriteLine(Libye2CutDialogueInstaller.ValidateOnly(game));
                        Console.WriteLine(Libye3DetailedRouteInstaller.ValidateOnly(game));
                        Console.WriteLine(BrestDormantGuardActionsInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3WeaponInspectionInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3MechanicCoverInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3Guard24SittingInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3Guard03HeatInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3AlarmPatrolInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3DormantSentryInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3JeepSteamInstaller.ValidateOnly(game));
                        Console.WriteLine(CoLibye1SmokingInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic4DogPatrolInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic4DocumentsMarkerInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic4IceFallInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech5WeatherInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps2AlarmVoiceInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayEnigmaLightmapInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1AmbientRoutesInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1CardPlayersInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa2GuardSignalInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1CommandAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1DormantInteractionsInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps1CivilAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps1CombatPostsInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps2ShotAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Burma2DormantScenesInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3VehicleDiscoveryInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic3CarHitInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech5OpelEffectInstaller.ValidateOnly(game));
                        Console.WriteLine(Normandy2Red26Installer.ValidateOnly(game));
                        Console.WriteLine(Normandy2BlueCounterfireInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy1GateInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy1CutsceneDialogueInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayApproachInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayTirpitzAmbienceInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayGuardTimerInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic1RadioButtonInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic2RadioInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic2DynamicLightInstaller.ValidateOnly(game));
                        Console.WriteLine(Sicily1AlarmButtonInstaller.ValidateOnly(game));
                        Console.WriteLine(CrossMissionScriptInstaller.ValidateOnly(game));
                        Console.WriteLine(MissionUnlockInstaller.ValidateOnly(game));
                        return 0;
                    }
                    if (command == "--self-test")
                    {
                        if (args.Length < 3)
                            throw new ArgumentException("--self-test exige le dossier du jeu et l'archive CMP.");
                        Console.WriteLine(CmpInstaller.ValidateOnly(args[2], game));
                        Console.WriteLine(WidescreenInstaller.ValidateOnly());
                        Console.WriteLine(GraphicsConfigurator.ValidateOnly());
                        Console.WriteLine(ExperimentalContentInstaller.ValidateOnly(game));
                        Console.WriteLine(OfficialContentInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic1FreeExplorationInstaller.ValidateOnly(game));
                        Console.WriteLine(ObjectiveFixInstaller.ValidateOnly(game));
                        Console.WriteLine(CoLibye2ObjectiveInstaller.ValidateOnly(game));
                        Console.WriteLine(CoBrestGeneratorObjectiveInstaller.ValidateOnly(game));
                        Console.WriteLine(CoBurgundy1StealthObjectiveInstaller.ValidateOnly(game));
                        Console.WriteLine(OfficialEasterEggInstaller.ValidateOnly(game));
                        Console.WriteLine(GuideInstaller.ValidateOnly());
                        Console.WriteLine(DormantContentInstaller.ValidateOnly(game));
                        Console.WriteLine(NormandyRouteInstaller.ValidateOnly(game));
                        Console.WriteLine(BrestRouteInstaller.ValidateOnly(game));
                        Console.WriteLine(CoBrestHintInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech4ZoneDoorInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech4AlternateApproachInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech2DoorGuardInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech2CarnageFreibergInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech2CutsceneSmokeInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech3DormantSequencesInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech4ObjectiveCounterInstaller.ValidateOnly(game));
                        Console.WriteLine(PairedSignalTargetInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa4RadioConsequenceInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa4DormantInfantryInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5StorageActivationInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5StorageAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5GateSmokeInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5SchumannAmbushInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa5DormantActorsInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy2PolishingInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy2DormantBehaviorInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy3Guard32PatrolInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy3SasDialogueInstaller.ValidateOnly(game));
                        Console.WriteLine(Libye2CutDialogueInstaller.ValidateOnly(game));
                        Console.WriteLine(Libye3DetailedRouteInstaller.ValidateOnly(game));
                        Console.WriteLine(BrestDormantGuardActionsInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3WeaponInspectionInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3MechanicCoverInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3Guard24SittingInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3Guard03HeatInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3AlarmPatrolInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3DormantSentryInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3JeepSteamInstaller.ValidateOnly(game));
                        Console.WriteLine(CoLibye1SmokingInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic4DogPatrolInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic4DocumentsMarkerInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic4IceFallInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech5WeatherInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps2AlarmVoiceInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayEnigmaLightmapInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1AmbientRoutesInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1CardPlayersInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa2GuardSignalInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1CommandAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa1DormantInteractionsInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps1CivilAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps1CombatPostsInstaller.ValidateOnly(game));
                        Console.WriteLine(Alps2ShotAlarmInstaller.ValidateOnly(game));
                        Console.WriteLine(Burma2DormantScenesInstaller.ValidateOnly(game));
                        Console.WriteLine(Africa3VehicleDiscoveryInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic3CarHitInstaller.ValidateOnly(game));
                        Console.WriteLine(Czech5OpelEffectInstaller.ValidateOnly(game));
                        Console.WriteLine(Normandy2Red26Installer.ValidateOnly(game));
                        Console.WriteLine(Normandy2BlueCounterfireInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy1GateInstaller.ValidateOnly(game));
                        Console.WriteLine(Burgundy1CutsceneDialogueInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayApproachInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayTirpitzAmbienceInstaller.ValidateOnly(game));
                        Console.WriteLine(NorwayGuardTimerInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic1RadioButtonInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic2RadioInstaller.ValidateOnly(game));
                        Console.WriteLine(Arctic2DynamicLightInstaller.ValidateOnly(game));
                        Console.WriteLine(Sicily1AlarmButtonInstaller.ValidateOnly(game));
                        Console.WriteLine(CrossMissionScriptInstaller.ValidateOnly(game));
                        Console.WriteLine(MissionUnlockInstaller.ValidateOnly(game));
                        return 0;
                    }
                    if (command == "--install")
                    {
                        InstallOptions options = new InstallOptions { GamePath = game };
                        if (args.Length > 2) options.PackageOverride = args[2];
                        InstallerCore.Install(options, Console.WriteLine, null);
                        return 0;
                    }
                    if (command == "--uninstall")
                    {
                        InstallerCore.Uninstall(Console.WriteLine);
                        return 0;
                    }
                    throw new ArgumentException("Commande inconnue : " + args[0]);
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine(ex);
                    return 1;
                }
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
            return 0;
        }
    }
}
