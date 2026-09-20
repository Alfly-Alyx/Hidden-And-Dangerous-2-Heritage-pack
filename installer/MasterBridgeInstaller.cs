using Microsoft.Win32;
using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Security.Cryptography;
using System.ServiceProcess;
using System.Text;
using System.Threading;

namespace HD2CommunityInstaller
{
    internal static class MasterBridgeInstaller
    {
        private const string ExecutableResource =
            "HD2CommunityInstaller.MasterBridge.exe";
        private const string HashResource =
            "HD2CommunityInstaller.MasterBridge.sha256";

        public static string ValidateOnly()
        {
            byte[] executable = ReadResource(ExecutableResource);
            string expected = Encoding.ASCII.GetString(
                ReadResource(HashResource)).Trim();
            string actual = ComputeSha256(executable);
            if (!String.Equals(expected, actual, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "L'empreinte du pont de listes Internet est invalide.");
            return "Pont de listes H&D2 (service actuel + OpenSpy) verifie.";
        }

        public static void Install(StateJournal journal, Action<string> progress)
        {
            if (progress != null)
                progress("Installation de la liste fusionnee (service actuel + OpenSpy)...");
            byte[] executable = ReadResource(ExecutableResource);
            string expected = Encoding.ASCII.GetString(
                ReadResource(HashResource)).Trim();
            if (!String.Equals(expected, ComputeSha256(executable),
                    StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "L'empreinte du pont de listes Internet est invalide.");

            bool exists = ServiceExists();
            if (exists)
            {
                string configured = ConfiguredServicePath();
                if (!SamePath(configured, AppConfig.MasterBridgePath))
                    throw new InvalidOperationException(
                        "Le service Windows " + AppConfig.MasterBridgeServiceName
                        + " existe deja avec un autre executable.");
                StopService(false);
            }

            Directory.CreateDirectory(AppConfig.DataRoot);
            string temporary = AppConfig.MasterBridgePath + ".new";
            File.WriteAllBytes(temporary, executable);
            if (!String.Equals(expected, CmpInstaller.ComputeSha256(temporary),
                    StringComparison.OrdinalIgnoreCase))
            {
                File.Delete(temporary);
                throw new InvalidDataException(
                    "Le pont de listes Internet extrait est corrompu.");
            }
            if (File.Exists(AppConfig.MasterBridgePath))
                File.Replace(temporary, AppConfig.MasterBridgePath, null);
            else
                File.Move(temporary, AppConfig.MasterBridgePath);

            journal.RecordNetworkBridgeInstalled();
            if (!exists)
            {
                RunSc("create " + AppConfig.MasterBridgeServiceName
                    + " binPath= \"\\\"" + AppConfig.MasterBridgePath + "\\\"\""
                    + " start= auto DisplayName= \"H&D2 Heritage - listes Internet fusionnees\"",
                    true);
            }
            else
            {
                RunSc("config " + AppConfig.MasterBridgeServiceName
                    + " binPath= \"\\\"" + AppConfig.MasterBridgePath + "\\\"\""
                    + " start= auto", true);
            }
            RunSc("start " + AppConfig.MasterBridgeServiceName, true);
            WaitUntilRunning();
            if (!CanConnectLocal())
                throw new InvalidOperationException(
                    "Le pont des listes Internet a demarre mais son port local ne repond pas.");
        }

        public static void Uninstall(InstallState state, Action<string> progress)
        {
            if (!state.NetworkBridgeInstalled && !ServiceExists()) return;
            if (progress != null)
                progress("Retrait du pont des listes Internet...");
            if (ServiceExists())
            {
                string configured = ConfiguredServicePath();
                if (!SamePath(configured, AppConfig.MasterBridgePath))
                    throw new InvalidOperationException(
                        "Le service de listes H&D2 pointe vers un autre executable; "
                        + "la restauration est suspendue.");
                StopService(false);
                RunSc("delete " + AppConfig.MasterBridgeServiceName, true);
                WaitUntilDeleted();
            }
            if (File.Exists(AppConfig.MasterBridgePath))
                File.Delete(AppConfig.MasterBridgePath);
        }

        public static string DetectStatus()
        {
            if (!ServiceExists()) return "a installer";
            string configured = ConfiguredServicePath();
            if (!SamePath(configured, AppConfig.MasterBridgePath))
                return "conflit avec un service homonyme";
            if (!File.Exists(AppConfig.MasterBridgePath))
                return "incomplet (executable absent)";
            try
            {
                using (ServiceController controller = new ServiceController(
                    AppConfig.MasterBridgeServiceName))
                {
                    if (controller.Status != ServiceControllerStatus.Running)
                        return "installe mais arrete";
                }
            }
            catch (Exception error)
            {
                return "indetermine (" + error.Message + ")";
            }
            return "deja actif (service actuel + OpenSpy)";
        }

        private static byte[] ReadResource(string name)
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(name))
            {
                if (stream == null)
                    throw new InvalidDataException("Ressource integree absente : " + name);
                using (MemoryStream copy = new MemoryStream())
                {
                    stream.CopyTo(copy);
                    return copy.ToArray();
                }
            }
        }

        private static string ComputeSha256(byte[] data)
        {
            using (SHA256 hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(data)).Replace("-", "");
        }

        private static bool ServiceExists()
        {
            foreach (ServiceController service in ServiceController.GetServices())
            {
                try
                {
                    if (String.Equals(service.ServiceName,
                        AppConfig.MasterBridgeServiceName,
                        StringComparison.OrdinalIgnoreCase)) return true;
                }
                finally { service.Dispose(); }
            }
            return false;
        }

        private static string ConfiguredServicePath()
        {
            using (RegistryKey key = Registry.LocalMachine.OpenSubKey(
                @"SYSTEM\CurrentControlSet\Services\"
                + AppConfig.MasterBridgeServiceName))
            {
                if (key == null) return String.Empty;
                string image = key.GetValue("ImagePath") as string;
                if (String.IsNullOrWhiteSpace(image)) return String.Empty;
                image = Environment.ExpandEnvironmentVariables(image.Trim());
                if (image.StartsWith("\"", StringComparison.Ordinal))
                {
                    int end = image.IndexOf('\"', 1);
                    if (end > 1) image = image.Substring(1, end - 1);
                }
                return image.Trim();
            }
        }

        private static bool SamePath(string left, string right)
        {
            if (String.IsNullOrWhiteSpace(left)
                || String.IsNullOrWhiteSpace(right)) return false;
            try
            {
                return String.Equals(Path.GetFullPath(left), Path.GetFullPath(right),
                    StringComparison.OrdinalIgnoreCase);
            }
            catch { return false; }
        }

        private static void StopService(bool required)
        {
            if (!ServiceExists()) return;
            using (ServiceController controller = new ServiceController(
                AppConfig.MasterBridgeServiceName))
            {
                controller.Refresh();
                if (controller.Status == ServiceControllerStatus.Stopped) return;
                try
                {
                    if (controller.CanStop) controller.Stop();
                    controller.WaitForStatus(ServiceControllerStatus.Stopped,
                        TimeSpan.FromSeconds(10));
                }
                catch
                {
                    if (required) throw;
                    RunSc("stop " + AppConfig.MasterBridgeServiceName, false);
                    Thread.Sleep(500);
                }
            }
        }

        private static void WaitUntilRunning()
        {
            using (ServiceController controller = new ServiceController(
                AppConfig.MasterBridgeServiceName))
            {
                controller.WaitForStatus(ServiceControllerStatus.Running,
                    TimeSpan.FromSeconds(10));
            }
        }

        private static void WaitUntilDeleted()
        {
            DateTime limit = DateTime.UtcNow.AddSeconds(10);
            while (ServiceExists() && DateTime.UtcNow < limit)
                Thread.Sleep(200);
            if (ServiceExists())
                throw new InvalidOperationException(
                    "Le service des listes H&D2 n'a pas pu etre supprime.");
        }

        private static bool CanConnectLocal()
        {
            try
            {
                using (TcpClient client = new TcpClient())
                {
                    IAsyncResult pending = client.BeginConnect(
                        IPAddress.Loopback, AppConfig.MasterPort, null, null);
                    if (!pending.AsyncWaitHandle.WaitOne(1500)) return false;
                    client.EndConnect(pending);
                    return true;
                }
            }
            catch { return false; }
        }

        private static void RunSc(string arguments, bool required)
        {
            string executable = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.System), "sc.exe");
            ProcessStartInfo start = new ProcessStartInfo(executable, arguments) {
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };
            using (Process process = Process.Start(start))
            {
                string output = process.StandardOutput.ReadToEnd();
                string error = process.StandardError.ReadToEnd();
                process.WaitForExit();
                if (required && process.ExitCode != 0)
                    throw new InvalidOperationException(
                        "Echec du service Windows (" + process.ExitCode + ") : "
                        + output + " " + error);
            }
        }
    }
}
