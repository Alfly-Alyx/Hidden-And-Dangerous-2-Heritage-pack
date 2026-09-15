using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal sealed class PackageFile
    {
        public ZipArchiveEntry Entry;
        public string RelativePath;
        public string TargetPath;
    }

    internal static class CmpInstaller
    {
        public static string ValidateOnly(string archivePath, string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);
            VerifySha256(archivePath, AppConfig.CmpSha256);
            Encoding ansi = Encoding.GetEncoding(1252);
            using (ZipArchive archive = ZipFile.OpenRead(archivePath))
            {
                List<PackageFile> files = ValidatePackage(archive, gamePath);
                ZipArchiveEntry mapEntry = null;
                foreach (PackageFile file in files)
                    if (String.Equals(file.RelativePath, "cmp_info/cmp_Maplist.txt",
                        StringComparison.OrdinalIgnoreCase))
                    {
                        mapEntry = file.Entry;
                        break;
                    }
                if (mapEntry == null)
                    throw new InvalidDataException("Liste CMP introuvable.");
                string cmpText;
                using (StreamReader reader = new StreamReader(
                    mapEntry.Open(), ansi, false))
                    cmpText = reader.ReadToEnd();
                string original = File.ReadAllText(
                    Path.Combine(gamePath, "mpmaplist.txt"), ansi);
                string result = ExperimentalContentInstaller.AddVestiges(
                    MergeCooperativeSection(original, cmpText));
                if (!Regex.IsMatch(result,
                    @"dir\s*=\s*""NORMANDY3_MP_ZONE""",
                    RegexOptions.IgnoreCase)
                    || !Regex.IsMatch(result,
                        @"dir\s*=\s*""AFRIKA5_MP""", RegexOptions.IgnoreCase))
                    throw new InvalidDataException("Activation experimentale absente.");
                int maps = Regex.Matches(cmpText, @"<MAP\b",
                    RegexOptions.IgnoreCase).Count;
                int testedFlags = 0;
                foreach (PackageFile file in files)
                {
                    if (!IsMissionTree(file.RelativePath)) continue;
                    byte[] tree = ReadZipEntry(file.Entry);
                    TreePatchStats stats = TreeKlzPatcher.Patch(tree);
                    if (stats.ChangedItems == 0) continue;
                    if (TreeKlzPatcher.Audit(tree).ChangedItems != 0)
                        throw new InvalidDataException(
                            "Validation exploration CMP impossible : " + file.RelativePath);
                    testedFlags = stats.ChangedItems;
                    break;
                }
                if (testedFlags == 0)
                    throw new InvalidDataException(
                        "Aucune limite de zone testable trouvee dans le CMP.");
                return "Archive CMP valide: " + archive.Entries.Count
                    + " entrees, " + files.Count + " fichiers installables, "
                    + maps + " cartes, 2 vestiges actifs, test exploration "
                    + testedFlags + " limites neutralisees.";
            }
        }

        public static void Install(
            InstallOptions options, StateJournal journal, HashSet<string> prepared,
            Action<string> progress, Action<int> percent)
        {
            EnsureSpace(options.GamePath, options.PackageOverride);
            InstallerCore.Report(progress,
                "Preparation du Community Map Package " + AppConfig.CmpVersion + "...");
            string package = Acquire(options.PackageOverride, progress, percent);
            InstallerCore.Report(progress, "Verification SHA-256 du paquet...");
            VerifySha256(package, AppConfig.CmpSha256);
            InstallerCore.SetPercent(percent, 35);
            InstallArchive(package, options.GamePath, journal, prepared,
                options.FreeExploration, progress, percent);
            if (String.IsNullOrWhiteSpace(options.PackageOverride))
                try { File.Delete(package); } catch { }
        }

        private static void InstallArchive(
            string archivePath, string gamePath, StateJournal journal,
            HashSet<string> prepared, bool patchTrees,
            Action<string> progress, Action<int> percent)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            using (ZipArchive archive = ZipFile.OpenRead(archivePath))
            {
                List<PackageFile> files = ValidatePackage(archive, gamePath);
                int completed = 0;
                int patchedTrees = 0;
                long neutralizedFlags = 0;
                long removedBoundaries = 0;
                foreach (PackageFile file in files)
                {
                    string relative = file.RelativePath.Replace('/', Path.DirectorySeparatorChar);
                    InstallerCore.PrepareTarget(
                        gamePath, relative, file.TargetPath, journal, prepared);
                    Directory.CreateDirectory(Path.GetDirectoryName(file.TargetPath));
                    string temporary = file.TargetPath + ".hd2pack.tmp";
                    try
                    {
                        using (FileStream output = new FileStream(
                            temporary, FileMode.Create, FileAccess.Write, FileShare.None,
                            131072, FileOptions.SequentialScan))
                        {
                            if (patchTrees && IsMissionTree(relative))
                            {
                                byte[] data = ReadZipEntry(file.Entry);
                                TreePatchStats stats = TreeKlzPatcher.Patch(data);
                                TreePatchStats after = TreeKlzPatcher.Audit(data);
                                if (after.ChangedItems != 0)
                                    throw new InvalidDataException(
                                        "Limites de zone restantes dans " + relative + ".");
                                output.Write(data, 0, data.Length);
                                if (stats.ChangedItems > 0)
                                {
                                    patchedTrees++;
                                    neutralizedFlags += stats.ChangedRecords;
                                    removedBoundaries += stats.BoundaryLabels;
                                }
                            }
                            else
                            {
                                using (Stream input = file.Entry.Open())
                                    input.CopyTo(output, 131072);
                            }
                        }
                        string installedHash = ComputeSha256(temporary);
                        File.Copy(temporary, file.TargetPath, true);
                        journal.RecordHash(relative, installedHash);
                    }
                    finally
                    {
                        if (File.Exists(temporary)) File.Delete(temporary);
                    }
                    completed++;
                    if (completed % 100 == 0 || completed == files.Count)
                    {
                        InstallerCore.SetPercent(percent,
                            35 + (int)(55L * completed / Math.Max(1, files.Count)));
                        if (progress != null)
                            progress("Installation CMP : " + completed + " / "
                                + files.Count + " fichiers");
                    }
                }

                string cmpListPath = Path.Combine(gamePath, "cmp_info", "cmp_Maplist.txt");
                string cmpText = File.ReadAllText(cmpListPath, ansi);
                int mapCount = Regex.Matches(cmpText, @"<MAP\b", RegexOptions.IgnoreCase).Count;
                if (mapCount < 100
                    || !Regex.IsMatch(cmpText,
                        @"<GAMESTYLE\s+type=""cooperative""", RegexOptions.IgnoreCase)
                    || cmpText.IndexOf("</GAMESTYLE>", StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException("La liste CMP est incomplete ou invalide.");

                string relativeMapList = "mpmaplist.txt";
                string rootMapList = Path.Combine(gamePath, relativeMapList);
                InstallerCore.PrepareTarget(
                    gamePath, relativeMapList, rootMapList, journal, prepared);
                string original = File.Exists(rootMapList)
                    ? File.ReadAllText(rootMapList, ansi)
                    : "<MAP_LIST>\r\n</MAP_LIST>\r\n";
                string merged = MergeCooperativeSection(original, cmpText);
                merged = ExperimentalContentInstaller.AddVestiges(merged);
                WriteTextAtomically(rootMapList, merged, ansi);
                journal.RecordHash(relativeMapList, ComputeSha256(rootMapList));
                InstallerCore.Log("CMP installe : " + files.Count
                    + " fichiers, " + mapCount + " cartes; 2 vestiges actifs; "
                    + patchedTrees + " arbres corriges et " + neutralizedFlags
                    + " drapeaux et " + removedBoundaries + " murs de limite retires.");
                if (patchTrees)
                    InstallerCore.Report(progress, "Exploration libre communautaire activee sur "
                        + patchedTrees + " cartes (" + neutralizedFlags + " drapeaux et "
                        + removedBoundaries + " murs de limite retires).");
            }
        }

        private static string MergeCooperativeSection(string original, string cmp)
        {
            Regex section = new Regex(
                @"<GAMESTYLE\s+type=""cooperative""[\s\S]*?</GAMESTYLE>",
                RegexOptions.IgnoreCase);
            if (section.IsMatch(original))
                return section.Replace(
                    original, delegate(Match ignored) { return cmp.Trim(); }, 1);
            if (!Regex.IsMatch(original, @"</MAP_LIST>", RegexOptions.IgnoreCase))
                throw new InvalidDataException("La liste multijoueur racine est invalide.");
            return Regex.Replace(
                original, @"</MAP_LIST>", cmp.Trim() + "\r\n</MAP_LIST>",
                RegexOptions.IgnoreCase);
        }

        private static string AddNormandy3Zone(string mapList)
        {
            if (Regex.IsMatch(mapList,
                @"dir\s*=\s*""NORMANDY3_MP_ZONE""", RegexOptions.IgnoreCase))
                return mapList;

            Regex teamplay = new Regex(
                @"<GAMESTYLE\s+type=""teamplay""[\s\S]*?</GAMESTYLE>",
                RegexOptions.IgnoreCase);
            Match section = teamplay.Match(mapList);
            if (!section.Success)
                throw new InvalidDataException("Section Occupation/teamplay introuvable.");

            Regex templatePattern = new Regex(
                @"<MAP\s+name=""Normandy3""\s+dir=""Normandy3_mp""[\s\S]*?</MAP>",
                RegexOptions.IgnoreCase);
            Match template = templatePattern.Match(section.Value);
            if (!template.Success)
                throw new InvalidDataException("Modele officiel Normandy3 introuvable.");

            string restored = Regex.Replace(
                template.Value, @"name=""Normandy3""",
                "name=\"" + ExperimentalContentInstaller.NormandyPrototypeName + "\"",
                RegexOptions.IgnoreCase);
            restored = Regex.Replace(
                restored, @"dir=""Normandy3_mp""",
                "dir=\"NORMANDY3_MP_ZONE\"",
                RegexOptions.IgnoreCase);
            string updatedSection = section.Value.Replace(
                "</GAMESTYLE>",
                "        <!-- Restored official vestige; listed in the Sabre Squadron server manual. -->\r\n"
                + restored + "\r\n    </GAMESTYLE>");
            return mapList.Substring(0, section.Index)
                + updatedSection
                + mapList.Substring(section.Index + section.Length);
        }

        private static bool IsMissionTree(string relative)
        {
            string value = relative.Replace((char)92, '/');
            return value.StartsWith("Missions/", StringComparison.OrdinalIgnoreCase)
                && value.EndsWith("/tree.klz", StringComparison.OrdinalIgnoreCase);
        }

        private static byte[] ReadZipEntry(ZipArchiveEntry entry)
        {
            if (entry.Length < 0 || entry.Length > Int32.MaxValue)
                throw new InvalidDataException("Fichier CMP trop grand : " + entry.FullName);
            using (Stream input = entry.Open())
            using (MemoryStream buffer = new MemoryStream((int)entry.Length))
            {
                input.CopyTo(buffer, 131072);
                if (buffer.Length != entry.Length)
                    throw new InvalidDataException("Fichier CMP tronque : " + entry.FullName);
                return buffer.ToArray();
            }
        }

        private static List<PackageFile> ValidatePackage(
            ZipArchive archive, string gamePath)
        {
            if (archive.Entries.Count != 23600)
                throw new InvalidDataException(
                    "Nombre d'entrees CMP inattendu : " + archive.Entries.Count + ".");
            List<PackageFile> files = new List<PackageFile>();
            HashSet<string> duplicates = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            string root = null;
            bool foundMapList = false;
            foreach (ZipArchiveEntry entry in archive.Entries)
            {
                string normalized = entry.FullName.Replace('\\', '/');
                string[] pieces = normalized.Split(
                    new[] { '/' }, StringSplitOptions.RemoveEmptyEntries);
                if (pieces.Length == 0) continue;
                if (root == null) root = pieces[0];
                if (!String.Equals(root, pieces[0], StringComparison.Ordinal))
                    throw new InvalidDataException("Le paquet contient plusieurs racines.");
                if (pieces.Length == 1 || normalized.EndsWith("/")) continue;
                foreach (string piece in pieces)
                    if (piece == "." || piece == "..")
                        throw new InvalidDataException(
                            "Chemin CMP non sur : " + normalized);

                string relative = String.Join("/", pieces, 1, pieces.Length - 1);
                string top = pieces[1];
                if (String.Equals(top, "cmp_optional", StringComparison.OrdinalIgnoreCase))
                    continue;
                if (pieces.Length == 2
                    && String.Equals(top, "README.md", StringComparison.OrdinalIgnoreCase))
                    relative = "cmp_info/README.md";
                else if (!AppConfig.CmpRoots.Contains(top))
                    throw new InvalidDataException("Dossier CMP inattendu : " + top);
                if (relative.IndexOf(':') >= 0)
                    throw new InvalidDataException("Chemin CMP non sur : " + relative);
                if (!duplicates.Add(relative))
                    throw new InvalidDataException("Chemin CMP duplique : " + relative);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                files.Add(new PackageFile {
                    Entry = entry, RelativePath = relative, TargetPath = target
                });
                if (String.Equals(relative, "cmp_info/cmp_Maplist.txt",
                    StringComparison.OrdinalIgnoreCase)) foundMapList = true;
            }
            if (String.IsNullOrWhiteSpace(root)
                || !root.StartsWith("had2-cmp-", StringComparison.OrdinalIgnoreCase)
                || !foundMapList)
                throw new InvalidDataException("Structure CMP non reconnue.");
            return files;
        }

        private static string Acquire(
            string packageOverride, Action<string> progress, Action<int> percent)
        {
            if (!String.IsNullOrWhiteSpace(packageOverride))
            {
                string local = Path.GetFullPath(packageOverride);
                if (!File.Exists(local))
                    throw new FileNotFoundException("Archive CMP locale introuvable.", local);
                return local;
            }

            string downloads = Path.Combine(AppConfig.DataRoot, "downloads");
            Directory.CreateDirectory(downloads);
            string target = Path.Combine(
                downloads, "had2-cmp-" + AppConfig.CmpVersion + ".zip");
            if (File.Exists(target))
                try
                {
                    VerifySha256(target, AppConfig.CmpSha256);
                    return target;
                }
                catch { File.Delete(target); }

            string temporary = target + ".partial";
            if (File.Exists(temporary)) File.Delete(temporary);
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
            using (WebClient client = new WebClient())
            {
                client.Headers.Add(HttpRequestHeader.UserAgent,
                    "HD2-Community-Installer/" + AppConfig.Version);
                int last = -1;
                client.DownloadProgressChanged += delegate(
                    object sender, DownloadProgressChangedEventArgs args)
                {
                    int value = 10 + (int)(25L * args.BytesReceived
                        / Math.Max(1L, args.TotalBytesToReceive));
                    InstallerCore.SetPercent(percent, value);
                    int whole = args.ProgressPercentage;
                    if (whole != last)
                    {
                        last = whole;
                        if (progress != null) progress(
                            "Telechargement CMP : " + whole + "% ("
                            + FormatBytes(args.BytesReceived) + ")");
                    }
                };
                try { client.DownloadFile(new Uri(AppConfig.CmpUrl), temporary); }
                catch
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                    throw;
                }
            }
            File.Move(temporary, target);
            return target;
        }

        private static void EnsureSpace(string gamePath, string packageOverride)
        {
            long gameFree = new DriveInfo(Path.GetPathRoot(gamePath)).AvailableFreeSpace;
            if (gameFree < AppConfig.CmpExpandedBytes + 1024L * 1024 * 1024)
                throw new IOException(
                    "Espace insuffisant sur le disque du jeu (minimum : 4,2 Go libres).");
            if (String.IsNullOrWhiteSpace(packageOverride))
            {
                long dataFree = new DriveInfo(
                    Path.GetPathRoot(AppConfig.DataRoot)).AvailableFreeSpace;
                if (dataFree < AppConfig.CmpArchiveBytes + 256L * 1024 * 1024)
                    throw new IOException(
                        "Espace insuffisant pour l'archive CMP (minimum : 1,3 Go libres).");
            }
        }

        private static void VerifySha256(string path, string expected)
        {
            string actual = ComputeSha256(path);
            if (!String.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Empreinte SHA-256 incorrecte. Attendue " + expected
                    + ", obtenue " + actual + ".");
        }

        internal static string ComputeSha256(string path)
        {
            using (SHA256 sha = SHA256.Create())
            using (FileStream stream = new FileStream(
                path, FileMode.Open, FileAccess.Read, FileShare.Read,
                1048576, FileOptions.SequentialScan))
                return BytesToHex(sha.ComputeHash(stream));
        }

        private static string BytesToHex(byte[] bytes)
        {
            StringBuilder value = new StringBuilder(bytes.Length * 2);
            foreach (byte item in bytes) value.Append(item.ToString("X2"));
            return value.ToString();
        }

        private static void WriteTextAtomically(
            string path, string content, Encoding encoding)
        {
            string temporary = path + ".hd2pack.tmp";
            try
            {
                File.WriteAllText(temporary, content, encoding);
                File.Copy(temporary, path, true);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }

        private static string FormatBytes(long value)
        {
            if (value < 0) return "?";
            double amount = value;
            string[] units = { "o", "Kio", "Mio", "Gio" };
            int unit = 0;
            while (amount >= 1024 && unit < units.Length - 1)
            {
                amount /= 1024;
                unit++;
            }
            return amount.ToString("0.0") + " " + units[unit];
        }
    }
}
