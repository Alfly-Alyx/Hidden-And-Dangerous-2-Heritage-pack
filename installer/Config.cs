using System;
using System.Collections.Generic;
using System.IO;

namespace HD2CommunityInstaller
{
    internal static class AppConfig
    {
        public const string ProductName = "H&D2 Heritage Pack";
        private const string DataFolderName = "HD2 Community Pack";
        public const string Version = "0.8.0";
        public const string ExpectedGameVersion = "1.12";
        public const string CmpVersion = "2.6.5";
        public const string CmpCommit = "793d979748b27a9924fccc30fa0fba6edb7cd70f";
        public const string CmpUrl = "https://codeload.github.com/ehylla93/had2-cmp/zip/" + CmpCommit;
        public const string CmpLatestCommitUrl =
            "https://api.github.com/repos/ehylla93/had2-cmp/commits/main";
        public const string CmpCodeloadBaseUrl =
            "https://codeload.github.com/ehylla93/had2-cmp/zip/";
        public const string CmpSha256 = "DD0CA6FED1FB056DCB064813C223E0423F1FD9B13E291D106D8B983C467ABC33";
        public const long CmpArchiveBytes = 1084146265L;
        public const long CmpExpandedBytes = 3118285955L;
        public const string MasterIp = "78.47.255.224";
        public const string OpenSpyMasterIp = "134.122.16.249";
        public const string LocalMasterIp = "127.0.0.1";
        public const int MasterPort = 28910;
        public const string MasterBridgeServiceName = "HD2HeritageMasterBridge";

        public static readonly string[] MasterAliases = {
            "hd2.available.gamespy.com",
            "hd2.master.gamespy.com",
            "hd2.ms14.gamespy.com"
        };

        public static string ExpectedIpForMasterAlias(string alias)
        {
            return String.Equals(alias, "hd2.ms14.gamespy.com",
                    StringComparison.OrdinalIgnoreCase)
                ? LocalMasterIp
                : MasterIp;
        }

        public static readonly HashSet<string> CmpRoots = new HashSet<string>(
            new[] { "Maps", "Missions", "Models", "Scripts", "Sounds", "Tables", "Text", "cmp_info" },
            StringComparer.OrdinalIgnoreCase);

        public static string DataRoot
        {
            get
            {
                return Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
                    DataFolderName);
            }
        }

        public static string StateFile { get { return Path.Combine(DataRoot, "state-v1.tsv"); } }
        public static string LogFile { get { return Path.Combine(DataRoot, "installer.log"); } }
        public static string MasterBridgePath
        {
            get { return Path.Combine(DataRoot, "HD2-Master-Bridge.exe"); }
        }
    }

    internal sealed class InstallOptions
    {
        public string GamePath;
        public bool ConfigureMasterServer = true;
        public bool EnableDirectPlay = true;
        public bool InstallCmp = true;
        public bool FreeExploration = true;
        public bool FixOptionalObjectives = true;
        public bool RestoreDormantSequences = true;
        public bool RestoreOfficialEasterEggs = true;
        public bool UnlockAllMissions = true;
        public bool AutoConfigureGraphics = true;
        public string PackageOverride;
    }
}

