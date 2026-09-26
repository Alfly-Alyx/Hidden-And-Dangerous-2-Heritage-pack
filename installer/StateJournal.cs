using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace HD2CommunityInstaller
{
    internal sealed class FileChange
    {
        public bool WasCreated;
        public string RelativePath;
        public string InstalledSha256;
    }

    internal sealed class ProfileUnlockChange
    {
        public string RelativePath;
        public byte[] OriginalBase;
        public byte[] OriginalSabre;
        public string InstalledSha256;
    }

    internal sealed class DiagnosticWerChange
    {
        public string RegistryView;
        public string Executable;
    }

    internal sealed class InstallState
    {
        public string GamePath;
        public string BackupRoot;
        public bool HostsChanged;
        public bool NetworkBridgeInstalled;
        public bool DirectPlayEnabledByInstaller;
        public string CmpVersion;
        public string CmpCommit;
        public string CmpSha256;
        public long CmpArchiveBytes;
        public byte[] OriginalGraphics;
        public byte[] InstalledGraphics;
        public string GraphicsProfile;
        public readonly List<FileChange> Changes = new List<FileChange>();
        public readonly List<ProfileUnlockChange> ProfileUnlocks =
            new List<ProfileUnlockChange>();
        public readonly List<DiagnosticWerChange> DiagnosticWerKeys =
            new List<DiagnosticWerChange>();

        public static InstallState Load()
        {
            if (!File.Exists(AppConfig.StateFile))
                return null;

            InstallState state = new InstallState();
            Dictionary<string, FileChange> byPath = new Dictionary<string, FileChange>(
                StringComparer.OrdinalIgnoreCase);
            foreach (string line in File.ReadAllLines(AppConfig.StateFile, Encoding.UTF8))
            {
                string[] fields = line.Split('\t');
                if (fields.Length < 2)
                    continue;
                if (fields[0] == "GAME")
                    state.GamePath = Decode(fields[1]);
                else if (fields[0] == "BACKUP")
                    state.BackupRoot = Decode(fields[1]);
                else if (fields[0] == "HOSTS")
                    state.HostsChanged = fields[1] == "1";
                else if (fields[0] == "NETWORK_BRIDGE")
                    state.NetworkBridgeInstalled = fields[1] == "1";
                else if (fields[0] == "DIRECTPLAY")
                    state.DirectPlayEnabledByInstaller = fields[1] == "1";
                else if (fields[0] == "CMP" && fields.Length >= 3)
                {
                    state.CmpVersion = fields[1];
                    state.CmpCommit = fields[2];
                    if (fields.Length >= 4) state.CmpSha256 = fields[3];
                    long archiveBytes;
                    if (fields.Length >= 5
                        && Int64.TryParse(fields[4], out archiveBytes))
                        state.CmpArchiveBytes = archiveBytes;
                }
                else if (fields[0] == "GRAPHICS" && fields.Length >= 4)
                {
                    if (state.OriginalGraphics == null)
                        state.OriginalGraphics = Convert.FromBase64String(fields[1]);
                    state.InstalledGraphics = Convert.FromBase64String(fields[2]);
                    state.GraphicsProfile = Decode(fields[3]);
                }
                else if (fields[0] == "PROFILE_UNLOCK" && fields.Length >= 5)
                {
                    state.ProfileUnlocks.Add(new ProfileUnlockChange {
                        RelativePath = NormalizeRelativePath(Decode(fields[1])),
                        OriginalBase = Convert.FromBase64String(fields[2]),
                        OriginalSabre = Convert.FromBase64String(fields[3]),
                        InstalledSha256 = fields[4]
                    });
                }
                else if (fields[0] == "DIAGNOSTIC_WER" && fields.Length >= 3)
                {
                    state.DiagnosticWerKeys.Add(new DiagnosticWerChange {
                        RegistryView = fields[1],
                        Executable = Decode(fields[2])
                    });
                }
                else if (fields[0] == "CREATED" || fields[0] == "REPLACED")
                {
                    string relative = NormalizeRelativePath(Decode(fields[1]));
                    if (IsExternalReleaseGuide(relative)) continue;
                    FileChange change = new FileChange {
                        WasCreated = fields[0] == "CREATED",
                        RelativePath = relative
                    };
                    state.Changes.Add(change);
                    byPath[change.RelativePath] = change;
                }
                else if (fields[0] == "HASH" && fields.Length >= 3)
                {
                    string relative = NormalizeRelativePath(Decode(fields[1]));
                    if (IsExternalReleaseGuide(relative)) continue;
                    FileChange change;
                    if (byPath.TryGetValue(relative, out change))
                        change.InstalledSha256 = fields[2];
                }
            }
            if (String.IsNullOrWhiteSpace(state.GamePath) || String.IsNullOrWhiteSpace(state.BackupRoot))
                throw new InvalidDataException("Le journal d'installation est incomplet.");
            return state;
        }

        internal static string NormalizeRelativePath(string value)
        {
            return value == null ? null : value
                .Replace(Path.AltDirectorySeparatorChar, Path.DirectorySeparatorChar)
                .Replace('/', Path.DirectorySeparatorChar)
                .Replace('\\', Path.DirectorySeparatorChar);
        }

        internal static bool IsExternalReleaseGuide(string relativePath)
        {
            string relative = NormalizeRelativePath(relativePath);
            return String.Equals(relative,
                    @"Guides\HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf",
                    StringComparison.OrdinalIgnoreCase)
                || String.Equals(relative,
                    @"Guides\HD2-Rapport-des-Decouvertes.pdf",
                    StringComparison.OrdinalIgnoreCase)
                || String.Equals(relative,
                    @"Guides\HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf",
                    StringComparison.OrdinalIgnoreCase)
                || String.Equals(relative,
                    @"Guides\HD2-Discovery-Report-EN.pdf",
                    StringComparison.OrdinalIgnoreCase);
        }

        internal static string Encode(string value)
        {
            return Convert.ToBase64String(Encoding.UTF8.GetBytes(value));
        }

        internal static string Decode(string value)
        {
            return Encoding.UTF8.GetString(Convert.FromBase64String(value));
        }
    }

    internal sealed class StateJournal : IDisposable
    {
        private readonly StreamWriter writer;
        public readonly InstallState State;

        private StateJournal(StreamWriter writer, InstallState state)
        {
            this.writer = writer;
            State = state;
        }

        public static StateJournal OpenExisting(string gamePath)
        {
            InstallState state = InstallState.Load();
            if (state == null)
                throw new InvalidOperationException("Journal de restauration introuvable.");
            string requested = Path.GetFullPath(gamePath)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            string recorded = Path.GetFullPath(state.GamePath)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            if (!String.Equals(requested, recorded, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException(
                    "Le journal existant appartient a une autre installation du jeu.");
            StreamWriter writer = new StreamWriter(
                AppConfig.StateFile, true, new UTF8Encoding(false));
            writer.AutoFlush = true;
            writer.WriteLine("UPDATE\t" + AppConfig.Version + "\t" + DateTime.UtcNow.ToString("u"));
            return new StateJournal(writer, state);
        }
        public static StateJournal Create(string gamePath)
        {
            if (File.Exists(AppConfig.StateFile))
                throw new InvalidOperationException(
                    "Une installation ou une restauration precedente existe deja. Utilisez d'abord Restaurer.");

            Directory.CreateDirectory(AppConfig.DataRoot);
            string backup = Path.Combine(
                AppConfig.DataRoot,
                "backup-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss"));
            Directory.CreateDirectory(backup);

            StreamWriter writer = new StreamWriter(
                AppConfig.StateFile, false, new UTF8Encoding(false));
            writer.AutoFlush = true;
            InstallState state = new InstallState {
                GamePath = Path.GetFullPath(gamePath),
                BackupRoot = backup
            };
            writer.WriteLine("FORMAT\t1");
            writer.WriteLine("GAME\t" + InstallState.Encode(state.GamePath));
            writer.WriteLine("BACKUP\t" + InstallState.Encode(state.BackupRoot));
            return new StateJournal(writer, state);
        }

        public void RecordCreated(string relativePath)
        {
            relativePath = InstallState.NormalizeRelativePath(relativePath);
            writer.WriteLine("CREATED\t" + InstallState.Encode(relativePath));
            State.Changes.Add(new FileChange { WasCreated = true, RelativePath = relativePath });
        }

        public void RecordReplacement(string relativePath)
        {
            relativePath = InstallState.NormalizeRelativePath(relativePath);
            writer.WriteLine("REPLACED\t" + InstallState.Encode(relativePath));
            State.Changes.Add(new FileChange { WasCreated = false, RelativePath = relativePath });
        }

        public void RecordHash(string relativePath, string sha256)
        {
            relativePath = InstallState.NormalizeRelativePath(relativePath);
            writer.WriteLine(
                "HASH\t" + InstallState.Encode(relativePath) + "\t" + sha256);
            for (int index = State.Changes.Count - 1; index >= 0; index--)
            {
                if (String.Equals(
                    State.Changes[index].RelativePath,
                    relativePath,
                    StringComparison.OrdinalIgnoreCase))
                {
                    State.Changes[index].InstalledSha256 = sha256;
                    break;
                }
            }
        }

        public void RecordProfileUnlock(
            string relativePath, byte[] originalBase, byte[] originalSabre,
            string installedSha256)
        {
            relativePath = InstallState.NormalizeRelativePath(relativePath);
            writer.WriteLine("PROFILE_UNLOCK\t" + InstallState.Encode(relativePath)
                + "\t" + Convert.ToBase64String(originalBase)
                + "\t" + Convert.ToBase64String(originalSabre)
                + "\t" + installedSha256);
            State.ProfileUnlocks.Add(new ProfileUnlockChange {
                RelativePath = relativePath,
                OriginalBase = (byte[])originalBase.Clone(),
                OriginalSabre = (byte[])originalSabre.Clone(),
                InstalledSha256 = installedSha256
            });
        }

        public void RecordGraphics(byte[] original, byte[] installed, string profile)
        {
            if (State.OriginalGraphics == null)
                State.OriginalGraphics = (byte[])original.Clone();
            State.InstalledGraphics = (byte[])installed.Clone();
            State.GraphicsProfile = profile;
            writer.WriteLine("GRAPHICS\t"
                + Convert.ToBase64String(State.OriginalGraphics) + "\t"
                + Convert.ToBase64String(State.InstalledGraphics) + "\t"
                + InstallState.Encode(profile));
        }

        public void RecordDiagnosticWerKey(string registryView, string executable)
        {
            writer.WriteLine("DIAGNOSTIC_WER\t" + registryView + "\t"
                + InstallState.Encode(executable));
            State.DiagnosticWerKeys.Add(new DiagnosticWerChange {
                RegistryView = registryView,
                Executable = executable
            });
        }

        public void RecordHostsChanged()
        {
            writer.WriteLine("HOSTS\t1");
            State.HostsChanged = true;
        }

        public void RecordNetworkBridgeInstalled()
        {
            if (State.NetworkBridgeInstalled) return;
            writer.WriteLine("NETWORK_BRIDGE\t1");
            State.NetworkBridgeInstalled = true;
        }

        public void RecordCmpPackage(
            string version, string commit, string sha256, long archiveBytes)
        {
            writer.WriteLine("CMP\t" + version + "\t" + commit + "\t"
                + sha256 + "\t" + archiveBytes);
            State.CmpVersion = version;
            State.CmpCommit = commit;
            State.CmpSha256 = sha256;
            State.CmpArchiveBytes = archiveBytes;
        }

        public void RecordDirectPlayEnabled()
        {
            writer.WriteLine("DIRECTPLAY\t1");
            State.DirectPlayEnabledByInstaller = true;
        }

        public int SealMissingHashes(string gamePath)
        {
            int sealedCount = 0;
            foreach (FileChange change in State.Changes)
            {
                if (!String.IsNullOrWhiteSpace(change.InstalledSha256))
                    continue;
                string target = InstallerCore.SafeGameTarget(
                    gamePath, change.RelativePath);
                if (!File.Exists(target))
                    throw new FileNotFoundException(
                        "Fichier suivi absent avant scellement du journal.", target);
                RecordHash(
                    change.RelativePath, CmpInstaller.ComputeSha256(target));
                sealedCount++;
            }
            return sealedCount;
        }

        public void Dispose()
        {
            writer.Dispose();
        }
    }
}
