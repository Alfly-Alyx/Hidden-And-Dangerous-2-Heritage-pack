using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class InstallerCore
    {
        private const string HostsStart = "# BEGIN HD2 Community MasterList";
        private const string HostsEnd = "# END HD2 Community MasterList";
        private static readonly object LogLock = new object();

        public static string DetectGamePath()
        {
            List<string> candidates = new List<string>();
            try
            {
                using (RegistryKey root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry32))
                using (RegistryKey key = root.OpenSubKey(@"SOFTWARE\GOG.com\Games\1576810170"))
                    if (key != null) candidates.Add(key.GetValue("PATH") as string);
            }
            catch { }
            try
            {
                using (RegistryKey root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry32))
                using (RegistryKey key = root.OpenSubKey(@"SOFTWARE\Illusion Softworks\Hidden & Dangerous 2"))
                    if (key != null)
                    {
                        candidates.Add(key.GetValue("InstallPath") as string);
                        candidates.Add(key.GetValue("InstallDir") as string);
                    }
            }
            catch { }
            candidates.Add(@"D:\Games\Hidden and Dangerous 2");
            foreach (string candidate in candidates)
                if (!String.IsNullOrWhiteSpace(candidate) && IsGamePath(candidate))
                    return Path.GetFullPath(candidate.Trim());
            return String.Empty;
        }

        public static bool IsGamePath(string path)
        {
            if (String.IsNullOrWhiteSpace(path)) return false;
            try
            {
                string full = Path.GetFullPath(path.Trim());
                return File.Exists(Path.Combine(full, "HD2_SabreSquadron.exe"))
                    && File.Exists(Path.Combine(full, "SabreSquadron.dta"))
                    && File.Exists(Path.Combine(full, "missions.dta"));
            }
            catch { return false; }
        }

        public static void ValidateGamePath(string path)
        {
            if (!IsGamePath(path))
                throw new InvalidOperationException(
                    "Le dossier ne contient pas une installation complete de Hidden & Dangerous 2: Sabre Squadron.");
        }

        public static string BuildDiagnostic(string gamePath)
        {
            if (String.IsNullOrWhiteSpace(gamePath)) gamePath = DetectGamePath();
            bool valid = IsGamePath(gamePath);
            StringBuilder text = new StringBuilder();
            text.AppendLine(AppConfig.ProductName + " - diagnostic");
            text.AppendLine("Date UTC : " + DateTime.UtcNow.ToString("u"));
            text.AppendLine();
            text.AppendLine("Jeu detecte : " + (valid ? "oui" : "non"));
            text.AppendLine("Dossier : " + (String.IsNullOrWhiteSpace(gamePath) ? "(introuvable)" : gamePath));
            if (valid)
            {
                try
                {
                    FileVersionInfo info = FileVersionInfo.GetVersionInfo(
                        Path.Combine(gamePath, "HD2_SabreSquadron.exe"));
                    text.AppendLine("Executable : " + info.FileVersion);
                }
                catch { text.AppendLine("Executable : version illisible"); }
            }
            text.AppendLine();
            text.AppendLine("Etat detecte des fonctions :");
            try { text.AppendLine("Serveurs Internet communautaires : " + DescribeHosts()); }
            catch (Exception ex) { text.AppendLine("Serveurs Internet communautaires : indetermine (" + ex.Message + ")"); }
            try { text.AppendLine("DirectPlay : " + (IsDirectPlayEnabled() ? "deja actif" : "a activer")); }
            catch (Exception ex) { text.AppendLine("DirectPlay : indetermine (" + ex.Message + ")"); }
            if (valid)
            {
                text.AppendLine("Correctif ecran large : " + WidescreenInstaller.DetectStatus(gamePath));
                text.AppendLine("Graphismes automatiques : " + GraphicsConfigurator.DetectStatus());
                text.AppendLine(FeatureStatusDetector.BuildReport(gamePath));
            }
            text.AppendLine("Serveur maitre TCP 28910 : "
                + (CanConnect(AppConfig.MasterIp, 28910, 3000) ? "joignable" : "non joignable"));
            text.AppendLine("Journal de restauration : "
                + (File.Exists(AppConfig.StateFile) ? "present" : "absent"));
            text.AppendLine();
            text.AppendLine("Audit officiel : 33 missions solo declarees sur 33 trouvees.");
            text.AppendLine("Vestiges : deux cartes PROTOTYPE d'exploration locale, sans objectifs, seront activees.");
            text.AppendLine("Exploration libre : disponible pour les cartes officielles et communautaires.");
            text.AppendLine("Objectifs repares : 14 ensembles, dont Arctic 2, Africa 5, la sortie Czech 2, les prisonniers Burgundy 3, les vehicules Libye 2, les generateurs Brest et la discretion Burgundy 1 cooperatif.");
            text.AppendLine("Easter eggs : sequences neutralisees d'Africa 1 et Africa 4 reactivables.");
            text.AppendLine("Vestiges narratifs : 2 sequences Arctic 1 et 2 identifiants de voix Africa 3 reparables.");
            text.AppendLine("Arctic 3 : les six occupants du camion reagissent de nouveau lorsqu'il est touche.");
            text.AppendLine("Czech 5 : l'OpelE_1 retrouve son effet officiel a la destruction.");
            text.AppendLine("Africa 5 : le mecanicien 04 du magasin reagit de nouveau avec son groupe.");
            text.AppendLine("Africa 5 : le garde 06 du magasin recherche de nouveau les alarmes exterieures.");
            text.AppendLine("Africa 5 : le garde d entree reprend sa cigarette apres avoir autorise le passage.");
            text.AppendLine("Africa 5 : Schumann rejoint sa position historique pendant l embuscade du tireur.");
            text.AppendLine("Africa 1 : les soldats 24 et 25 jouent de nouveau aux cartes dans le hangar.");
            text.AppendLine("Burgundy 2 : le polisseur reprend son animation apres le dialogue.");
            text.AppendLine("Burgundy 3 : le garde 32 retrouve sa ronde officielle entre deux points conserves.");
            text.AppendLine("Burgundy 3 : le premier SAS retrouve sa replique d'ouverture officielle.");
            text.AppendLine("Africa 3 : la ronde 08 inspecte de nouveau son arme aux deux temps prevus.");
            text.AppendLine("Africa 3 : le mecanicien 21 peut de nouveau se refugier sous l Opel lorsqu il est blesse.");
            text.AppendLine("Africa 3 : le garde 24 retrouve son repos assis et son retour apres alarme.");
            text.AppendLine("Africa 3 : le garde 03 retrouve son geste de chaleur pendant sa pause.");
            text.AppendLine("Africa 3 : la cinematique Jeep retrouve son sifflement de vapeur officiel.");
            text.AppendLine("Libye 1 cooperative : quatre gardes retrouvent leur animation de cigarette.");
            text.AppendLine("Arctic 4 : la patrouille 3 retrouve le mode marche retire pour le test avec son chien.");
            text.AppendLine("Arctic 4 : le marqueur historique des documents reapparait a proximite.");
            text.AppendLine("Arctic 4 : la chute de glace retrouve son impact historique.");
            text.AppendLine("Czech 5 : les scripts officiels de meteo et d'eclairs sont reactives.");
            text.AppendLine("Normandy 2 : le soldat Red 26 peut rejoindre la vague 7 comme prevu.");
            text.AppendLine("Normandy 2 : les quinze defenseurs Blue conservent leur riposte contre Ally 5.");
            text.AppendLine("Burgundy 1 : la barriere peut se refermer et son garde rejoint son poste apres le passage du camion.");
            text.AppendLine("Burgundy 1 : la cinematique finale retrouve une replique enregistree retiree.");
            text.AppendLine("Burgundy 2 : un garde reprend son cinquieme segment et le collaborateur marmonne de nouveau.");
            text.AppendLine("Norway : les deux zones d'approche peuvent de nouveau s'exclure mutuellement.");
            text.AppendLine("Norway : huit gardes presents du Tirpitz retrouvent leurs animations aleatoires.");
            text.AppendLine("Norway : le garde 3 interrompt de nouveau son minuteur de fausse alerte lorsqu'il est blesse.");
            text.AppendLine("Czech 4 : les trois soldats reagissent a la seconde approche de la place.");
            text.AppendLine("France : guidage original des acces souterrains de Lighthouse et seconde route de Brest reactivables.");
            text.AppendLine("London : l'arene London_mp est achevee sous le nom Poland; la campagne anglaise reste distincte.");
            text.AppendLine("Guides : le guide joueur et le rapport des decouvertes sont inclus.");
            text.AppendLine("Aucune cle de produit n'est lue, affichee ou modifiee.");
            return text.ToString();
        }

        public static void Install(InstallOptions options, Action<string> progress, Action<int> percent)
        {
            ValidateGamePath(options.GamePath);
            options.GamePath = Path.GetFullPath(options.GamePath);
            if (options.UnlockAllMissions)
                MissionUnlockInstaller.ValidateOnly(options.GamePath);
            if (options.AutoConfigureGraphics)
            {
                WidescreenInstaller.ValidateOnly();
                GraphicsConfigurator.ValidateOnly();
            }
            bool updating = File.Exists(AppConfig.StateFile);

            StateJournal journal = null;
            try
            {
                Log((updating ? "Mise a jour" : "Installation") + " dans " + options.GamePath);
                journal = updating
                    ? StateJournal.OpenExisting(options.GamePath)
                    : StateJournal.Create(options.GamePath);
                if (options.EnableDirectPlay)
                {
                    Report(progress, "Verification de DirectPlay...");
                    if (!IsDirectPlayEnabled())
                    {
                        SetDirectPlay(true);
                        journal.RecordDirectPlayEnabled();
                    }
                }
                SetPercent(percent, 5);
                if (options.ConfigureMasterServer)
                {
                    Report(progress, "Configuration de la liste des serveurs...");
                    ConfigureHosts(journal);
                }
                SetPercent(percent, 10);
                HashSet<string> prepared = new HashSet<string>(
                    StringComparer.OrdinalIgnoreCase);
                foreach (FileChange change in journal.State.Changes)
                    prepared.Add(change.RelativePath);
                GuideInstaller.Install(
                    options.GamePath, journal, prepared, progress);
                if (options.AutoConfigureGraphics)
                {
                    WidescreenInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                    GraphicsConfigurator.Apply(journal, progress);
                }
                ExperimentalContentInstaller.Install(
                    options.GamePath, journal, prepared, progress);
                if (options.FreeExploration)
                    OfficialContentInstaller.Install(
                        options.GamePath, journal, prepared, progress, percent);
                if (options.FreeExploration)
                    Arctic1FreeExplorationInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.InstallCmp)
                    CmpInstaller.Install(options, journal, prepared, progress, percent);
                if (options.FreeExploration)
                    OfficialContentInstaller.PatchLooseMissionTrees(
                        options.GamePath, journal, prepared, progress);
                if (options.FixOptionalObjectives)
                    ObjectiveFixInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.FixOptionalObjectives)
                    CoLibye2ObjectiveInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.FixOptionalObjectives)
                    CoBrestGeneratorObjectiveInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.FixOptionalObjectives)
                    CoBurgundy1StealthObjectiveInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreOfficialEasterEggs)
                    OfficialEasterEggInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    NormandyRouteInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    BrestRouteInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Alps1CivilAlarmInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Alps1CombatPostsInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Alps2ShotAlarmInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Burma2DormantScenesInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    CoBrestHintInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3VehicleDiscoveryInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Arctic3CarHitInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech5OpelEffectInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Normandy2Red26Installer.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Normandy2BlueCounterfireInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Burgundy1GateInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Burgundy1CutsceneDialogueInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    NorwayApproachInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    NorwayTirpitzAmbienceInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    NorwayGuardTimerInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech4ZoneDoorInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech4AlternateApproachInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech2DoorGuardInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech2CarnageFreibergInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech2CutsceneSmokeInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech3DormantSequencesInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech4ObjectiveCounterInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    PairedSignalTargetInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa4RadioConsequenceInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa4DormantInfantryInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa5StorageActivationInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa5StorageAlarmInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa5GateSmokeInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa5SchumannAmbushInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa5DormantActorsInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Burgundy2PolishingInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Burgundy2DormantBehaviorInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Burgundy3Guard32PatrolInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Burgundy3SasDialogueInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Libye2CutDialogueInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Libye3DetailedRouteInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    BrestDormantGuardActionsInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3WeaponInspectionInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3MechanicCoverInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3Guard24SittingInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3Guard03HeatInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3AlarmPatrolInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3DormantSentryInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa3JeepSteamInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    CoLibye1SmokingInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Arctic4DogPatrolInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Arctic4DocumentsMarkerInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Arctic4IceFallInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Czech5WeatherInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Alps2AlarmVoiceInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    NorwayEnigmaLightmapInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa1AmbientRoutesInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa1CardPlayersInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa2GuardSignalInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa1CommandAlarmInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Africa1DormantInteractionsInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Arctic1RadioButtonInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Arctic2RadioInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Arctic2DynamicLightInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    Sicily1AlarmButtonInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    CoSicily2GunSoundInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    CrossMissionScriptInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.RestoreDormantSequences)
                    DormantContentInstaller.Install(
                        options.GamePath, journal, prepared, progress);
                if (options.UnlockAllMissions)
                    MissionUnlockInstaller.Install(options.GamePath, journal, progress);
                SetPercent(percent, 100);
                Report(progress, "Installation terminee. La restauration reste disponible.");
            }
            catch (Exception original)
            {
                Log("Echec : " + original);
                if (journal != null)
                {
                    journal.Dispose();
                    journal = null;
                    if (updating)
                        throw new InvalidOperationException(
                            "Echec de la mise a jour; le journal et l'installation existante "
                            + "ont ete conserves. " + original.Message, original);
                    try
                    {
                        Uninstall(progress);
                        throw new InvalidOperationException(
                            "Echec de l'installation; tous les changements ont ete restaures. "
                            + original.Message, original);
                    }
                    catch (InvalidOperationException rollback)
                    {
                        if (rollback.InnerException == original) throw;
                        throw new InvalidOperationException(
                            "Echec de l'installation et de la restauration automatique. "
                            + "Le journal est conserve. Erreur: " + original.Message
                            + " / restauration: " + rollback.Message, original);
                    }
                    catch (Exception rollback)
                    {
                        throw new InvalidOperationException(
                            "Echec de l'installation et de la restauration automatique. "
                            + "Le journal est conserve. Erreur: " + original.Message
                            + " / restauration: " + rollback.Message, original);
                    }
                }
                throw;
            }
            finally { if (journal != null) journal.Dispose(); }
        }

        public static void Uninstall(Action<string> progress)
        {
            InstallState state = InstallState.Load();
            if (state == null)
                throw new InvalidOperationException("Aucun journal de restauration n'a ete trouve.");
            ValidateStatePaths(state);
            Report(progress, "Verification des fichiers avant restauration...");
            List<string> conflicts = FindModifiedFiles(state);
            if (conflicts.Count > 0)
            {
                StringBuilder message = new StringBuilder(
                    "Restauration suspendue: des fichiers ont ete modifies depuis l'installation.\r\n");
                for (int i = 0; i < Math.Min(8, conflicts.Count); i++)
                    message.AppendLine(" - " + conflicts[i]);
                if (conflicts.Count > 8)
                    message.AppendLine(" - ... et " + (conflicts.Count - 8) + " autres");
                message.AppendLine("Le journal et les sauvegardes sont conserves.");
                throw new InvalidOperationException(message.ToString());
            }
            GraphicsConfigurator.Restore(state, progress);
            for (int index = state.ProfileUnlocks.Count - 1; index >= 0; index--)
                MissionUnlockInstaller.Restore(
                    state.GamePath, state.ProfileUnlocks[index], progress);
            if (state.DirectPlayEnabledByInstaller)
            {
                Report(progress, "Restauration de l'etat DirectPlay...");
                SetDirectPlay(false);
            }
            if (state.HostsChanged)
            {
                Report(progress, "Retrait du bloc masterlist...");
                RemoveHostsBlock();
            }
            Report(progress, "Restauration des fichiers du jeu...");
            for (int i = state.Changes.Count - 1; i >= 0; i--)
            {
                FileChange change = state.Changes[i];
                string target = SafeGameTarget(state.GamePath, change.RelativePath);
                if (change.WasCreated)
                {
                    if (File.Exists(target)) File.Delete(target);
                }
                else
                {
                    string backup = SafeBackupTarget(state.BackupRoot, change.RelativePath);
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    File.Copy(backup, target, true);
                }
                RemoveEmptyParents(Path.GetDirectoryName(target), state.GamePath);
            }
            string data = Path.GetFullPath(AppConfig.DataRoot)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            string parent = Path.GetFullPath(
                Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData))
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            if (!data.StartsWith(parent + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)
                || String.Equals(data, parent, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Chemin de donnees de restauration non sur.");
            Directory.Delete(data, true);
            if (progress != null) progress("Restauration terminee.");
        }

        internal static void PrepareTarget(
            string gamePath, string relative, string target,
            StateJournal journal, HashSet<string> prepared)
        {
            relative = relative.Replace('/', Path.DirectorySeparatorChar);
            if (!prepared.Add(relative))
                return;
            if (File.Exists(target))
            {
                string backup = SafeBackupTarget(journal.State.BackupRoot, relative);
                Directory.CreateDirectory(Path.GetDirectoryName(backup));
                File.Copy(target, backup, false);
                journal.RecordReplacement(relative);
            }
            else journal.RecordCreated(relative);
        }

        internal static string SafeGameTarget(string gamePath, string relative)
        {
            if (String.IsNullOrWhiteSpace(relative) || Path.IsPathRooted(relative)
                || relative.IndexOf(':') >= 0)
                throw new InvalidDataException("Chemin relatif non sur : " + relative);
            string root = Path.GetFullPath(gamePath)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            string target = Path.GetFullPath(
                Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
            if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Chemin hors du jeu : " + relative);
            return target;
        }

        internal static string SafeBackupTarget(string backupRoot, string relative)
        {
            string root = Path.GetFullPath(Path.Combine(backupRoot, "files"))
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            string target = Path.GetFullPath(
                Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
            if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Chemin hors sauvegarde : " + relative);
            return target;
        }

        private static List<string> FindModifiedFiles(InstallState state)
        {
            List<string> conflicts = new List<string>();
            foreach (FileChange change in state.Changes)
            {
                string target = SafeGameTarget(state.GamePath, change.RelativePath);
                if (!change.WasCreated
                    && !File.Exists(SafeBackupTarget(state.BackupRoot, change.RelativePath)))
                {
                    conflicts.Add(change.RelativePath + " (sauvegarde absente)");
                    continue;
                }
                if (File.Exists(target) && !String.IsNullOrWhiteSpace(change.InstalledSha256)
                    && !String.Equals(
                        CmpInstaller.ComputeSha256(target), change.InstalledSha256,
                        StringComparison.OrdinalIgnoreCase))
                    conflicts.Add(change.RelativePath + " (modifie)");
            }
            if (GraphicsConfigurator.HasRestoreConflict(state))
                conflicts.Add("Registre LS3D_setup (modifie)");
            return conflicts;
        }

        private static void ValidateStatePaths(InstallState state)
        {
            ValidateGamePath(state.GamePath);
            string root = Path.GetFullPath(AppConfig.DataRoot)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            if (!Path.GetFullPath(state.BackupRoot).StartsWith(root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Le dossier de sauvegarde sort de l'espace gere.");
        }

        private static void ConfigureHosts(StateJournal journal)
        {
            string path = HostsPath();
            string content = File.ReadAllText(path, Encoding.Default);
            bool marker = content.IndexOf(HostsStart, StringComparison.OrdinalIgnoreCase) >= 0
                || content.IndexOf(HostsEnd, StringComparison.OrdinalIgnoreCase) >= 0;
            int exact = 0;
            List<string> conflicts = new List<string>();
            foreach (string raw in Regex.Split(content, "\r\n|\n|\r"))
            {
                string line = raw.Trim();
                if (line.Length == 0 || line.StartsWith("#")) continue;
                string[] fields = Regex.Split(line.Split('#')[0].Trim(), @"\s+");
                if (fields.Length < 2) continue;
                foreach (string alias in AppConfig.MasterAliases)
                    for (int i = 1; i < fields.Length; i++)
                        if (String.Equals(fields[i], alias, StringComparison.OrdinalIgnoreCase))
                        {
                            if (String.Equals(fields[0], AppConfig.MasterIp, StringComparison.OrdinalIgnoreCase))
                                exact++;
                            else conflicts.Add(alias + " -> " + fields[0]);
                        }
            }
            if (conflicts.Count > 0)
                throw new InvalidOperationException(
                    "Le fichier hosts contient une adresse differente pour : " + String.Join(", ", conflicts));
            if (marker)
            {
                if (exact >= AppConfig.MasterAliases.Length) return;
                throw new InvalidOperationException("Un bloc HD2 Community MasterList incomplet existe deja.");
            }
            if (exact >= AppConfig.MasterAliases.Length) return;
            if (exact > 0)
                throw new InvalidOperationException("La configuration HD2 du fichier hosts est partielle.");

            string newline = content.Contains("\r\n") ? "\r\n" : Environment.NewLine;
            StringBuilder block = new StringBuilder();
            if (content.Length > 0 && !content.EndsWith("\n") && !content.EndsWith("\r"))
                block.Append(newline);
            block.Append(HostsStart).Append(newline);
            foreach (string alias in AppConfig.MasterAliases)
                block.Append(AppConfig.MasterIp).Append(" ").Append(alias).Append(newline);
            block.Append(HostsEnd).Append(newline);
            journal.RecordHostsChanged();
            File.AppendAllText(path, block.ToString(), Encoding.Default);
        }

        private static void RemoveHostsBlock()
        {
            string path = HostsPath();
            string content = File.ReadAllText(path, Encoding.Default);
            string pattern = @"(?ims)^[ \t]*\# BEGIN HD2 Community MasterList[ \t]*\r?\n.*?"
                + @"^[ \t]*\# END HD2 Community MasterList[ \t]*(?:\r?\n)?";
            File.WriteAllText(path, Regex.Replace(content, pattern, String.Empty), Encoding.Default);
        }

        private static string DescribeHosts()
        {
            string content = File.ReadAllText(HostsPath(), Encoding.Default);
            int found = 0;
            foreach (string alias in AppConfig.MasterAliases)
                if (Regex.IsMatch(content, @"(?im)^[ \t]*" + Regex.Escape(AppConfig.MasterIp)
                    + @"[ \t]+" + Regex.Escape(alias) + @"(?:[ \t]|$)")) found++;
            if (found == AppConfig.MasterAliases.Length) return "configuree";
            if (found == 0) return "non configuree";
            return "partielle (" + found + "/" + AppConfig.MasterAliases.Length + ")";
        }

        private static string HostsPath()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),
                "drivers", "etc", "hosts");
        }

        private static bool IsDirectPlayEnabled()
        {
            string script = "$f=Get-WindowsOptionalFeature -Online -FeatureName DirectPlay;"
                + "if($f.State -eq 'Enabled'){'Enabled'}else{'Disabled'}";
            ProcessResult result = RunProcess(PowerShellPath(),
                "-NoProfile -NonInteractive -Command \"" + script + "\"");
            if (result.ExitCode != 0)
                throw new InvalidOperationException("Impossible de lire l'etat de DirectPlay.");
            return result.Output.IndexOf("Enabled", StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private static void SetDirectPlay(bool enable)
        {
            string arguments = "/online /" + (enable ? "Enable-Feature" : "Disable-Feature")
                + " /FeatureName:DirectPlay /NoRestart" + (enable ? " /All" : "");
            ProcessResult result = RunProcess(
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "dism.exe"),
                arguments);
            if (result.ExitCode != 0 && result.ExitCode != 3010)
                throw new InvalidOperationException("DISM a echoue (code " + result.ExitCode + ").");
        }

        private static string PowerShellPath()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),
                @"WindowsPowerShell\v1.0\powershell.exe");
        }

        private static ProcessResult RunProcess(string file, string arguments)
        {
            ProcessStartInfo start = new ProcessStartInfo {
                FileName = file, Arguments = arguments, UseShellExecute = false,
                CreateNoWindow = true, RedirectStandardOutput = true,
                RedirectStandardError = true, WindowStyle = ProcessWindowStyle.Hidden
            };
            using (Process process = Process.Start(start))
            {
                string output = process.StandardOutput.ReadToEnd();
                string error = process.StandardError.ReadToEnd();
                process.WaitForExit();
                return new ProcessResult {
                    ExitCode = process.ExitCode,
                    Output = output + Environment.NewLine + error
                };
            }
        }

        private static bool CanConnect(string host, int port, int timeout)
        {
            using (TcpClient client = new TcpClient())
                try
                {
                    IAsyncResult result = client.BeginConnect(host, port, null, null);
                    if (!result.AsyncWaitHandle.WaitOne(timeout)) return false;
                    client.EndConnect(result);
                    return true;
                }
                catch { return false; }
        }

        private static void RemoveEmptyParents(string directory, string stop)
        {
            string root = Path.GetFullPath(stop).TrimEnd(Path.DirectorySeparatorChar);
            while (!String.IsNullOrWhiteSpace(directory)
                && !String.Equals(Path.GetFullPath(directory).TrimEnd(Path.DirectorySeparatorChar),
                    root, StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    if (Directory.Exists(directory)
                        && Directory.GetFileSystemEntries(directory).Length == 0)
                        Directory.Delete(directory, false);
                    else break;
                }
                catch { break; }
                directory = Path.GetDirectoryName(directory);
            }
        }

        internal static void Report(Action<string> action, string message)
        {
            Log(message);
            if (action != null) action(message);
        }

        internal static void SetPercent(Action<int> action, int value)
        {
            if (action != null) action(Math.Max(0, Math.Min(100, value)));
        }

        internal static void Log(string message)
        {
            lock (LogLock)
            {
                Directory.CreateDirectory(AppConfig.DataRoot);
                File.AppendAllText(AppConfig.LogFile,
                    DateTime.UtcNow.ToString("u") + " " + message + Environment.NewLine,
                    Encoding.UTF8);
            }
        }

        private sealed class ProcessResult
        {
            public int ExitCode;
            public string Output;
        }
    }
}

