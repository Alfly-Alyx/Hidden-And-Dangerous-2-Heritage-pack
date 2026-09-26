using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

namespace HD2HeritageDiagnostics
{
    internal sealed class CrashEventInfo
    {
        public long Index;
        public DateTime TimeUtc;
        public string Source;
        public long EventId;
        public string Message;
    }

    internal sealed class GameSession
    {
        public Process Process;
        public int Pid;
        public string Name;
        public string Executable;
        public DateTime StartedUtc;
        public DateTime LastResponsiveUtc;
        public DateTime? ExitObservedUtc;
        public int? ExitCode;
        public bool HangReported;
        public bool ModulesCaptured;
        public long GameLogOffset;
        public readonly List<string> Modules = new List<string>();
        public readonly HashSet<string> ErrorSignals =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    }

    internal static class ReportWriter
    {
        private const int MaximumReports = 30;
        private const int MaximumTailBytes = 262144;

        public static string DefaultRoot
        {
            get
            {
                return Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "HD2 Heritage Pack", "Reports");
            }
        }

        public static string Create(
            string gamePath, string reason, GameSession session,
            IList<CrashEventInfo> events, IList<string> dumps,
            string rootOverride)
        {
            string root = String.IsNullOrWhiteSpace(rootOverride)
                ? DefaultRoot : Path.GetFullPath(rootOverride);
            Directory.CreateDirectory(root);
            string executable = session == null || String.IsNullOrWhiteSpace(session.Name)
                ? "HD2" : SafeName(session.Name);
            int pid = session == null ? 0 : session.Pid;
            string prefix = DateTime.Now.ToString("yyyyMMdd-HHmmss-fff", CultureInfo.InvariantCulture)
                + "-" + executable + "-" + pid.ToString(CultureInfo.InvariantCulture);
            string folder = UniquePath(Path.Combine(root, prefix));
            Directory.CreateDirectory(folder);

            StringBuilder report = new StringBuilder();
            report.AppendLine("H&D2 Heritage Pack - rapport automatique");
            report.AppendLine("Format : 1");
            report.AppendLine("Moniteur : " + Assembly.GetExecutingAssembly().GetName().Version);
            report.AppendLine("Date locale : " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss zzz"));
            report.AppendLine("Date UTC : " + DateTime.UtcNow.ToString("u"));
            report.AppendLine("Motif : " + (reason ?? "Erreur H&D2 detectee"));
            report.AppendLine("Envoi reseau : aucun");
            report.AppendLine();
            report.AppendLine("SYSTEME");
            report.AppendLine("Windows : " + Environment.OSVersion);
            report.AppendLine("64 bits : " + Environment.Is64BitOperatingSystem);
            report.AppendLine("Processeurs logiques : " + Environment.ProcessorCount);
            report.AppendLine("CLR : " + Environment.Version);
            report.AppendLine();
            report.AppendLine("JEU");
            report.AppendLine("Dossier : " + gamePath);
            if (session != null)
            {
                report.AppendLine("Processus : " + session.Name);
                report.AppendLine("PID : " + session.Pid);
                report.AppendLine("Executable : " + session.Executable);
                report.AppendLine("Debut UTC : " + session.StartedUtc.ToString("u"));
                DateTime ended = session.ExitObservedUtc ?? DateTime.UtcNow;
                report.AppendLine("Duree : " + (ended - session.StartedUtc));
                if (session.ExitCode.HasValue)
                    report.AppendLine("Code de sortie : " + session.ExitCode.Value
                        + " (0x" + unchecked((uint)session.ExitCode.Value).ToString("X8") + ")");
            }
            AppendFileMetadata(report, Path.Combine(gamePath, "HD2_SabreSquadron.exe"));
            AppendFileMetadata(report, Path.Combine(gamePath, "HD2.exe"));
            AppendFileMetadata(report, Path.Combine(gamePath, "Scripts", "HD2.CustomMenu.asi"));
            AppendFileMetadata(report, Path.Combine(gamePath, "GameData", "Gamedata02.gdt"));
            AppendFileMetadata(report, Path.Combine(gamePath, "GameData", "Gamedata03.gdt"));
            AppendFileMetadata(report, Path.Combine(gamePath, "GameData", "Gamedata04.gdt"));
            AppendFileMetadata(report, Path.Combine(gamePath, "GameData", "Gamedata05.gdt"));

            report.AppendLine();
            report.AppendLine("EVENEMENTS WINDOWS");
            if (events == null || events.Count == 0) report.AppendLine("Aucun evenement correle.");
            else foreach (CrashEventInfo item in events)
            {
                report.AppendLine("[" + item.TimeUtc.ToString("u") + "] "
                    + item.Source + " / " + item.EventId);
                report.AppendLine(item.Message ?? String.Empty);
            }

            report.AppendLine();
            report.AppendLine("MINIDUMPS WINDOWS");
            if (dumps == null || dumps.Count == 0) report.AppendLine("Aucun minidump correle.");
            else foreach (string dump in dumps) report.AppendLine(dump);

            report.AppendLine();
            report.AppendLine("MODULES CHARGES");
            if (session == null || session.Modules.Count == 0)
                report.AppendLine("Indisponibles.");
            else foreach (string module in session.Modules) report.AppendLine(module);

            AppendProfileMetadata(report, gamePath);
            WriteText(Path.Combine(folder, "report.txt"), report.ToString());
            CopyTail(Path.Combine(gamePath, "log.txt"),
                Path.Combine(folder, "game-log.txt"));
            CopyTail(Path.Combine(gamePath, "HD2.CustomMenu.log"),
                Path.Combine(folder, "custom-menu-log.txt"));
            CopySmallFile(Path.Combine(gamePath, "CUSTOM_MISSIONS_INSTALL.json"), folder);
            CopySmallFile(Path.Combine(gamePath, "STATIC_MENU_MANAGED_FILES.json"), folder);

            string zip = folder + ".zip";
            ZipFile.CreateFromDirectory(folder, zip, CompressionLevel.Optimal, false);
            WriteText(Path.Combine(root, "latest-report.txt"), folder + Environment.NewLine);
            ApplyRetention(root);
            return folder;
        }

        private static void AppendFileMetadata(StringBuilder report, string path)
        {
            if (!File.Exists(path)) return;
            FileInfo file = new FileInfo(path);
            report.AppendLine("Fichier : " + path);
            report.AppendLine("  taille=" + file.Length + " date_utc="
                + file.LastWriteTimeUtc.ToString("u"));
            try
            {
                FileVersionInfo version = FileVersionInfo.GetVersionInfo(path);
                if (!String.IsNullOrWhiteSpace(version.FileVersion))
                    report.AppendLine("  version=" + version.FileVersion);
            }
            catch { }
            if (file.Length <= 33554432)
                try { report.AppendLine("  sha256=" + Sha256(path)); }
                catch { }
        }

        private static void AppendProfileMetadata(StringBuilder report, string gamePath)
        {
            report.AppendLine();
            report.AppendLine("PROFILS ET SAUVEGARDES (metadonnees uniquement)");
            string root = Path.Combine(gamePath, "PlayersProfiles");
            if (!Directory.Exists(root))
            {
                report.AppendLine("Dossier absent.");
                return;
            }
            try
            {
                foreach (FileInfo file in new DirectoryInfo(root).GetFiles("*", SearchOption.AllDirectories)
                    .OrderByDescending(item => item.LastWriteTimeUtc).Take(40))
                {
                    string relative = file.FullName.Substring(root.Length)
                        .TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
                    report.AppendLine(relative + " | " + file.Length + " | "
                        + file.LastWriteTimeUtc.ToString("u"));
                }
            }
            catch (Exception error) { report.AppendLine("Lecture impossible : " + error.Message); }
        }

        private static string Sha256(string path)
        {
            using (FileStream input = new FileStream(path, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete))
            using (SHA256 algorithm = SHA256.Create())
                return BitConverter.ToString(algorithm.ComputeHash(input)).Replace("-", String.Empty);
        }

        private static void CopyTail(string source, string target)
        {
            if (!File.Exists(source)) return;
            try
            {
                using (FileStream input = new FileStream(source, FileMode.Open, FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete))
                {
                    long start = Math.Max(0, input.Length - MaximumTailBytes);
                    input.Position = start;
                    byte[] data = new byte[(int)(input.Length - start)];
                    int total = 0;
                    while (total < data.Length)
                    {
                        int read = input.Read(data, total, data.Length - total);
                        if (read == 0) break;
                        total += read;
                    }
                    string text = Encoding.Default.GetString(data, 0, total);
                    if (start > 0) text = "[debut du journal tronque]\r\n" + text;
                    WriteText(target, text);
                }
            }
            catch (Exception error) { WriteText(target, "Lecture impossible : " + error); }
        }

        private static void CopySmallFile(string source, string folder)
        {
            try
            {
                FileInfo file = new FileInfo(source);
                if (file.Exists && file.Length <= 2097152)
                    File.Copy(source, Path.Combine(folder, file.Name), true);
            }
            catch { }
        }

        private static string UniquePath(string candidate)
        {
            if (!Directory.Exists(candidate) && !File.Exists(candidate)) return candidate;
            for (int index = 2; index < 1000; index++)
            {
                string path = candidate + "-" + index;
                if (!Directory.Exists(path) && !File.Exists(path)) return path;
            }
            return candidate + "-" + Guid.NewGuid().ToString("N");
        }

        private static string SafeName(string value)
        {
            foreach (char invalid in Path.GetInvalidFileNameChars()) value = value.Replace(invalid, '_');
            return value;
        }

        private static void ApplyRetention(string root)
        {
            try
            {
                DirectoryInfo directory = new DirectoryInfo(root);
                DirectoryInfo[] reports = directory.GetDirectories("20*-HD2*")
                    .OrderByDescending(item => item.CreationTimeUtc).ToArray();
                for (int index = MaximumReports; index < reports.Length; index++)
                    reports[index].Delete(true);
                FileInfo[] archives = directory.GetFiles("20*-HD2*.zip")
                    .OrderByDescending(item => item.CreationTimeUtc).ToArray();
                for (int index = MaximumReports; index < archives.Length; index++)
                    archives[index].Delete();
            }
            catch { }
        }

        private static void WriteText(string path, string text)
        {
            File.WriteAllText(path, text, new UTF8Encoding(false));
        }
    }

    internal static class Program
    {
        private const int VkShift = 0x10;
        private const int VkControl = 0x11;
        private const int VkF12 = 0x7B;
        private static readonly object EventLock = new object();
        private static readonly List<CrashEventInfo> Events = new List<CrashEventInfo>();
        private static readonly HashSet<long> ReportedEvents = new HashSet<long>();
        private static readonly HashSet<string> SeenDumps =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        private static long syntheticEventIndex;

        [DllImport("user32.dll")]
        private static extern short GetAsyncKeyState(int virtualKey);

        [DllImport("user32.dll")]
        private static extern bool MessageBeep(uint type);

        [STAThread]
        private static int Main(string[] args)
        {
            try
            {
                if (args.Length > 0 && args[0] == "--self-test") return SelfTest();
                if (args.Length > 2 && args[0] == "--report")
                {
                    Console.WriteLine(ReportWriter.Create(
                        Path.GetFullPath(args[1]), args[2], null,
                        new List<CrashEventInfo>(), new List<string>(), null));
                    return 0;
                }
                int watchedPid;
                if (args.Length == 3 && args[0] == "--watch-pid"
                    && Int32.TryParse(args[1], out watchedPid))
                    return Watch(watchedPid, Path.GetFullPath(args[2]));
                return 2;
            }
            catch (Exception error)
            {
                SafeLog(error.ToString());
                try { Console.Error.WriteLine(error); } catch { }
                return 1;
            }
        }

        private static int Watch(int watchedPid, string gamePath)
        {
            if (!Directory.Exists(gamePath)) return 3;
            bool created;
            string mutexName = "Local\\HD2HeritageDiagnostics_" + watchedPid + "_"
                + ShortHash(gamePath);
            using (Mutex mutex = new Mutex(true, mutexName, out created))
            {
                if (!created) return 0;
                Directory.CreateDirectory(ReportWriter.DefaultRoot);
                string dumpRoot = Path.Combine(ReportWriter.DefaultRoot, "CrashDumps");
                Directory.CreateDirectory(dumpRoot);
                foreach (string dump in Directory.GetFiles(dumpRoot, "*.dmp"))
                    SeenDumps.Add(DumpIdentity(dump));

                Process process;
                try { process = Process.GetProcessById(watchedPid); }
                catch { return 4; }
                string executable = String.Empty;
                try { executable = process.MainModule.FileName; } catch { }
                if (!String.IsNullOrWhiteSpace(executable)
                    && !String.Equals(Path.GetDirectoryName(executable), gamePath,
                        StringComparison.OrdinalIgnoreCase))
                {
                    process.Dispose();
                    return 5;
                }
                DateTime start;
                try { start = process.StartTime.ToUniversalTime(); }
                catch { start = DateTime.UtcNow; }
                GameSession session = new GameSession {
                    Process = process,
                    Pid = watchedPid,
                    Name = process.ProcessName,
                    Executable = executable,
                    StartedUtc = start,
                    LastResponsiveUtc = DateTime.UtcNow,
                    GameLogOffset = 0
                };
                SafeLog("Session liee au jeu : " + session.Name + " PID " + watchedPid);
                EventLog application = TrySubscribeEventLog();
                bool hotkeyDown = false;
                try
                {
                    while (true)
                    {
                        if (!session.ExitObservedUtc.HasValue)
                        {
                            DateTime now = DateTime.UtcNow;
                            PollRunningSession(session, gamePath, now);
                            if (HasExited(session))
                            {
                                session.ExitObservedUtc = now;
                                try { session.ExitCode = session.Process.ExitCode; } catch { }
                            }
                        }
                        if (session.ExitObservedUtc.HasValue
                            && DateTime.UtcNow - session.ExitObservedUtc.Value
                                >= TimeSpan.FromSeconds(8))
                        {
                            CompleteSession(session, gamePath);
                            return 0;
                        }

                        bool pressed = !session.ExitObservedUtc.HasValue
                            && KeyDown(VkControl) && KeyDown(VkShift) && KeyDown(VkF12);
                        if (pressed && !hotkeyDown)
                        {
                            CreateReport(gamePath,
                                "Signalement manuel pendant la mission (Ctrl+Maj+F12)",
                                session, false);
                            MessageBeep(0x40);
                        }
                        hotkeyDown = pressed;
                        Thread.Sleep(200);
                    }
                }
                finally
                {
                    if (application != null) application.Dispose();
                    process.Dispose();
                }
            }
        }

        private static EventLog TrySubscribeEventLog()
        {
            try
            {
                EventLog log = new EventLog("Application");
                log.EntryWritten += delegate(object sender, EntryWrittenEventArgs args)
                {
                    try
                    {
                        EventLogEntry entry = args.Entry;
                        string message = entry.Message ?? String.Empty;
                        if (!MentionsGame(message)) return;
                        CrashEventInfo item = new CrashEventInfo {
                            Index = entry.Index,
                            TimeUtc = entry.TimeGenerated.ToUniversalTime(),
                            Source = entry.Source,
                            EventId = entry.InstanceId,
                            Message = message
                        };
                        lock (EventLock) Events.Add(item);
                    }
                    catch { }
                };
                log.EnableRaisingEvents = true;
                return log;
            }
            catch (Exception error)
            {
                SafeLog("Journal Windows indisponible : " + error.Message);
                return null;
            }
        }

        private static void PollRunningSession(
            GameSession session, string gamePath, DateTime now)
        {
            if (!session.ModulesCaptured && now - session.StartedUtc > TimeSpan.FromSeconds(3))
                CaptureModules(session);
            try
            {
                session.Process.Refresh();
                if (session.Process.MainWindowHandle == IntPtr.Zero || session.Process.Responding)
                    session.LastResponsiveUtc = now;
                else if (!session.HangReported
                    && now - session.LastResponsiveUtc >= TimeSpan.FromSeconds(20))
                {
                    session.HangReported = true;
                    CreateReport(gamePath, "Jeu bloque ou ne repondant plus depuis 20 secondes",
                        session, false);
                }
            }
            catch { }

            foreach (string signal in ReadNewErrorSignals(session, gamePath))
                if (session.ErrorSignals.Add(signal))
                    CreateReport(gamePath, "Erreur signalee par le journal du jeu : " + signal,
                        session, false);
        }

        private static IEnumerable<string> ReadNewErrorSignals(
            GameSession session, string gamePath)
        {
            List<string> found = new List<string>();
            string path = Path.Combine(gamePath, "log.txt");
            try
            {
                using (FileStream input = new FileStream(path, FileMode.Open, FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete))
                {
                    if (input.Length < session.GameLogOffset) session.GameLogOffset = 0;
                    input.Position = session.GameLogOffset;
                    using (StreamReader reader = new StreamReader(input, Encoding.Default, true, 4096, true))
                    {
                        string line;
                        while ((line = reader.ReadLine()) != null)
                            if (IsErrorSignal(line)) found.Add(line.Trim());
                    }
                    session.GameLogOffset = input.Position;
                }
            }
            catch { }
            return found;
        }

        internal static bool IsErrorSignal(string line)
        {
            if (String.IsNullOrWhiteSpace(line)) return false;
            string lower = line.ToLowerInvariant();
            if (lower.Contains("eax unified was not found")) return false;
            return lower.Contains("fatal error") || lower.Contains("script error")
                || lower.Contains("exception") || lower.Contains("assertion failed")
                || lower.Contains("cannot load") || lower.Contains("unable to load")
                || lower.Contains("failed to load") || lower.Contains("invalid opcode")
                || lower.StartsWith("error:") || lower.Contains("[error]");
        }

        private static void CaptureModules(GameSession session)
        {
            session.ModulesCaptured = true;
            try
            {
                foreach (ProcessModule module in session.Process.Modules)
                {
                    string version = String.Empty;
                    try { version = FileVersionInfo.GetVersionInfo(module.FileName).FileVersion; }
                    catch { }
                    session.Modules.Add(module.ModuleName + " | " + version + " | " + module.FileName);
                }
            }
            catch (Exception error) { session.Modules.Add("Lecture impossible : " + error.Message); }
        }

        private static void CompleteSession(GameSession session, string gamePath)
        {
            int reportedSignalCount = session.ErrorSignals.Count;
            foreach (string signal in ReadNewErrorSignals(session, gamePath))
                session.ErrorSignals.Add(signal);
            List<CrashEventInfo> events = CorrelatedEvents(session);
            List<string> dumps = NewDumps(session);
            bool error = session.ExitCode.HasValue && session.ExitCode.Value != 0;
            bool loggedError = session.ErrorSignals.Count > reportedSignalCount;
            if (error || events.Count > 0 || dumps.Count > 0 || loggedError)
            {
                string reason = error
                    ? "Arret anormal du jeu, code " + session.ExitCode.Value
                    : events.Count > 0 ? "Erreur Windows associee au jeu"
                    : dumps.Count > 0 ? "Minidump Windows cree pour le jeu"
                    : "Erreur signalee par le journal du jeu : "
                        + session.ErrorSignals.First();
                CreateReport(gamePath, reason, session, true, events, dumps);
            }
            SafeLog("Session terminee : " + session.Name + " PID " + session.Pid
                + " code " + (session.ExitCode.HasValue ? session.ExitCode.Value.ToString() : "inconnu"));
        }

        private static void CreateReport(
            string gamePath, string reason, GameSession session, bool correlate,
            IList<CrashEventInfo> eventOverride = null, IList<string> dumpOverride = null)
        {
            try
            {
                IList<CrashEventInfo> events = eventOverride
                    ?? (correlate ? CorrelatedEvents(session) : new List<CrashEventInfo>());
                IList<string> dumps = dumpOverride
                    ?? (correlate ? NewDumps(session) : new List<string>());
                string path = ReportWriter.Create(gamePath, reason, session, events, dumps, null);
                SafeLog("Rapport cree : " + path);
            }
            catch (Exception error) { SafeLog("Echec du rapport : " + error); }
        }

        private static List<CrashEventInfo> CorrelatedEvents(GameSession session)
        {
            DateTime end = (session.ExitObservedUtc ?? DateTime.UtcNow).AddSeconds(20);
            DateTime start = session.StartedUtc.AddSeconds(-5);
            lock (EventLock)
            {
                List<CrashEventInfo> result = Events.Where(item =>
                    item.TimeUtc >= start && item.TimeUtc <= end
                    && !ReportedEvents.Contains(item.Index)).ToList();
                foreach (CrashEventInfo item in result) ReportedEvents.Add(item.Index);
                return result;
            }
        }

        private static List<string> NewDumps(GameSession session)
        {
            List<string> result = new List<string>();
            string root = Path.Combine(ReportWriter.DefaultRoot, "CrashDumps");
            if (!Directory.Exists(root)) return result;
            foreach (string path in Directory.GetFiles(root, "*.dmp"))
            {
                string identity = DumpIdentity(path);
                if (SeenDumps.Contains(identity)) continue;
                FileInfo file = new FileInfo(path);
                if (file.LastWriteTimeUtc >= session.StartedUtc.AddSeconds(-5)
                    && (file.Name.IndexOf(session.Name, StringComparison.OrdinalIgnoreCase) >= 0
                        || file.Name.IndexOf("HD2", StringComparison.OrdinalIgnoreCase) >= 0))
                {
                    result.Add(path);
                    SeenDumps.Add(identity);
                }
            }
            return result;
        }

        private static bool HasExited(GameSession session)
        {
            try { return session.Process.HasExited; }
            catch { return true; }
        }

        private static bool MentionsGame(string value)
        {
            return value.IndexOf("HD2_SabreSquadron.exe", StringComparison.OrdinalIgnoreCase) >= 0
                || value.IndexOf("HD2.exe", StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private static bool KeyDown(int key)
        {
            return (GetAsyncKeyState(key) & 0x8000) != 0;
        }

        private static string DumpIdentity(string path)
        {
            FileInfo file = new FileInfo(path);
            return file.FullName + "|" + file.Length + "|" + file.LastWriteTimeUtc.Ticks;
        }

        private static string ShortHash(string value)
        {
            using (SHA256 hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(
                    Encoding.UTF8.GetBytes(value.ToUpperInvariant())))
                    .Replace("-", String.Empty).Substring(0, 16);
        }

        private static void SafeLog(string value)
        {
            try
            {
                Directory.CreateDirectory(ReportWriter.DefaultRoot);
                File.AppendAllText(Path.Combine(ReportWriter.DefaultRoot, "monitor.log"),
                    DateTime.UtcNow.ToString("u") + " " + value + Environment.NewLine,
                    new UTF8Encoding(false));
            }
            catch { }
        }

        private static int SelfTest()
        {
            string root = Path.Combine(Path.GetTempPath(),
                "HD2-Heritage-Diagnostics-Test-" + Guid.NewGuid().ToString("N"));
            string game = Path.Combine(root, "game");
            string reports = Path.Combine(root, "reports");
            Directory.CreateDirectory(game);
            try
            {
                File.WriteAllText(Path.Combine(game, "log.txt"),
                    "LS3D Engine\r\nScript error: test controlled\r\n", Encoding.Default);
                File.WriteAllText(Path.Combine(game, "HD2.CustomMenu.log"),
                    "view=3\r\n", Encoding.ASCII);
                File.WriteAllText(Path.Combine(game, "CUSTOM_MISSIONS_INSTALL.json"),
                    "{\"missions\":11}", Encoding.UTF8);
                GameSession session = new GameSession {
                    Pid = 1234,
                    Name = "HD2_SabreSquadron",
                    StartedUtc = DateTime.UtcNow.AddMinutes(-1),
                    ExitObservedUtc = DateTime.UtcNow,
                    ExitCode = unchecked((int)0xC0000005)
                };
                CrashEventInfo crash = new CrashEventInfo {
                    Index = ++syntheticEventIndex,
                    TimeUtc = DateTime.UtcNow,
                    Source = "Application Error",
                    EventId = 1000,
                    Message = "HD2_SabreSquadron.exe controlled test"
                };
                string report = ReportWriter.Create(game, "Autotest", session,
                    new[] { crash }, new string[0], reports);
                string text = File.ReadAllText(Path.Combine(report, "report.txt"), Encoding.UTF8);
                if (!text.Contains("Autotest") || !text.Contains("0xC0000005")
                    || !File.Exists(Path.Combine(report, "game-log.txt"))
                    || !File.Exists(report + ".zip")) return 10;
                if (!IsErrorSignal("Script error: controlled")
                    || IsErrorSignal("EAX Unified was not found. Trying normal DirectSound")) return 11;
                Console.WriteLine("Autotests du moniteur de diagnostics reussis.");
                return 0;
            }
            finally
            {
                try { if (Directory.Exists(root)) Directory.Delete(root, true); } catch { }
            }
        }
    }
}
