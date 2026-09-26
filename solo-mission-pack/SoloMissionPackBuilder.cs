using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using HD2CommunityInstaller;

namespace HD2CustomMissionManager
{
    internal sealed class SoloMissionSpec
    {
        public string Id;
        public string PackageFolder;
        public string SourceMission;
        public string TargetMission;
        public string TemplateMission;
        public string DefaultTitle;
        public string FrenchTitle;
        public int[] ObjectiveTextIds;
        public string SpawnSourceMission;
        public string[] SpawnActors;
        public string SpawnPositionActor;
        public string[] ExtraSoloScripts;
    }

    internal sealed class ArchivedFile
    {
        public string Relative;
        public byte[] Data;
    }

    internal sealed class SourceArchiveEntry
    {
        public string Name;
        public long Size;
        public string Sha256;
        public string OriginalPath;
        public bool OriginallyMissing;
    }

    internal sealed class SourceArchiveRepair : IDisposable
    {
        private readonly string Root;
        private readonly string Game;
        private readonly List<SourceArchiveEntry> Replaced;
        private bool Finished;

        public SourceArchiveRepair(
            string root, string game, List<SourceArchiveEntry> replaced)
        {
            Root = root;
            Game = game;
            Replaced = replaced;
        }

        public void Commit()
        {
            if (Finished) return;
            bool hasOriginals = Replaced.Any(entry =>
                !entry.OriginallyMissing && File.Exists(entry.OriginalPath));
            if (hasOriginals)
            {
                string backupParent = Path.Combine(
                    Game, "STATIC_MENU_BACKUP", "SourceArchives");
                Directory.CreateDirectory(backupParent);
                string backupRoot = Path.Combine(backupParent, Path.GetFileName(Root));
                File.WriteAllText(Path.Combine(Root, "README.txt"),
                    "Copies remplacées par le pack personnel de missions solo.",
                    new UTF8Encoding(false));
                Directory.Move(Root, backupRoot);
            }
            Finished = true;
            Cleanup();
        }

        public void RollBack()
        {
            if (Finished) return;
            foreach (SourceArchiveEntry entry in Replaced.AsEnumerable().Reverse())
            {
                string target = Path.Combine(Game, entry.Name);
                if (File.Exists(target)) File.Delete(target);
                if (!entry.OriginallyMissing && File.Exists(entry.OriginalPath))
                    File.Move(entry.OriginalPath, target);
            }
            Finished = true;
            Cleanup();
        }

        private void Cleanup()
        {
            if (Directory.Exists(Root)) Directory.Delete(Root, true);
        }

        public void Dispose()
        {
            if (!Finished) RollBack();
        }
    }

    internal static class SoloMissionPackBuilder
    {
        private const string Category = "multiplayer-adaptation";
        private const string EmbeddedPayloadResource =
            "HD2SoloMissionPack.SoloMissionPayload.zip";
        private const string EmbeddedSourceArchivesResource =
            "HD2SoloMissionPack.SourceArchives.zip";
        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };
        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };
        private static readonly string[] SourceArchives = {
            "missions.dta", "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };
        private static readonly string[] Languages = {
            "czech", "english", "EnglishUS", "french", "german",
            "italian", "japan", "spanish"
        };
        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer {
            MaxJsonLength = 16 * 1024 * 1024
        };

        private static readonly SoloMissionSpec[] Specs = {
            new SoloMissionSpec {
                Id = "heritage.solo.alps3-objective",
                PackageFolder = "Heritage Solo - Alps3 Objectif",
                SourceMission = "Alps3_obj", TargetMission = "HP_Solo_Alps3_Obj",
                TemplateMission = "Alps2",
                DefaultTitle = "SOLO ADAPTATION - ALPS 3",
                FrenchTitle = "ADAPTATION SOLO - ALPES 3",
                ObjectiveTextIds = new[] { 15011, 15010, 15002 },
                SpawnSourceMission = "Alps2",
                SpawnActors = new[] { "Spawnpoint01" },
                SpawnPositionActor = "zone1"
            },
            new SoloMissionSpec {
                Id = "heritage.solo.ardennes1-objective",
                PackageFolder = "Heritage Solo - Ardennes1 Objectif",
                SourceMission = "Ardens1_obj", TargetMission = "HP_Solo_Ardens1_Obj",
                TemplateMission = "Alps2",
                DefaultTitle = "SOLO ADAPTATION - ARDENNES 1",
                FrenchTitle = "ADAPTATION SOLO - ARDENNES 1",
                ObjectiveTextIds = new[] { 15020, 15021, 15022 },
                SpawnSourceMission = "Alps2",
                SpawnActors = new[] { "Spawnpoint01" },
                SpawnPositionActor = "zone1"
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-brest",
                PackageFolder = "Heritage Solo - Coop Brest",
                SourceMission = "Co_Brest", TargetMission = "HP_Solo_Co_Brest",
                TemplateMission = "Brest",
                DefaultTitle = "SOLO ADAPTATION - BREST CO-OP",
                FrenchTitle = "ADAPTATION SOLO - BREST COOP",
                ObjectiveTextIds = new[] { 15500, 15506, 15503, 15501 },
                SpawnSourceMission = "Brest",
                SpawnActors = new[] { "spawn_", "spawn_2", "spawn_3" }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-burgundy1",
                PackageFolder = "Heritage Solo - Coop Burgundy1",
                SourceMission = "Co_Burgundy1", TargetMission = "HP_Solo_Co_Burgundy1",
                TemplateMission = "Burgundy1",
                DefaultTitle = "SOLO ADAPTATION - BURGUNDY 1 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - BOURGOGNE 1 COOP",
                ObjectiveTextIds = new[] { 15560, 15561, 15562, 15563 },
                SpawnSourceMission = "Burgundy1",
                SpawnActors = new[] { "spawn01", "spawn02", "spawn03", "spawn04" }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-burgundy2",
                PackageFolder = "Heritage Solo - Coop Burgundy2",
                SourceMission = "Co_Burgundy2", TargetMission = "HP_Solo_Co_Burgundy2",
                TemplateMission = "Burgundy2",
                DefaultTitle = "SOLO ADAPTATION - BURGUNDY 2 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - BOURGOGNE 2 COOP",
                ObjectiveTextIds = new[] { 15570, 15571, 15572, 15575, 15576 },
                SpawnSourceMission = "Burgundy2",
                SpawnActors = new[] { "spawn_1", "spawn_2", "spawn_3", "spawn_4" }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-burgundy3",
                PackageFolder = "Heritage Solo - Coop Burgundy3",
                SourceMission = "Co_Burgundy3", TargetMission = "HP_Solo_Co_Burgundy3",
                TemplateMission = "Burgundy3",
                DefaultTitle = "SOLO ADAPTATION - BURGUNDY 3 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - BOURGOGNE 3 COOP",
                ObjectiveTextIds = new[] { 15588, 15580, 15581, 15582, 15584, 15585, 15586 },
                SpawnSourceMission = "Burgundy3",
                SpawnActors = new[] { "pspawn01", "pspawn02", "pspawn03", "pspawn04" },
                ExtraSoloScripts = new[] {
                    "bur3_plassign.scr", "bur3_plassign2.scr",
                    "bur3_pl01.scr", "bur3_pl02.scr"
                }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-libye1",
                PackageFolder = "Heritage Solo - Coop Libye1",
                SourceMission = "Co_Libye1", TargetMission = "HP_Solo_Co_Libye1",
                TemplateMission = "Libye1",
                DefaultTitle = "SOLO ADAPTATION - LIBYA 1 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - LIBYE 1 COOP",
                ObjectiveTextIds = new[] { 15510, 15518, 15514, 15515, 15519, 15509 },
                SpawnSourceMission = "Libye1",
                SpawnActors = new[] { "Spawnpoint01", "Spawnpoint02", "Spawnpoint03", "Spawnpoint04" }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-libye2",
                PackageFolder = "Heritage Solo - Coop Libye2",
                SourceMission = "Co_Libye2", TargetMission = "HP_Solo_Co_Libye2",
                TemplateMission = "Libye2",
                DefaultTitle = "SOLO ADAPTATION - LIBYA 2 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - LIBYE 2 COOP",
                ObjectiveTextIds = new[] { 15520, 15521 },
                SpawnSourceMission = "Libye2",
                SpawnActors = new[] { "Spawnsingle1", "Spawnsingle2", "Spawnsingle3", "Spawnsingle4" }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-libye3",
                PackageFolder = "Heritage Solo - Coop Libye3",
                SourceMission = "Co_Libye3", TargetMission = "HP_Solo_Co_Libye3",
                TemplateMission = "Libye3",
                DefaultTitle = "SOLO ADAPTATION - LIBYA 3 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - LIBYE 3 COOP",
                ObjectiveTextIds = new[] { 15535, 15536, 15530, 15537, 15538, 15531, 15545, 15501 },
                SpawnSourceMission = "Libye3",
                SpawnActors = new[] { "dummy_player1", "dummy_player2", "dummy_player3", "dummy_player4" }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-sicily1",
                PackageFolder = "Heritage Solo - Coop Sicily1",
                SourceMission = "Co_Sicily1", TargetMission = "HP_Solo_Co_Sicily1",
                TemplateMission = "Sicily1",
                DefaultTitle = "SOLO ADAPTATION - SICILY 1 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - SICILE 1 COOP",
                ObjectiveTextIds = new[] { 15540, 15541, 15542, 15545, 15546, 15547, 15548 },
                SpawnSourceMission = "Sicily1",
                SpawnActors = new[] { "player_1", "player_2", "player_3", "player_4" }
            },
            new SoloMissionSpec {
                Id = "heritage.solo.co-sicily2",
                PackageFolder = "Heritage Solo - Coop Sicily2",
                SourceMission = "Co_Sicily2", TargetMission = "HP_Solo_Co_Sicily2",
                TemplateMission = "Sicily2",
                DefaultTitle = "SOLO ADAPTATION - SICILY 2 CO-OP",
                FrenchTitle = "ADAPTATION SOLO - SICILE 2 COOP",
                ObjectiveTextIds = new[] { 15550, 15553, 15554, 15556, 15557 },
                SpawnSourceMission = "Sicily2",
                SpawnActors = new[] { "Player_1", "Player_2", "Player_3", "Player_4" }
            }
        };

        public static string ExportLibrary(
            string gamePath, string outputPath, Action<string> progress)
        {
            string game = Path.GetFullPath(gamePath.Trim()).TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            if (!File.Exists(Path.Combine(game, "HD2_SabreSquadron.exe")))
                throw new FileNotFoundException("HD2_SabreSquadron.exe est introuvable.");
            foreach (string archive in MissionArchives.Concat(ScriptArchives)
                .Distinct(StringComparer.OrdinalIgnoreCase))
                if (!File.Exists(Path.Combine(game, archive)))
                    throw new FileNotFoundException(
                        "Archive commerciale absente : " + archive);
            string output = Path.GetFullPath(outputPath);
            if (Directory.Exists(output) && Directory.GetFileSystemEntries(output).Length != 0)
                throw new IOException("Le dossier d'export doit être vide : " + output);
            Directory.CreateDirectory(output);
            Dictionary<string, Dictionary<int, string>> texts = LoadTextTables(game);
            foreach (SoloMissionSpec spec in Specs)
            {
                Report(progress, "Export de " + spec.FrenchTitle + "...");
                BuildPackage(game, output, spec, texts);
            }
            string validation = MissionPackageCore.ValidateLibrary(output);
            return validation + " Les 11 paquets complets sont prêts à être embarqués.";
        }

        public static string Check(string gamePath)
        {
            string game = ValidateGamePath(gamePath);
            string custom = Path.Combine(game, "CustomMissions");
            int packages = 0;
            int installed = 0;
            foreach (SoloMissionSpec spec in Specs)
            {
                string folder = Path.Combine(custom, spec.PackageFolder);
                if (OwnedPackage(folder, spec.Id)) packages++;
                if (File.Exists(Path.Combine(game, "Missions", spec.TargetMission, "tree.klz")))
                    installed++;
            }
            if (packages == Specs.Length && installed == Specs.Length)
                return "Pack installé : 11/11 adaptations présentes.";
            if (packages == 0 && installed == 0)
                return "Pack non installé; installation H&D2 valide.";
            return "Installation partielle : " + packages + "/11 paquets, "
                + installed + "/11 missions déployées.";
        }

        public static string Install(string gamePath, Action<string> progress)
        {
            string game = ValidateGamePath(gamePath);
            string custom = Path.Combine(game, "CustomMissions");
            Directory.CreateDirectory(custom);
            string stage = Path.Combine(custom, ".solo-pack-stage-"
                + Guid.NewGuid().ToString("N"));
            string backup = Path.Combine(custom, ".solo-pack-backup-"
                + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(stage);
            SourceArchiveRepair archiveRepair = null;
            bool packagesSwapped = false;
            bool integrationApplied = false;
            try
            {
                archiveRepair = RepairSourceArchives(game, progress);
                if (HasEmbeddedPayload())
                {
                    Report(progress, "Extraction des onze missions complètes embarquées...");
                    ExtractEmbeddedPayload(stage);
                }
                else
                {
                    Report(progress, "Vérification et extraction des fichiers commerciaux...");
                    Dictionary<string, Dictionary<int, string>> texts = LoadTextTables(game);
                    foreach (SoloMissionSpec spec in Specs)
                    {
                        Report(progress, "Préparation de " + spec.FrenchTitle + "...");
                        BuildPackage(game, stage, spec, texts);
                    }
                }
                string validation = MissionPackageCore.ValidateLibrary(stage);
                Report(progress, validation);
                SwapInPackages(custom, stage, backup);
                packagesSwapped = true;
                try
                {
                    Report(progress, "Installation des missions et reconstruction du menu...");
                    string result = MissionPackageCore.Integrate(custom, game, game);
                    Report(progress, result);
                    integrationApplied = true;
                }
                catch
                {
                    RollBackPackages(custom, backup);
                    packagesSwapped = false;
                    throw;
                }
                string status = Check(game);
                if (status.IndexOf("11/11", StringComparison.Ordinal) < 0)
                    throw new InvalidDataException("Contrôle final incomplet : " + status);
                archiveRepair.Commit();
                try { DeleteDirectoryIfPresent(backup); }
                catch { }
                packagesSwapped = false;
                return "Les 11 adaptations solo sont installées dans Adaptations multijoueur. "
                    + "Les archives sources ont été vérifiées et réparées si nécessaire. "
                    + "Le jeu n'a pas été lancé.";
            }
            catch
            {
                if (packagesSwapped)
                {
                    RollBackPackages(custom, backup);
                    packagesSwapped = false;
                    if (integrationApplied)
                    {
                        try { MissionPackageCore.Integrate(custom, game, game); }
                        catch { }
                    }
                }
                if (archiveRepair != null) archiveRepair.RollBack();
                throw;
            }
            finally
            {
                DeleteDirectoryIfPresent(stage);
                DeleteDirectoryIfPresent(backup);
                if (archiveRepair != null) archiveRepair.Dispose();
            }
        }

        public static string Restore(string gamePath, Action<string> progress)
        {
            string game = ValidateGamePath(gamePath);
            string custom = Path.Combine(game, "CustomMissions");
            Directory.CreateDirectory(custom);
            string backup = Path.Combine(custom, ".solo-pack-remove-"
                + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(backup);
            int moved = 0;
            SourceArchiveRepair archiveRepair = null;
            try
            {
                foreach (SoloMissionSpec spec in Specs)
                {
                    string source = Path.Combine(custom, spec.PackageFolder);
                    if (!Directory.Exists(source)) continue;
                    if (!OwnedPackage(source, spec.Id))
                        throw new InvalidDataException(
                            "Le dossier a été modifié et n'appartient plus à ce pack : " + source);
                    Directory.Move(source, Path.Combine(backup, spec.PackageFolder));
                    moved++;
                }
                if (moved == 0)
                    return "Aucun paquet de cette collection n'était présent.";
                archiveRepair = RepairSourceArchives(game, progress);
                try
                {
                    Report(progress, "Retrait des onze paquets et reconstruction du menu...");
                    MissionPackageCore.Integrate(custom, game, game);
                }
                catch
                {
                    RestoreMovedPackages(custom, backup);
                    throw;
                }
                DeleteEmptyOwnedPayloadDirectories(game);
                archiveRepair.Commit();
                try { DeleteDirectoryIfPresent(backup); }
                catch { }
                int removed = moved;
                moved = 0;
                return removed + " paquet(s) retiré(s). Les autres missions personnalisées ont été conservées.";
            }
            catch
            {
                if (moved > 0) RestoreMovedPackages(custom, backup);
                if (archiveRepair != null) archiveRepair.RollBack();
                throw;
            }
            finally
            {
                if (Directory.Exists(backup) && Directory.GetFileSystemEntries(backup).Length == 0)
                    Directory.Delete(backup);
                if (archiveRepair != null) archiveRepair.Dispose();
            }
        }

        private static void Report(Action<string> progress, string text)
        {
            if (progress != null) progress(text);
        }

        private static string ValidateGamePath(string gamePath)
        {
            if (String.IsNullOrWhiteSpace(gamePath))
                throw new DirectoryNotFoundException("Choisissez le dossier de H&D2.");
            string game = Path.GetFullPath(gamePath.Trim()).TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            string executable = Path.Combine(game, "HD2_SabreSquadron.exe");
            if (!File.Exists(executable))
                throw new FileNotFoundException("HD2_SabreSquadron.exe est introuvable.", executable);
            if (!HasEmbeddedPayload())
                foreach (string archive in MissionArchives.Concat(ScriptArchives)
                    .Distinct(StringComparer.OrdinalIgnoreCase))
                {
                    string path = Path.Combine(game, archive);
                    if (!File.Exists(path))
                        throw new FileNotFoundException(
                            "Archive commerciale absente : " + archive, path);
                }
            string textRoot = Path.Combine(game, "Text");
            if (!Directory.Exists(textRoot))
                throw new DirectoryNotFoundException("Le dossier Text du jeu est absent.");
            return game;
        }

        private static bool OwnedPackage(string folder, string expectedId)
        {
            string manifest = Path.Combine(folder, "mission.json");
            if (!File.Exists(manifest)) return false;
            try
            {
                Dictionary<string, object> document = Json.DeserializeObject(
                    File.ReadAllText(manifest, Encoding.UTF8)) as Dictionary<string, object>;
                object id;
                return document != null && document.TryGetValue("id", out id)
                    && String.Equals(Convert.ToString(id), expectedId,
                        StringComparison.OrdinalIgnoreCase);
            }
            catch { return false; }
        }

        private static void SwapInPackages(string custom, string stage, string backup)
        {
            Directory.CreateDirectory(backup);
            List<SoloMissionSpec> movedOld = new List<SoloMissionSpec>();
            List<SoloMissionSpec> movedNew = new List<SoloMissionSpec>();
            try
            {
                foreach (SoloMissionSpec spec in Specs)
                {
                    string target = Path.Combine(custom, spec.PackageFolder);
                    if (!Directory.Exists(target)) continue;
                    if (!OwnedPackage(target, spec.Id))
                        throw new InvalidDataException(
                            "Un dossier non géré porte déjà le nom réservé : " + target);
                    Directory.Move(target, Path.Combine(backup, spec.PackageFolder));
                    movedOld.Add(spec);
                }
                foreach (SoloMissionSpec spec in Specs)
                {
                    string source = Path.Combine(stage, spec.PackageFolder);
                    string target = Path.Combine(custom, spec.PackageFolder);
                    if (!Directory.Exists(source))
                        throw new DirectoryNotFoundException(
                            "Paquet préparé absent : " + source);
                    Directory.Move(source, target);
                    movedNew.Add(spec);
                }
            }
            catch
            {
                foreach (SoloMissionSpec spec in movedNew.AsEnumerable().Reverse())
                {
                    string target = Path.Combine(custom, spec.PackageFolder);
                    if (Directory.Exists(target)) Directory.Delete(target, true);
                }
                foreach (SoloMissionSpec spec in movedOld.AsEnumerable().Reverse())
                {
                    string source = Path.Combine(backup, spec.PackageFolder);
                    if (Directory.Exists(source))
                        Directory.Move(source, Path.Combine(custom, spec.PackageFolder));
                }
                throw;
            }
        }

        private static void RollBackPackages(string custom, string backup)
        {
            foreach (SoloMissionSpec spec in Specs)
            {
                string target = Path.Combine(custom, spec.PackageFolder);
                if (Directory.Exists(target) && OwnedPackage(target, spec.Id))
                    Directory.Delete(target, true);
            }
            RestoreMovedPackages(custom, backup);
        }

        private static void RestoreMovedPackages(string custom, string backup)
        {
            if (!Directory.Exists(backup)) return;
            foreach (SoloMissionSpec spec in Specs)
            {
                string source = Path.Combine(backup, spec.PackageFolder);
                if (!Directory.Exists(source)) continue;
                string target = Path.Combine(custom, spec.PackageFolder);
                if (Directory.Exists(target))
                    throw new IOException("Impossible de restaurer le dossier : " + target);
                Directory.Move(source, target);
            }
        }

        private static void DeleteDirectoryIfPresent(string path)
        {
            if (Directory.Exists(path)) Directory.Delete(path, true);
        }

        private static void DeleteEmptyOwnedPayloadDirectories(string game)
        {
            foreach (SoloMissionSpec spec in Specs)
            {
                string[] paths = {
                    Path.Combine(game, "Missions", spec.TargetMission),
                    Path.Combine(game, "Scripts", spec.TargetMission)
                };
                foreach (string path in paths)
                    if (Directory.Exists(path)
                        && Directory.GetFileSystemEntries(path).Length == 0)
                        Directory.Delete(path);
            }
        }

        private static void BuildPackage(
            string game, string stage, SoloMissionSpec spec,
            Dictionary<string, Dictionary<int, string>> texts)
        {
            string package = Path.Combine(stage, spec.PackageFolder);
            string missionRoot = Path.Combine(
                package, "payload", "Missions", spec.TargetMission);
            string scriptRoot = Path.Combine(
                package, "payload", "Scripts", spec.TargetMission);
            Directory.CreateDirectory(missionRoot);
            Directory.CreateDirectory(scriptRoot);

            Dictionary<string, ArchivedFile> missionFiles = ReadEffectiveSubtree(
                game, MissionArchives, "Missions/" + spec.SourceMission + "/");
            string[] required = {
                "tree.klz", "map.4ds", "scene.4ds", "loader.4ds",
                "actors.bin", "scene2.bin", "check2.bin", "mpscripts.dta"
            };
            foreach (string requiredFile in required)
                if (!missionFiles.ContainsKey(requiredFile.ToLowerInvariant()))
                    throw new InvalidDataException(spec.SourceMission
                        + " : fichier commercial requis absent : " + requiredFile);

            Dictionary<string, ArchivedFile> spawnFiles = ReadEffectiveSubtree(
                game, MissionArchives, "Missions/" + spec.SpawnSourceMission + "/");
            ArchivedFile spawnActors;
            if (!spawnFiles.TryGetValue("actors.bin", out spawnActors))
                throw new InvalidDataException(
                    spec.SpawnSourceMission + " : actors.bin absent.");

            byte[] convertedActors = ConvertActors(
                missionFiles["actors.bin"].Data, spawnActors.Data, spec);
            byte[] soloRegistry = ConvertRegistry(missionFiles["mpscripts.dta"].Data, spec);

            foreach (ArchivedFile file in missionFiles.Values)
            {
                byte[] data = file.Data;
                string name = file.Relative;
                if (String.Equals(name, "actors.bin", StringComparison.OrdinalIgnoreCase))
                    data = convertedActors;
                if (String.Equals(name, "scripts.dta", StringComparison.OrdinalIgnoreCase))
                    continue;
                WriteFile(Path.Combine(missionRoot, name), data);
            }
            WriteFile(Path.Combine(missionRoot, "scripts.dta"), soloRegistry);

            Dictionary<string, ArchivedFile> scripts = ReadEffectiveSubtree(
                game, ScriptArchives, "Scripts/" + spec.SourceMission + "/");
            if (scripts.Count == 0)
                throw new InvalidDataException(
                    spec.SourceMission + " : scripts commerciaux absents.");
            foreach (ArchivedFile file in scripts.Values)
                WriteFile(Path.Combine(scriptRoot, file.Relative),
                    DisableMultiplayerSpawnCalls(file.Data));

            Dictionary<string, ArchivedFile> soloScripts = ReadEffectiveSubtree(
                game, ScriptArchives, "Scripts/" + spec.SpawnSourceMission + "/");
            if (spec.ExtraSoloScripts != null && spec.ExtraSoloScripts.Length > 0)
            {
                foreach (string name in spec.ExtraSoloScripts)
                {
                    ArchivedFile file;
                    if (!soloScripts.TryGetValue(name.ToLowerInvariant(), out file))
                        throw new InvalidDataException(
                            spec.SpawnSourceMission + " : script solo absent : " + name);
                    WriteFile(Path.Combine(scriptRoot, name), file.Data);
                }
            }
            CompleteScriptClosure(scriptRoot, soloRegistry, soloScripts, spec);

            WriteManifest(Path.Combine(package, "mission.json"), spec, texts);
            ValidateBuiltPackage(package, spec, required);
        }

        private static void ValidateBuiltPackage(
            string package, SoloMissionSpec spec, IEnumerable<string> required)
        {
            string mission = Path.Combine(package, "payload", "Missions", spec.TargetMission);
            foreach (string file in required)
            {
                string expected = String.Equals(file, "mpscripts.dta",
                    StringComparison.OrdinalIgnoreCase) ? "scripts.dta" : file;
                string path = Path.Combine(mission, expected);
                if (!File.Exists(path) || new FileInfo(path).Length == 0)
                    throw new InvalidDataException(
                        spec.Id + " : sortie requise absente : " + expected);
            }
            string scripts = Path.Combine(package, "payload", "Scripts", spec.TargetMission);
            if (!Directory.Exists(scripts)
                || Directory.GetFiles(scripts, "*.scr", SearchOption.AllDirectories).Length == 0)
                throw new InvalidDataException(spec.Id + " : aucun script solo produit.");
            HashSet<string> availableScripts = new HashSet<string>(
                Directory.GetFiles(scripts, "*.scr", SearchOption.AllDirectories)
                    .Select(path => Path.GetFileName(path)),
                StringComparer.OrdinalIgnoreCase);
            byte[] registry = File.ReadAllBytes(Path.Combine(mission, "scripts.dta"));
            int offset = 6;
            while (offset < registry.Length)
            {
                ReadRegistryField(registry, ref offset);
                string script = ReadRegistryField(registry, ref offset)
                    .Replace('\\', '/').Split('/').Last();
                if (String.IsNullOrWhiteSpace(script)) continue;
                if (!script.EndsWith(".scr", StringComparison.OrdinalIgnoreCase))
                    script += ".scr";
                if (!availableScripts.Contains(script))
                    throw new InvalidDataException(
                        spec.Id + " : script lié absent : " + script);
            }
            foreach (string path in Directory.GetFiles(
                scripts, "*.scr", SearchOption.AllDirectories))
            {
                string text = Encoding.GetEncoding(1252).GetString(
                    File.ReadAllBytes(path));
                if (Regex.IsMatch(text, @"\bMP_EnableSpawnZone\s*\(",
                    RegexOptions.IgnoreCase | RegexOptions.CultureInvariant))
                    throw new InvalidDataException(
                        spec.Id + " : appel de zone multijoueur encore actif dans "
                        + Path.GetFileName(path));
                foreach (string dependency in ReferencedScriptNames(text))
                    if (!availableScripts.Contains(dependency))
                        throw new InvalidDataException(
                            spec.Id + " : dépendance de script absente : " + dependency);
            }
            byte[] actors = File.ReadAllBytes(Path.Combine(mission, "actors.bin"));
            foreach (string actor in spec.SpawnActors)
                FindActorRecord(actors, actor);
        }

        private static void WriteFile(string path, byte[] data)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllBytes(path, data);
            if (!File.ReadAllBytes(path).SequenceEqual(data))
                throw new IOException("Vérification d'écriture impossible : " + path);
        }

        private static Dictionary<string, ArchivedFile> ReadEffectiveSubtree(
            string game, IEnumerable<string> archiveNames, string wantedPrefix)
        {
            string prefix = wantedPrefix.Replace('\\', '/').Trim('/') + "/";
            Dictionary<string, ArchivedFile> result =
                new Dictionary<string, ArchivedFile>(StringComparer.OrdinalIgnoreCase);
            foreach (string archiveName in archiveNames)
            {
                string path = Path.Combine(game, archiveName);
                if (!File.Exists(path))
                    throw new FileNotFoundException(
                        "Archive commerciale absente : " + archiveName, path);
                using (DtaArchive archive = new DtaArchive(path))
                {
                    foreach (DtaEntry entry in archive.Entries)
                    {
                        string name = entry.Name.Replace('\\', '/');
                        if (!name.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                            continue;
                        string relative = name.Substring(prefix.Length);
                        if (String.IsNullOrWhiteSpace(relative)
                            || relative.StartsWith("/", StringComparison.Ordinal)
                            || relative.Split('/').Any(part => part == ".." || part == "."))
                            throw new InvalidDataException(
                                "Chemin commercial invalide : " + entry.Name);
                        result[relative.ToLowerInvariant()] = new ArchivedFile {
                            Relative = relative.Replace('/', Path.DirectorySeparatorChar),
                            Data = archive.Read(entry)
                        };
                    }
                }
            }
            return result;
        }

        private static Dictionary<string, Dictionary<int, string>> LoadTextTables(
            string game)
        {
            Dictionary<string, Dictionary<int, string>> result =
                new Dictionary<string, Dictionary<int, string>>(
                    StringComparer.OrdinalIgnoreCase);
            foreach (string language in Languages)
            {
                string path = Path.Combine(game, "Text", language, "TEXTY_DD.txt");
                if (!File.Exists(path)) continue;
                Encoding encoding = String.Equals(language, "czech",
                    StringComparison.OrdinalIgnoreCase) ? Encoding.GetEncoding(1250)
                    : String.Equals(language, "japan", StringComparison.OrdinalIgnoreCase)
                        ? new UTF8Encoding(false) : Encoding.GetEncoding(1252);
                Dictionary<int, string> values = new Dictionary<int, string>();
                foreach (string line in File.ReadAllLines(path, encoding))
                {
                    Match match = Regex.Match(line,
                        "^\\s*(?<id>[0-9]+)\\s+\\\"(?<text>.*)\\\"\\s*$");
                    int id;
                    if (!match.Success || !Int32.TryParse(match.Groups["id"].Value, out id))
                        continue;
                    string value = match.Groups["text"].Value
                        .Replace("\\\"", "\"").Replace("\\\\", "\\");
                    values[id] = value;
                }
                result[language] = values;
            }
            if (!result.ContainsKey("english") && !result.ContainsKey("EnglishUS"))
                throw new InvalidDataException(
                    "Les textes multijoueur anglais sont nécessaires pour construire le pack.");
            return result;
        }

        private static Dictionary<string, string> LocalizedObjective(
            int textId, int index,
            Dictionary<string, Dictionary<int, string>> tables)
        {
            Dictionary<string, string> result =
                new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (string language in Languages)
            {
                Dictionary<int, string> table;
                string value;
                if (tables.TryGetValue(language, out table)
                    && table.TryGetValue(textId, out value)
                    && !String.IsNullOrWhiteSpace(value))
                    result[language] = value.Trim();
            }
            string fallback;
            if (!result.TryGetValue("english", out fallback)
                && !result.TryGetValue("EnglishUS", out fallback)
                && !result.TryGetValue("french", out fallback))
                fallback = "Complete objective " + index + ".";
            result["default"] = fallback;
            return result;
        }

        private static void WriteManifest(
            string path, SoloMissionSpec spec,
            Dictionary<string, Dictionary<int, string>> texts)
        {
            Dictionary<string, object> title = new Dictionary<string, object>();
            title["default"] = spec.DefaultTitle;
            title["english"] = spec.DefaultTitle;
            title["EnglishUS"] = spec.DefaultTitle;
            title["french"] = spec.FrenchTitle;
            List<object> objectives = new List<object>();
            for (int index = 0; index < spec.ObjectiveTextIds.Length; index++)
                objectives.Add(LocalizedObjective(
                    spec.ObjectiveTextIds[index], index + 1, texts));

            Dictionary<string, object> document = new Dictionary<string, object>();
            document["format"] = 1;
            document["id"] = spec.Id;
            document["category"] = Category;
            document["missionDirectory"] = spec.TargetMission;
            document["templateMission"] = spec.TemplateMission;
            document["title"] = title;
            document["objectives"] = objectives;
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, Json.Serialize(document), new UTF8Encoding(false));
        }

        private static byte[] DisableMultiplayerSpawnCalls(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            text = Regex.Replace(
                text,
                @"\bMP_EnableSpawnZone\s*\([^;]*\)\s*;",
                "/* spawn multijoueur désactivé dans l'adaptation solo */",
                RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            return Encoding.GetEncoding(1252).GetBytes(text);
        }

        private static string NormalizeScriptName(string value)
        {
            string name = value.Replace('\\', '/').Split('/').Last().Trim();
            if (name.Length > 0
                && !name.EndsWith(".scr", StringComparison.OrdinalIgnoreCase))
                name += ".scr";
            return name;
        }

        private static IEnumerable<string> ReferencedScriptNames(string text)
        {
            HashSet<string> result = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            foreach (Match match in Regex.Matches(text,
                @"^\s*#include\s+""([^""]+\.scr)""",
                RegexOptions.IgnoreCase | RegexOptions.Multiline
                    | RegexOptions.CultureInvariant))
                result.Add(NormalizeScriptName(match.Groups[1].Value));
            foreach (Match match in Regex.Matches(text,
                @"\bScriptAssign\s*\(\s*[^,\r\n]+\s*,\s*""([^""]+)""",
                RegexOptions.IgnoreCase | RegexOptions.CultureInvariant))
                result.Add(NormalizeScriptName(match.Groups[1].Value));
            return result.Where(value => value.Length > 0);
        }

        private static IEnumerable<string> RegistryScriptNames(byte[] registry)
        {
            int offset = 6;
            while (offset < registry.Length)
            {
                ReadRegistryField(registry, ref offset);
                string script = NormalizeScriptName(
                    ReadRegistryField(registry, ref offset));
                if (script.Length > 0) yield return script;
            }
        }

        private static void CompleteScriptClosure(
            string scriptRoot, byte[] registry,
            Dictionary<string, ArchivedFile> fallbackScripts,
            SoloMissionSpec spec)
        {
            Dictionary<string, ArchivedFile> fallbacks = fallbackScripts.Values
                .GroupBy(file => Path.GetFileName(file.Relative),
                    StringComparer.OrdinalIgnoreCase)
                .ToDictionary(group => group.Key, group => group.Last(),
                    StringComparer.OrdinalIgnoreCase);
            HashSet<string> visited = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            Queue<string> pending = new Queue<string>(RegistryScriptNames(registry));
            while (pending.Count > 0)
            {
                string name = NormalizeScriptName(pending.Dequeue());
                if (name.Length == 0 || !visited.Add(name)) continue;
                string path = Path.Combine(scriptRoot, name);
                if (!File.Exists(path))
                {
                    ArchivedFile fallback;
                    if (!fallbacks.TryGetValue(name, out fallback))
                        throw new InvalidDataException(
                            spec.Id + " : script lié introuvable : " + name);
                    WriteFile(path, DisableMultiplayerSpawnCalls(fallback.Data));
                }
                string text = Encoding.GetEncoding(1252).GetString(
                    File.ReadAllBytes(path));
                foreach (string dependency in ReferencedScriptNames(text))
                    if (!visited.Contains(dependency)) pending.Enqueue(dependency);
            }
        }

        private static byte[] ConvertRegistry(byte[] multiplayer, SoloMissionSpec spec)
        {
            if (multiplayer == null || multiplayer.Length < 6
                || ReadUInt32(multiplayer, 2) != multiplayer.Length)
                throw new InvalidDataException(
                    spec.SourceMission + " : registre mpscripts.dta invalide.");
            byte[] result = (byte[])multiplayer.Clone();
            if (String.Equals(spec.SourceMission, "Co_Burgundy3",
                StringComparison.OrdinalIgnoreCase))
            {
                result = AddBinding(result, "pspawn04", "bur3_plassign2.scr");
                result = AddBinding(result, "pspawn01", "bur3_plassign.scr");
            }
            return result;
        }

        private static byte[] AddBinding(byte[] registry, string actor, string script)
        {
            if (RegistryHasBinding(registry, actor, script)) return registry;
            byte[] left = RegistryField(actor);
            byte[] right = RegistryField(script);
            byte[] result = new byte[registry.Length + left.Length + right.Length];
            Buffer.BlockCopy(registry, 0, result, 0, registry.Length);
            Buffer.BlockCopy(left, 0, result, registry.Length, left.Length);
            Buffer.BlockCopy(right, 0, result, registry.Length + left.Length, right.Length);
            WriteUInt32(result, 2, result.Length);
            return result;
        }

        private static bool RegistryHasBinding(byte[] data, string actor, string script)
        {
            int offset = 6;
            while (offset < data.Length)
            {
                string currentActor = ReadRegistryField(data, ref offset);
                string currentScript = ReadRegistryField(data, ref offset);
                if (String.Equals(currentActor, actor, StringComparison.OrdinalIgnoreCase)
                    && String.Equals(currentScript, script, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static byte[] RegistryField(string value)
        {
            byte[] encoded = Encoding.GetEncoding(1252).GetBytes(value);
            byte[] result = new byte[7 + encoded.Length];
            WriteUInt16(result, 0, 1);
            WriteUInt32(result, 2, result.Length);
            Buffer.BlockCopy(encoded, 0, result, 6, encoded.Length);
            result[result.Length - 1] = 0;
            return result;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length || ReadUInt16(data, offset) != 1)
                throw new InvalidDataException("Registre de scripts tronqué.");
            int size = checked((int)ReadUInt32(data, offset + 2));
            if (size < 7 || offset + size > data.Length || data[offset + size - 1] != 0)
                throw new InvalidDataException("Champ de registre invalide.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, size - 7);
            offset += size;
            return value;
        }

        private static byte[] ConvertActors(
            byte[] multiplayerActors, byte[] soloActors, SoloMissionSpec spec)
        {
            List<byte[]> records = new List<byte[]>();
            byte[] position = null;
            if (!String.IsNullOrWhiteSpace(spec.SpawnPositionActor))
            {
                byte[] targetRecord = FindActorRecord(
                    multiplayerActors, spec.SpawnPositionActor);
                position = ActorPosition(targetRecord);
                if (position == null)
                    throw new InvalidDataException(spec.SourceMission
                        + " : position de départ absente sur "
                        + spec.SpawnPositionActor + ".");
            }
            foreach (string actor in spec.SpawnActors)
            {
                byte[] record = FindActorRecord(soloActors, actor);
                if (position != null)
                    record = ReplaceActorPosition(record, position);
                records.Add(record);
            }
            byte[] result = AppendActorRecords(multiplayerActors, records);
            foreach (string actor in spec.SpawnActors)
                FindActorRecord(result, actor);
            return result;
        }

        private static byte[] FindActorRecord(byte[] data, string wantedName)
        {
            int sectionStart;
            int sectionEnd;
            ActorSection(data, out sectionStart, out sectionEnd);
            int cursor = sectionStart + 6;
            while (cursor < sectionEnd)
            {
                int end = BlockEnd(data, cursor, sectionEnd);
                string name = DirectString(data, cursor, end, 0x10);
                if (String.Equals(name, wantedName, StringComparison.OrdinalIgnoreCase))
                {
                    byte[] result = new byte[end - cursor];
                    Buffer.BlockCopy(data, cursor, result, 0, result.Length);
                    return result;
                }
                cursor = end;
            }
            throw new InvalidDataException("Acteur commercial introuvable : " + wantedName);
        }

        private static byte[] ActorPosition(byte[] record)
        {
            int cursor = 6;
            while (cursor < record.Length)
            {
                int end = BlockEnd(record, cursor, record.Length);
                ushort kind = ReadUInt16(record, cursor);
                if ((kind == 0x20 || kind == 0x2C) && end - cursor >= 18)
                {
                    byte[] result = new byte[12];
                    Buffer.BlockCopy(record, cursor + 6, result, 0, 12);
                    return result;
                }
                cursor = end;
            }
            return null;
        }

        private static byte[] ReplaceActorPosition(byte[] record, byte[] position)
        {
            if (position == null || position.Length != 12)
                throw new ArgumentException("Position d'acteur invalide.", "position");
            byte[] result = (byte[])record.Clone();
            int cursor = 6;
            bool replaced = false;
            while (cursor < result.Length)
            {
                int end = BlockEnd(result, cursor, result.Length);
                ushort kind = ReadUInt16(result, cursor);
                if ((kind == 0x20 || kind == 0x2C) && end - cursor >= 18)
                {
                    Buffer.BlockCopy(position, 0, result, cursor + 6, 12);
                    replaced = true;
                }
                cursor = end;
            }
            if (!replaced)
                throw new InvalidDataException("Record d'acteur sans position.");
            return result;
        }

        private static byte[] AppendActorRecords(byte[] data, IEnumerable<byte[]> records)
        {
            List<byte[]> additions = records.Select(item => (byte[])item.Clone()).ToList();
            if (additions.Count == 0) return (byte[])data.Clone();
            int sectionStart;
            int sectionEnd;
            ActorSection(data, out sectionStart, out sectionEnd);
            HashSet<string> existing = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            int cursor = sectionStart + 6;
            while (cursor < sectionEnd)
            {
                int end = BlockEnd(data, cursor, sectionEnd);
                string name = DirectString(data, cursor, end, 0x10);
                if (!String.IsNullOrWhiteSpace(name)) existing.Add(name);
                cursor = end;
            }
            foreach (byte[] record in additions)
            {
                if (ReadUInt16(record, 0) != 0x4010
                    || ReadUInt32(record, 2) != record.Length)
                    throw new InvalidDataException("Record d'acteur source invalide.");
                string name = DirectString(record, 0, record.Length, 0x10);
                if (String.IsNullOrWhiteSpace(name) || !existing.Add(name))
                    throw new InvalidDataException(
                        "Acteur solo absent ou dupliqué : " + name);
            }
            int added = additions.Sum(item => item.Length);
            byte[] result = new byte[data.Length + added];
            Buffer.BlockCopy(data, 0, result, 0, sectionEnd);
            int output = sectionEnd;
            foreach (byte[] record in additions)
            {
                Buffer.BlockCopy(record, 0, result, output, record.Length);
                output += record.Length;
            }
            Buffer.BlockCopy(data, sectionEnd, result, output, data.Length - sectionEnd);
            WriteUInt32(result, 2, result.Length);
            WriteUInt32(result, sectionStart + 2,
                checked((int)ReadUInt32(data, sectionStart + 2) + added));
            int verifyStart;
            int verifyEnd;
            ActorSection(result, out verifyStart, out verifyEnd);
            if (verifyEnd != sectionEnd + added)
                throw new InvalidDataException("Validation actors.bin impossible.");
            return result;
        }

        private static void ActorSection(
            byte[] data, out int sectionStart, out int sectionEnd)
        {
            if (data == null || data.Length < 12 || ReadUInt16(data, 0) != 0x4C53
                || ReadUInt32(data, 2) != data.Length)
                throw new InvalidDataException("actors.bin invalide.");
            sectionStart = 6;
            if (ReadUInt16(data, sectionStart) != 0x4000)
                throw new InvalidDataException("Section d'acteurs absente.");
            sectionEnd = BlockEnd(data, sectionStart, data.Length);
        }

        private static string DirectString(
            byte[] data, int blockStart, int blockEnd, ushort wantedKind)
        {
            int cursor = blockStart + 6;
            while (cursor < blockEnd)
            {
                int end = BlockEnd(data, cursor, blockEnd);
                if (ReadUInt16(data, cursor) == wantedKind)
                {
                    int length = end - cursor - 6;
                    while (length > 0 && data[cursor + 6 + length - 1] == 0) length--;
                    return Encoding.GetEncoding(1252).GetString(data, cursor + 6, length);
                }
                cursor = end;
            }
            return null;
        }

        private static int BlockEnd(byte[] data, int start, int parentEnd)
        {
            if (start < 0 || start > parentEnd - 6 || parentEnd > data.Length)
                throw new InvalidDataException("Bloc binaire tronqué.");
            int size = checked((int)ReadUInt32(data, start + 2));
            if (size < 6 || start > parentEnd - size)
                throw new InvalidDataException("Taille de bloc binaire invalide.");
            return start + size;
        }

        private static ushort ReadUInt16(byte[] data, int offset)
        {
            if (offset < 0 || offset > data.Length - 2)
                throw new InvalidDataException("Lecture binaire hors tampon.");
            return (ushort)(data[offset] | (data[offset + 1] << 8));
        }

        private static uint ReadUInt32(byte[] data, int offset)
        {
            if (offset < 0 || offset > data.Length - 4)
                throw new InvalidDataException("Lecture binaire hors tampon.");
            return (uint)data[offset] | ((uint)data[offset + 1] << 8)
                | ((uint)data[offset + 2] << 16) | ((uint)data[offset + 3] << 24);
        }

        private static void WriteUInt16(byte[] data, int offset, int value)
        {
            data[offset] = (byte)(value & 0xFF);
            data[offset + 1] = (byte)((value >> 8) & 0xFF);
        }

        private static void WriteUInt32(byte[] data, int offset, int value)
        {
            data[offset] = (byte)(value & 0xFF);
            data[offset + 1] = (byte)((value >> 8) & 0xFF);
            data[offset + 2] = (byte)((value >> 16) & 0xFF);
            data[offset + 3] = (byte)((value >> 24) & 0xFF);
        }

        private static bool HasEmbeddedPayload()
        {
            return Assembly.GetExecutingAssembly().GetManifestResourceNames().Any(
                name => String.Equals(name, EmbeddedPayloadResource,
                    StringComparison.Ordinal));
        }

        private static bool HasEmbeddedSourceArchives()
        {
            return Assembly.GetExecutingAssembly().GetManifestResourceNames().Any(
                name => String.Equals(name, EmbeddedSourceArchivesResource,
                    StringComparison.Ordinal));
        }

        private static string Sha256File(string path)
        {
            using (FileStream input = File.OpenRead(path))
            using (SHA256 algorithm = SHA256.Create())
                return BitConverter.ToString(algorithm.ComputeHash(input)).Replace("-", "");
        }

        private static SourceArchiveRepair RepairSourceArchives(
            string game, Action<string> progress)
        {
            string repairRoot = Path.Combine(game, ".solo-pack-archive-repair-"
                + Guid.NewGuid().ToString("N"));
            List<SourceArchiveEntry> replaced = new List<SourceArchiveEntry>();
            SourceArchiveRepair session = new SourceArchiveRepair(
                repairRoot, game, replaced);
            if (!HasEmbeddedSourceArchives())
            {
                foreach (string name in SourceArchives)
                    if (!File.Exists(Path.Combine(game, name)))
                        throw new FileNotFoundException(
                            "Archive commerciale absente du constructeur : " + name);
                return session;
            }

            Directory.CreateDirectory(repairRoot);
            try
            {
                Assembly assembly = Assembly.GetExecutingAssembly();
                using (Stream stream = assembly.GetManifestResourceStream(
                    EmbeddedSourceArchivesResource))
                using (ZipArchive archive = new ZipArchive(
                    stream, ZipArchiveMode.Read, false))
                {
                    ZipArchiveEntry manifestEntry = archive.GetEntry("source-archives.json");
                    if (manifestEntry == null)
                        throw new InvalidDataException(
                            "Manifeste des archives sources absent de l'exécutable.");
                    Dictionary<string, object> manifest;
                    using (StreamReader reader = new StreamReader(
                        manifestEntry.Open(), Encoding.UTF8, true))
                        manifest = Json.DeserializeObject(reader.ReadToEnd())
                            as Dictionary<string, object>;
                    if (manifest == null || !manifest.ContainsKey("archives"))
                        throw new InvalidDataException(
                            "Manifeste des archives sources invalide.");
                    object[] rawEntries = manifest["archives"] as object[];
                    if (rawEntries == null || rawEntries.Length != SourceArchives.Length)
                        throw new InvalidDataException(
                            "Nombre d'archives sources embarquées invalide.");

                    Dictionary<string, Dictionary<string, object>> records =
                        new Dictionary<string, Dictionary<string, object>>(
                            StringComparer.OrdinalIgnoreCase);
                    foreach (object raw in rawEntries)
                    {
                        Dictionary<string, object> record = raw as Dictionary<string, object>;
                        if (record == null) throw new InvalidDataException(
                            "Entrée d'archive source invalide.");
                        string name = Convert.ToString(record["name"]);
                        if (Path.GetFileName(name) != name || records.ContainsKey(name))
                            throw new InvalidDataException(
                                "Nom d'archive source invalide : " + name);
                        records[name] = record;
                    }

                    foreach (string name in SourceArchives)
                    {
                        Dictionary<string, object> record;
                        if (!records.TryGetValue(name, out record))
                            throw new InvalidDataException(
                                "Archive source non embarquée : " + name);
                        long expectedSize = Convert.ToInt64(record["size"]);
                        string expectedHash = Convert.ToString(record["sha256"]);
                        string target = Path.Combine(game, name);
                        if (File.Exists(target)
                            && new FileInfo(target).Length == expectedSize
                            && String.Equals(Sha256File(target), expectedHash,
                                StringComparison.OrdinalIgnoreCase))
                        {
                            Report(progress, name + " : archive source vérifiée.");
                            continue;
                        }

                        Report(progress, name
                            + " : archive absente ou altérée, remplacement autonome...");
                        ZipArchiveEntry payload = archive.GetEntry(name);
                        if (payload == null || payload.Length != expectedSize)
                            throw new InvalidDataException(
                                "Contenu embarqué invalide : " + name);
                        string fresh = Path.Combine(repairRoot, name + ".new");
                        using (Stream input = payload.Open())
                        using (FileStream output = new FileStream(
                            fresh, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                            input.CopyTo(output);
                        if (new FileInfo(fresh).Length != expectedSize
                            || !String.Equals(Sha256File(fresh), expectedHash,
                                StringComparison.OrdinalIgnoreCase))
                            throw new InvalidDataException(
                                "Échec de vérification après extraction : " + name);

                        SourceArchiveEntry replacedEntry = new SourceArchiveEntry {
                            Name = name,
                            Size = expectedSize,
                            Sha256 = expectedHash,
                            OriginalPath = Path.Combine(repairRoot, name + ".original"),
                            OriginallyMissing = !File.Exists(target)
                        };
                        if (!replacedEntry.OriginallyMissing)
                            File.Move(target, replacedEntry.OriginalPath);
                        replaced.Add(replacedEntry);
                        File.Move(fresh, target);
                    }
                }
                return session;
            }
            catch
            {
                session.RollBack();
                throw;
            }
        }

        private static void ExtractEmbeddedPayload(string destination)
        {
            Assembly assembly = Assembly.GetExecutingAssembly();
            using (Stream stream = assembly.GetManifestResourceStream(
                EmbeddedPayloadResource))
            {
                if (stream == null)
                    throw new InvalidDataException(
                        "Le contenu autonome des missions est absent de l'exécutable.");
                string root = Path.GetFullPath(destination).TrimEnd(
                    Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                    + Path.DirectorySeparatorChar;
                using (ZipArchive archive = new ZipArchive(
                    stream, ZipArchiveMode.Read, false))
                {
                    foreach (ZipArchiveEntry entry in archive.Entries)
                    {
                        string relative = entry.FullName.Replace('/', Path.DirectorySeparatorChar);
                        if (String.IsNullOrWhiteSpace(relative)) continue;
                        string target = Path.GetFullPath(Path.Combine(root, relative));
                        if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                            throw new InvalidDataException(
                                "Chemin hors du contenu autonome : " + entry.FullName);
                        if (entry.FullName.EndsWith("/", StringComparison.Ordinal))
                        {
                            Directory.CreateDirectory(target);
                            continue;
                        }
                        Directory.CreateDirectory(Path.GetDirectoryName(target));
                        using (Stream input = entry.Open())
                        using (FileStream output = new FileStream(
                            target, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                            input.CopyTo(output);
                    }
                }
            }
        }

        private static byte[] MakeBlock(ushort kind, params byte[][] payloads)
        {
            int payloadLength = payloads.Sum(item => item.Length);
            byte[] result = new byte[6 + payloadLength];
            WriteUInt16(result, 0, kind);
            WriteUInt32(result, 2, result.Length);
            int cursor = 6;
            foreach (byte[] payload in payloads)
            {
                Buffer.BlockCopy(payload, 0, result, cursor, payload.Length);
                cursor += payload.Length;
            }
            return result;
        }

        private static byte[] TestActor(string name, byte value)
        {
            byte[] encoded = Encoding.GetEncoding(1252).GetBytes(name + "\0");
            byte[] position = Enumerable.Repeat(value, 12).ToArray();
            return MakeBlock(0x4010,
                MakeBlock(0x10, encoded),
                MakeBlock(0x20, position),
                MakeBlock(0x2C, position));
        }

        public static string RunSelfTests()
        {
            byte[] targetRecord = TestActor("zone1", 7);
            byte[] sourceRecord = TestActor("Spawnpoint01", 3);
            byte[] targetActors = MakeBlock(0x4C53,
                MakeBlock(0x4000, targetRecord), MakeBlock(0xAE20));
            byte[] sourceActors = MakeBlock(0x4C53,
                MakeBlock(0x4000, sourceRecord), MakeBlock(0xAE20));
            SoloMissionSpec spec = new SoloMissionSpec {
                SourceMission = "test", SpawnPositionActor = "zone1",
                SpawnActors = new[] { "Spawnpoint01" }
            };
            byte[] converted = ConvertActors(targetActors, sourceActors, spec);
            byte[] restored = FindActorRecord(converted, "Spawnpoint01");
            if (!ActorPosition(restored).SequenceEqual(Enumerable.Repeat((byte)7, 12)))
                throw new InvalidDataException("Autotest actors.bin échoué.");

            byte[] registry = new byte[6];
            WriteUInt32(registry, 2, registry.Length);
            registry = AddBinding(registry, "actor", "script.scr");
            if (!RegistryHasBinding(registry, "actor", "script.scr")
                || ReadUInt32(registry, 2) != registry.Length)
                throw new InvalidDataException("Autotest registre de scripts échoué.");

            byte[] script = Encoding.GetEncoding(1252).GetBytes(
                "MP_EnableSpawnZone(\"zone2\", 0);\r\nSetObjectiveStatus(1,1);");
            string patched = Encoding.GetEncoding(1252).GetString(
                DisableMultiplayerSpawnCalls(script));
            if (patched.IndexOf("MP_EnableSpawnZone", StringComparison.OrdinalIgnoreCase) >= 0
                || patched.IndexOf("SetObjectiveStatus", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException("Autotest scripts solo échoué.");
            return "Autotests du pack solo réussis.";
        }
    }
}
