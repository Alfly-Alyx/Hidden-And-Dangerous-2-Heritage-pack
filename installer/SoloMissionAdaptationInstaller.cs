using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;

namespace HD2CommunityInstaller
{
    internal static class SoloMissionAdaptationInstaller
    {
        private sealed class Adaptation
        {
            public string Id;
            public string PackageFolder;
            public string MissionDirectory;
        }

        private static readonly Adaptation[] Adaptations = {
            Item("heritage.solo.alps3-objective", "Heritage Solo - Alps3 Objectif", "HP_Solo_Alps3_Obj"),
            Item("heritage.solo.ardennes1-objective", "Heritage Solo - Ardennes1 Objectif", "HP_Solo_Ardens1_Obj"),
            Item("heritage.solo.co-brest", "Heritage Solo - Coop Brest", "HP_Solo_Co_Brest"),
            Item("heritage.solo.co-burgundy1", "Heritage Solo - Coop Burgundy1", "HP_Solo_Co_Burgundy1"),
            Item("heritage.solo.co-burgundy2", "Heritage Solo - Coop Burgundy2", "HP_Solo_Co_Burgundy2"),
            Item("heritage.solo.co-burgundy3", "Heritage Solo - Coop Burgundy3", "HP_Solo_Co_Burgundy3"),
            Item("heritage.solo.co-libye1", "Heritage Solo - Coop Libye1", "HP_Solo_Co_Libye1"),
            Item("heritage.solo.co-libye2", "Heritage Solo - Coop Libye2", "HP_Solo_Co_Libye2"),
            Item("heritage.solo.co-libye3", "Heritage Solo - Coop Libye3", "HP_Solo_Co_Libye3"),
            Item("heritage.solo.co-sicily1", "Heritage Solo - Coop Sicily1", "HP_Solo_Co_Sicily1"),
            Item("heritage.solo.co-sicily2", "Heritage Solo - Coop Sicily2", "HP_Solo_Co_Sicily2")
        };

        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer {
            MaxJsonLength = 16 * 1024 * 1024
        };

        private static Adaptation Item(string id, string folder, string mission)
        {
            return new Adaptation {
                Id = id, PackageFolder = folder, MissionDirectory = mission
            };
        }

        public static string DetectStatus(string gamePath)
        {
            int packages = 0;
            int deployed = 0;
            foreach (Adaptation adaptation in Adaptations)
            {
                string package = InstallerCore.SafeGameTarget(
                    gamePath, "CustomMissions/" + adaptation.PackageFolder);
                if (OwnedPackage(package, adaptation.Id)) packages++;
                if (DeployedMission(gamePath, adaptation.MissionDirectory)) deployed++;
            }
            if (packages == Adaptations.Length && deployed == Adaptations.Length)
                return "deja installees (11/11 dans Adaptations multijoueur)";
            if (packages == 0 && deployed == 0) return "a installer";
            return "partielles (" + packages + "/11 paquets; "
                + deployed + "/11 missions deployees)";
        }

        private static bool DeployedMission(string gamePath, string missionDirectory)
        {
            string missionRoot = InstallerCore.SafeGameTarget(
                gamePath, "Missions/" + missionDirectory);
            string[] required = {
                "tree.klz", "map.4ds", "scene.4ds", "loader.4ds",
                "actors.bin", "scene2.bin", "check2.bin", "scripts.dta"
            };
            if (required.Any(file => !File.Exists(Path.Combine(missionRoot, file))))
                return false;
            string scriptRoot = InstallerCore.SafeGameTarget(
                gamePath, "Scripts/" + missionDirectory);
            return Directory.Exists(scriptRoot)
                && Directory.GetFiles(scriptRoot, "*.scr", SearchOption.AllDirectories).Length > 0;
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            string manager = InstallerCore.SafeGameTarget(
                gamePath, "HD2-Custom-Mission-Manager.exe");
            if (!File.Exists(manager))
                throw new FileNotFoundException(
                    "Le gestionnaire de missions personnalisees est absent.", manager);

            string stage = Path.Combine(Path.GetTempPath(),
                "HD2-Heritage-solo-adaptations-" + Guid.NewGuid().ToString("N"));
            try
            {
                InstallerCore.Report(progress,
                    "Creation des 11 adaptations solo depuis les archives du jeu...");
                string export = CustomMissionManagerInstaller.RunManager(
                    manager, "--export-heritage-solo", gamePath, stage);
                ValidateStage(stage);
                CopyPackages(stage, gamePath, journal, prepared);
                InstallerCore.Report(progress, export.Trim());
                InstallerCore.Report(progress,
                    "Onze adaptations pretes pour le menu Adaptations multijoueur.");
            }
            finally
            {
                if (Directory.Exists(stage)) Directory.Delete(stage, true);
            }
        }

        private static void ValidateStage(string stage)
        {
            HashSet<string> expected = new HashSet<string>(
                Adaptations.Select(item => item.PackageFolder),
                StringComparer.OrdinalIgnoreCase);
            string[] folders = Directory.GetDirectories(stage);
            if (folders.Length != Adaptations.Length
                || folders.Any(folder => !expected.Contains(Path.GetFileName(folder))))
                throw new InvalidDataException(
                    "Le constructeur n'a pas produit exactement les 11 adaptations attendues.");
            foreach (Adaptation adaptation in Adaptations)
            {
                string package = Path.Combine(stage, adaptation.PackageFolder);
                if (!OwnedPackage(package, adaptation.Id))
                    throw new InvalidDataException(
                        "Paquet produit invalide : " + adaptation.PackageFolder);
                if (!File.Exists(Path.Combine(package, "payload", "Missions",
                        adaptation.MissionDirectory, "tree.klz")))
                    throw new InvalidDataException(
                        "Carte absente du paquet : " + adaptation.PackageFolder);
            }
        }

        private static void CopyPackages(
            string stage, string gamePath, StateJournal journal,
            HashSet<string> prepared)
        {
            string customRoot = InstallerCore.SafeGameTarget(gamePath, "CustomMissions");
            Directory.CreateDirectory(customRoot);
            foreach (Adaptation adaptation in Adaptations)
            {
                string source = Path.Combine(stage, adaptation.PackageFolder);
                string destination = Path.Combine(customRoot, adaptation.PackageFolder);
                if (Directory.Exists(destination)
                    && !OwnedPackage(destination, adaptation.Id))
                    throw new InvalidDataException(
                        "Un dossier non gere utilise le nom reserve : " + destination);
                foreach (string sourceFile in Directory.GetFiles(
                    source, "*", SearchOption.AllDirectories))
                {
                    if ((File.GetAttributes(sourceFile) & FileAttributes.ReparsePoint) != 0)
                        throw new InvalidDataException(
                            "Lien interdit dans le paquet : " + sourceFile);
                    string suffix = Path.GetFullPath(sourceFile).Substring(
                        Path.GetFullPath(source).TrimEnd(
                            Path.DirectorySeparatorChar,
                            Path.AltDirectorySeparatorChar).Length)
                        .TrimStart(Path.DirectorySeparatorChar,
                            Path.AltDirectorySeparatorChar);
                    string relative = Path.Combine(
                        "CustomMissions", adaptation.PackageFolder, suffix);
                    string target = InstallerCore.SafeGameTarget(gamePath, relative);
                    InstallerCore.PrepareTarget(
                        gamePath, relative, target, journal, prepared);
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    string temporary = target + ".hd2pack.tmp";
                    try
                    {
                        File.Copy(sourceFile, temporary, true);
                        File.Copy(temporary, target, true);
                        journal.RecordHash(
                            relative, CmpInstaller.ComputeSha256(target));
                    }
                    finally
                    {
                        if (File.Exists(temporary)) File.Delete(temporary);
                    }
                }
            }
        }

        private static bool OwnedPackage(string folder, string expectedId)
        {
            string manifest = Path.Combine(folder, "mission.json");
            if (!File.Exists(manifest)) return false;
            try
            {
                Dictionary<string, object> document = Json.DeserializeObject(
                    File.ReadAllText(manifest, Encoding.UTF8))
                    as Dictionary<string, object>;
                object id;
                return document != null && document.TryGetValue("id", out id)
                    && String.Equals(Convert.ToString(id), expectedId,
                        StringComparison.OrdinalIgnoreCase);
            }
            catch { return false; }
        }
    }
}
