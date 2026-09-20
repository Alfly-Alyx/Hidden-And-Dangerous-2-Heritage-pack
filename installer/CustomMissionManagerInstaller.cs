using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace HD2CommunityInstaller
{
    internal static class CustomMissionManagerInstaller
    {
        private const string ManagerHashResource =
            "HD2CommunityInstaller.CustomMissionManager.sha256";

        private static readonly string[] MenuRuntimeFiles = {
            "GameData/Gamedata02.gdt",
            "GameData/Gamedata03.gdt",
            "GameData/Gamedata04.gdt",
            "GameData/Gamedata05.gdt",
            "Models/singleplayer.4ds",
            "Models/single mission 2.4ds",
            "Scripts/HD2.CustomMenu.asi",
            "STATIC_MENU_MANAGED_FILES.json",
            "CUSTOM_MISSIONS_INSTALL.json"
        };

        private sealed class EmbeddedFile
        {
            public string ResourceName;
            public string RelativePath;
            public string Sha256;
            public bool PreserveExisting;
            public bool Executable;
        }

        private static readonly EmbeddedFile[] Files = {
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissionManager.exe",
                RelativePath = "HD2-Custom-Mission-Manager.exe",
                Executable = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.Readme",
                RelativePath = "CustomMissions/README.md",
                Sha256 = "A68618FCEE71845E95A6967F830CF1556E4D0916E5B2446761E4A1820F6E8415",
                PreserveExisting = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.Schema",
                RelativePath = "CustomMissions/mission.schema.json",
                Sha256 = "C53CDD71AAB058D3B8E4E94B6A1140663B7D9A0B577B040FFD6850CA3EDE9D75",
                PreserveExisting = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.TemplateManifest",
                RelativePath = "CustomMissions/_modele/mission.json",
                Sha256 = "9439500FB79D571160E22B2884DE1662E73ED779641329A3C7AA5E737DA5946F",
                PreserveExisting = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.TemplateReadme",
                RelativePath = "CustomMissions/_modele/payload/Missions/MaMission/LISEZ_MOI.txt",
                Sha256 = "A48C1FFE82BDD37BD943CF259B7468AD4DF5D65F96096A6C5CD3269BAE834A03",
                PreserveExisting = true
            }
        };

        public static string ValidateOnly()
        {
            foreach (EmbeddedFile file in Files)
                ValidateFile(file, ReadResource(file));
            return "Missions personnalisees verifiees : gestionnaire, moteur du nouveau menu "
                + "et squelette embarques.";
        }

        public static string DetectStatus(string gamePath)
        {
            int ready = 0;
            foreach (EmbeddedFile file in Files)
            {
                string target = InstallerCore.SafeGameTarget(gamePath, file.RelativePath);
                if (!File.Exists(target)) continue;
                if (file.Executable)
                {
                    try
                    {
                        ValidateFile(file, File.ReadAllBytes(target));
                        ready++;
                    }
                    catch (InvalidDataException) { }
                }
                else if (String.Equals(
                    CmpInstaller.ComputeSha256(target), file.Sha256,
                    StringComparison.OrdinalIgnoreCase))
                    ready++;
            }
            bool menuReady = MenuRuntimeFiles.All(relative => {
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                return File.Exists(target) && new FileInfo(target).Length > 0;
            });
            if (menuReady)
            {
                string report = InstallerCore.SafeGameTarget(
                    gamePath, "CUSTOM_MISSIONS_INSTALL.json");
                try
                {
                    menuReady = File.ReadAllText(report, Encoding.UTF8).Contains(
                        "CUSTOM_MISSIONS_INSTALLED_THREE_LIST_GUI_GAME_NOT_LAUNCHED");
                    if (menuReady)
                        ValidateMenuModule(File.ReadAllBytes(InstallerCore.SafeGameTarget(
                            gamePath, "Scripts/HD2.CustomMenu.asi")));
                }
                catch { menuReady = false; }
            }
            if (ready == Files.Length && menuReady)
                return "installe, nouveau menu actif dans le jeu";
            if (ready == Files.Length)
                return "gestionnaire installe, nouveau menu absent";
            if (ready == 0 && !menuReady) return "a installer";
            return "partiel (" + ready + "/" + Files.Length
                + " fichiers du gestionnaire; menu "
                + (menuReady ? "actif" : "absent") + ")";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(
                progress, "Installation du gestionnaire de missions personnalisees...");
            foreach (EmbeddedFile file in Files)
            {
                byte[] content = ReadResource(file);
                ValidateFile(file, content);
                string relative = file.RelativePath.Replace(
                    '/', Path.DirectorySeparatorChar);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                bool tracked = prepared.Contains(relative);
                if (file.PreserveExisting && File.Exists(target) && !tracked)
                {
                    InstallerCore.Report(
                        progress, "Fichier CustomMissions existant conserve : "
                            + file.RelativePath);
                    continue;
                }

                InstallerCore.PrepareTarget(
                    gamePath, relative, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, content);
                    ValidateFile(file, File.ReadAllBytes(temporary));
                    File.Copy(temporary, target, true);
                    journal.RecordHash(
                        relative, CmpInstaller.ComputeSha256(target));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
            }
            InstallerCore.Report(
                progress, "Gestionnaire installe; missions utilisateur conservees.");
        }

        public static void ActivateMenu(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(
                progress, "Installation du nouveau menu de missions dans le jeu...");
            string manager = InstallerCore.SafeGameTarget(
                gamePath, "HD2-Custom-Mission-Manager.exe");
            ValidateFile(Files[0], File.ReadAllBytes(manager));

            List<string> outputs = new List<string>(MenuRuntimeFiles);
            string textRoot = InstallerCore.SafeGameTarget(gamePath, "Text");
            if (!Directory.Exists(textRoot))
                throw new DirectoryNotFoundException(
                    "Dossier Text du jeu introuvable; le nouveau menu ne peut pas etre installe.");
            foreach (string language in Directory.GetDirectories(textRoot))
            {
                string table = Path.Combine(language, "TEXTY_DD.txt");
                if (!File.Exists(table)) continue;
                outputs.Add(Path.GetFullPath(table).Substring(
                    Path.GetFullPath(gamePath).TrimEnd(
                        Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar).Length)
                    .TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));
            }

            foreach (string relative in outputs)
            {
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                InstallerCore.PrepareTarget(
                    gamePath, relative, target, journal, prepared);
            }

            HashSet<string> priorBackups = BackupFiles(gamePath);
            string emptyLibrary = Path.Combine(
                Path.GetTempPath(), "HD2-Heritage-empty-menu-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(emptyLibrary);
            try
            {
                RunManager(manager, "--integrate", emptyLibrary, gamePath, gamePath);
            }
            finally
            {
                if (Directory.Exists(emptyLibrary)) Directory.Delete(emptyLibrary, true);
            }

            foreach (string relative in BackupFiles(gamePath))
                if (!priorBackups.Contains(relative) && prepared.Add(relative))
                    journal.RecordCreated(relative);

            foreach (string relative in outputs.Concat(BackupFiles(gamePath)).Distinct(
                StringComparer.OrdinalIgnoreCase))
            {
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                if (!File.Exists(target))
                    throw new InvalidDataException(
                        "Le nouveau menu n'a pas produit le fichier attendu : " + relative);
                journal.RecordHash(relative, CmpInstaller.ComputeSha256(target));
            }
            ValidateMenuModule(File.ReadAllBytes(InstallerCore.SafeGameTarget(
                gamePath, "Scripts/HD2.CustomMenu.asi")));
            string report = File.ReadAllText(InstallerCore.SafeGameTarget(
                gamePath, "CUSTOM_MISSIONS_INSTALL.json"), Encoding.UTF8);
            if (!report.Contains(
                "CUSTOM_MISSIONS_INSTALLED_THREE_LIST_GUI_GAME_NOT_LAUNCHED"))
                throw new InvalidDataException(
                    "Le gestionnaire n'a pas confirme l'installation du nouveau menu.");
            InstallerCore.Report(
                progress, "Nouveau menu de missions installe dans H&D2 (trois categories).");
        }

        private static HashSet<string> BackupFiles(string gamePath)
        {
            HashSet<string> result = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            string root = InstallerCore.SafeGameTarget(gamePath, "STATIC_MENU_BACKUP");
            if (!Directory.Exists(root)) return result;
            string game = Path.GetFullPath(gamePath).TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            foreach (string path in Directory.GetFiles(root, "*", SearchOption.AllDirectories))
                result.Add(Path.GetFullPath(path).Substring(game.Length));
            return result;
        }

        private static void RunManager(
            string manager, params string[] arguments)
        {
            ProcessStartInfo start = new ProcessStartInfo {
                FileName = manager,
                Arguments = String.Join(" ", arguments.Select(QuoteArgument)),
                WorkingDirectory = Path.GetDirectoryName(manager),
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };
            using (Process process = Process.Start(start))
            {
                if (process == null)
                    throw new InvalidOperationException(
                        "Impossible de demarrer le gestionnaire du nouveau menu.");
                StringBuilder output = new StringBuilder();
                StringBuilder error = new StringBuilder();
                process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs data) {
                    if (data.Data != null) output.AppendLine(data.Data);
                };
                process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs data) {
                    if (data.Data != null) error.AppendLine(data.Data);
                };
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                if (!process.WaitForExit(120000))
                {
                    try { process.Kill(); }
                    catch { }
                    throw new TimeoutException(
                        "Le gestionnaire du nouveau menu n'a pas repondu dans les deux minutes.");
                }
                process.WaitForExit();
                if (process.ExitCode != 0)
                    throw new InvalidOperationException(
                        "Installation du nouveau menu impossible. "
                        + (error.Length == 0 ? output : error).ToString().Trim());
            }
        }

        private static string QuoteArgument(string value)
        {
            if (value.IndexOf('"') >= 0)
                throw new InvalidDataException("Argument de chemin invalide.");
            return "\"" + value + "\"";
        }

        private static void ValidateMenuModule(byte[] content)
        {
            if (content == null || content.Length < 4096
                || content[0] != (byte)'M' || content[1] != (byte)'Z')
                throw new InvalidDataException("Module du nouveau menu absent ou invalide.");
            int peOffset = BitConverter.ToInt32(content, 0x3C);
            if (peOffset < 0x40 || peOffset > content.Length - 6
                || content[peOffset] != (byte)'P'
                || content[peOffset + 1] != (byte)'E'
                || content[peOffset + 2] != 0
                || content[peOffset + 3] != 0
                || BitConverter.ToUInt16(content, peOffset + 4) != 0x014C)
                throw new InvalidDataException(
                    "Module du nouveau menu invalide ou non x86.");
        }

        private static byte[] ReadResource(EmbeddedFile file)
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(file.ResourceName))
            {
                if (stream == null)
                    throw new InvalidDataException(
                        "Ressource du gestionnaire introuvable : " + file.ResourceName);
                using (MemoryStream memory = new MemoryStream())
                {
                    stream.CopyTo(memory);
                    return memory.ToArray();
                }
            }
        }

        private static void ValidateFile(EmbeddedFile file, byte[] content)
        {
            if (file.Executable)
            {
                ValidateExecutable(content);
                string expected = ReadManagerHash();
                string actual = ComputeSha256(content);
                if (!String.Equals(actual, expected,
                    StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "Empreinte invalide pour le gestionnaire de missions.");
                return;
            }
            string skeletonHash = ComputeSha256(content);
            if (!String.Equals(skeletonHash, file.Sha256,
                StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Empreinte invalide dans le squelette CustomMissions : "
                        + file.RelativePath);
        }

        private static string ReadManagerHash()
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(ManagerHashResource))
            {
                if (stream == null)
                    throw new InvalidDataException(
                        "Empreinte embarquee du gestionnaire introuvable.");
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.ASCII, false))
                {
                    string expected = reader.ReadToEnd().Trim();
                    if (expected.Length != 64)
                        throw new InvalidDataException(
                            "Empreinte embarquee du gestionnaire invalide.");
                    for (int index = 0; index < expected.Length; index++)
                        if (!Uri.IsHexDigit(expected[index]))
                            throw new InvalidDataException(
                                "Empreinte embarquee du gestionnaire invalide.");
                    return expected;
                }
            }
        }

        private static string ComputeSha256(byte[] content)
        {
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(
                    sha.ComputeHash(content)).Replace("-", "");
        }

        private static void ValidateExecutable(byte[] content)
        {
            if (content == null || content.Length < 65536
                || content[0] != (byte)'M' || content[1] != (byte)'Z')
                throw new InvalidDataException(
                    "Executable du gestionnaire absent ou invalide.");
            int peOffset = BitConverter.ToInt32(content, 0x3C);
            if (peOffset < 0x40 || peOffset > content.Length - 26
                || content[peOffset] != (byte)'P'
                || content[peOffset + 1] != (byte)'E'
                || content[peOffset + 2] != 0
                || content[peOffset + 3] != 0
                || BitConverter.ToUInt16(content, peOffset + 4) != 0x014C
                || BitConverter.ToUInt16(content, peOffset + 24) != 0x010B)
                throw new InvalidDataException(
                    "Executable Windows x86 du gestionnaire invalide.");
        }
    }
}
