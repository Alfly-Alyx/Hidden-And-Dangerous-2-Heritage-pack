using System;
using System.Collections.Generic;
using System.IO;

namespace HD2CommunityInstaller
{
    internal sealed class OfficialTreeSource
    {
        public string ArchivePath;
        public int EntryIndex;
        public string RelativePath;
    }

    internal static class OfficialContentInstaller
    {
        private static readonly string[] ArchiveNames = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            List<OfficialTreeSource> sources = Discover(gamePath);
            int filesWithLimits = 0;
            long records = 0;
            long flags = 0;
            long boundaries = 0;
            foreach (string archivePath in ArchivePaths(gamePath))
            {
                using (DtaArchive archive = new DtaArchive(archivePath))
                {
                    foreach (OfficialTreeSource source in sources)
                    {
                        if (!String.Equals(source.ArchivePath, archivePath,
                            StringComparison.OrdinalIgnoreCase)) continue;
                        byte[] data = archive.Read(archive.Entries[source.EntryIndex]);
                        TreePatchStats stats = TreeKlzPatcher.Patch(data);
                        TreePatchStats after = TreeKlzPatcher.Audit(data);
                        if (after.ChangedItems != 0)
                            throw new InvalidDataException(
                                "Des limites subsistent dans " + source.RelativePath + ".");
                        records += stats.Records;
                        flags += stats.ChangedRecords;
                        boundaries += stats.BoundaryLabels;
                        if (stats.ChangedItems > 0) filesWithLimits++;
                    }
                }
            }
            return sources.Count + " arbres officiels finaux verifies, "
                + filesWithLimits + " avec limites, " + flags
                + " drapeaux de zone et " + boundaries + " objets de mur neutralisables sur "
                + records + " collisions.";
        }
        public static string DetectStatus(string gamePath)
        {
            try
            {
                List<OfficialTreeSource> sources = Discover(gamePath);
                int ready = 0;
                foreach (string archivePath in ArchivePaths(gamePath))
                {
                    using (DtaArchive archive = new DtaArchive(archivePath))
                    {
                        foreach (OfficialTreeSource source in sources)
                        {
                            if (!String.Equals(source.ArchivePath, archivePath,
                                StringComparison.OrdinalIgnoreCase)) continue;
                            string target = InstallerCore.SafeGameTarget(
                                gamePath, source.RelativePath);
                            byte[] data = File.Exists(target)
                                ? File.ReadAllBytes(target)
                                : archive.Read(archive.Entries[source.EntryIndex]);
                            if (TreeKlzPatcher.Audit(data).ChangedItems == 0) ready++;
                        }
                    }
                }
                bool warningsDisabled =
                    Arctic1FreeExplorationInstaller.IsActive(gamePath);
                int looseTotal;
                int looseReady;
                CountAdditionalLooseTrees(
                    gamePath, sources, out looseTotal, out looseReady);
                if (ready == sources.Count && looseReady == looseTotal
                    && warningsDisabled)
                    return "deja active (" + ready
                        + " cartes officielles, " + looseReady
                        + " autres arbres libres et avertissements Arctic 1 verifies)";
                if (ready > 0 || looseReady > 0 || warningsDisabled)
                    return "partielle (" + ready + "/" + sources.Count
                        + " cartes officielles; " + looseReady + "/" + looseTotal
                        + " autres arbres libres; avertissements Arctic 1 : "
                        + (warningsDisabled ? "neutralises" : "a neutraliser") + ")";
                return "a activer";
            }
            catch (Exception ex)
            {
                return "indeterminee (" + ex.Message + ")";
            }
        }
        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress, Action<int> percent)
        {
            EnsureSpace(gamePath);
            InstallerCore.Report(progress,
                "Preparation de l'exploration libre des missions officielles...");
            List<OfficialTreeSource> sources = Discover(gamePath);
            int completed = 0;
            int written = 0;
            long flags = 0;
            long boundaries = 0;

            foreach (string archivePath in ArchivePaths(gamePath))
            {
                using (DtaArchive archive = new DtaArchive(archivePath))
                {
                    foreach (OfficialTreeSource source in sources)
                    {
                        if (!String.Equals(source.ArchivePath, archivePath,
                            StringComparison.OrdinalIgnoreCase)) continue;
                        string relative = source.RelativePath.Replace(
                            '/', Path.DirectorySeparatorChar);
                        string target = InstallerCore.SafeGameTarget(gamePath, relative);
                        byte[] data = File.Exists(target)
                            ? File.ReadAllBytes(target)
                            : archive.Read(archive.Entries[source.EntryIndex]);
                        TreePatchStats stats = TreeKlzPatcher.Patch(data);
                        flags += stats.ChangedRecords;
                        boundaries += stats.BoundaryLabels;
                        if (stats.ChangedItems > 0)
                        {
                            InstallerCore.PrepareTarget(
                                gamePath, relative, target, journal, prepared);
                            Directory.CreateDirectory(Path.GetDirectoryName(target));
                            string temporary = target + ".hd2pack.tmp";
                            try
                            {
                                File.WriteAllBytes(temporary, data);
                                File.Copy(temporary, target, true);
                                journal.RecordHash(
                                    relative, CmpInstaller.ComputeSha256(temporary));
                            }
                            finally
                            {
                                if (File.Exists(temporary)) File.Delete(temporary);
                            }
                            written++;
                        }
                        completed++;
                        if (completed % 10 == 0 || completed == sources.Count)
                        {
                            InstallerCore.SetPercent(
                                percent, 10 + (int)(20L * completed / Math.Max(1, sources.Count)));
                            if (progress != null)
                                progress("Exploration officielle : " + completed + " / "
                                    + sources.Count + " cartes analysees");
                        }
                    }
                }
            }
            InstallerCore.Log("Exploration libre officielle : " + written
                + " fichiers crees ou corriges, " + flags + " drapeaux et "
                + boundaries + " objets de limite neutralises.");
            InstallerCore.Report(progress, "Exploration libre officielle activee sur "
                + written + " cartes (" + flags + " drapeaux et " + boundaries
                + " murs de limite retires).");
        }
        public static void PatchLooseMissionTrees(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            string gameRoot = Path.GetFullPath(gamePath)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            string missionsRoot = Path.Combine(gameRoot, "Missions");
            if (!Directory.Exists(missionsRoot)) return;

            int written = 0;
            long flags = 0;
            long boundaries = 0;
            foreach (string tree in Directory.GetFiles(
                missionsRoot, "tree.klz", SearchOption.AllDirectories))
            {
                string target = Path.GetFullPath(tree);
                if (!target.StartsWith(gameRoot, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Arbre de mission hors du dossier du jeu.");
                byte[] data = File.ReadAllBytes(target);
                TreePatchStats stats = TreeKlzPatcher.Patch(data);
                if (stats.ChangedItems == 0) continue;
                string relative = target.Substring(gameRoot.Length);
                InstallerCore.PrepareTarget(gamePath, relative, target, journal, prepared);
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, data);
                    File.Copy(temporary, target, true);
                    journal.RecordHash(relative, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                written++;
                flags += stats.ChangedRecords;
                boundaries += stats.BoundaryLabels;
            }
            if (written > 0)
                InstallerCore.Report(progress, "Exploration libre : " + written
                    + " cartes deja installees corrigees (" + flags + " drapeaux, "
                    + boundaries + " murs de limite).");
        }

        private static List<OfficialTreeSource> Discover(string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);
            Dictionary<string, OfficialTreeSource> selected =
                new Dictionary<string, OfficialTreeSource>(StringComparer.OrdinalIgnoreCase);
            foreach (string archivePath in ArchivePaths(gamePath))
            {
                using (DtaArchive archive = new DtaArchive(archivePath))
                {
                    foreach (DtaEntry entry in archive.Entries)
                    {
                        string relative;
                        if (!TryNormalizeTreePath(entry.Name, out relative)) continue;
                        InstallerCore.SafeGameTarget(gamePath, relative);
                        selected[relative] = new OfficialTreeSource {
                            ArchivePath = archivePath,
                            EntryIndex = entry.Index,
                            RelativePath = relative
                        };
                    }
                }
            }
            List<OfficialTreeSource> result = new List<OfficialTreeSource>(selected.Values);
            result.Sort(delegate(OfficialTreeSource left, OfficialTreeSource right) {
                int archive = StringComparer.OrdinalIgnoreCase.Compare(
                    left.ArchivePath, right.ArchivePath);
                return archive != 0 ? archive : StringComparer.OrdinalIgnoreCase.Compare(
                    left.RelativePath, right.RelativePath);
            });
            if (result.Count < 70)
                throw new InvalidDataException(
                    "Inventaire officiel incomplet : " + result.Count + " arbres tree.klz.");
            return result;
        }

        private static void CountAdditionalLooseTrees(
            string gamePath, IList<OfficialTreeSource> officialSources,
            out int total, out int ready)
        {
            total = 0;
            ready = 0;
            HashSet<string> official = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            foreach (OfficialTreeSource source in officialSources)
                official.Add(source.RelativePath.Replace((char)92, '/'));

            string gameRoot = Path.GetFullPath(gamePath)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            string missionsRoot = Path.Combine(gameRoot, "Missions");
            if (!Directory.Exists(missionsRoot)) return;
            foreach (string tree in Directory.GetFiles(
                missionsRoot, "tree.klz", SearchOption.AllDirectories))
            {
                string target = Path.GetFullPath(tree);
                if (!target.StartsWith(gameRoot, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "Arbre libre hors du dossier du jeu.");
                string relative = target.Substring(gameRoot.Length)
                    .Replace((char)92, '/');
                if (official.Contains(relative)) continue;
                total++;
                if (TreeKlzPatcher.Audit(File.ReadAllBytes(target)).ChangedItems == 0)
                    ready++;
            }
        }

        private static bool TryNormalizeTreePath(string raw, out string relative)
        {
            relative = null;
            if (String.IsNullOrWhiteSpace(raw) || raw.IndexOf(':') >= 0) return false;
            string value = raw.Replace((char)92, '/').TrimStart('/');
            string[] pieces = value.Split(new[] { '/' }, StringSplitOptions.RemoveEmptyEntries);
            if (pieces.Length < 3
                || !String.Equals(pieces[0], "Missions", StringComparison.OrdinalIgnoreCase)
                || !String.Equals(pieces[pieces.Length - 1], "tree.klz",
                    StringComparison.OrdinalIgnoreCase))
                return false;
            foreach (string piece in pieces)
                if (piece == "." || piece == "..") return false;
            relative = String.Join("/", pieces);
            return true;
        }

        private static List<string> ArchivePaths(string gamePath)
        {
            List<string> paths = new List<string>();
            foreach (string name in ArchiveNames)
            {
                string path = Path.Combine(gamePath, name);
                if (!File.Exists(path))
                    throw new FileNotFoundException("Archive officielle manquante.", path);
                paths.Add(path);
            }
            return paths;
        }

        private static void EnsureSpace(string gamePath)
        {
            long free = new DriveInfo(Path.GetPathRoot(gamePath)).AvailableFreeSpace;
            if (free < 1024L * 1024 * 1024)
                throw new IOException(
                    "Espace insuffisant pour l'exploration libre (minimum : 1 Go libre).");
        }
    }
}
