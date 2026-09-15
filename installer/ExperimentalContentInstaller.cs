using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class ExperimentalContentInstaller
    {
        private const string AfricaSourcePrefix = "Missions/Africa5_MP/";
        private const string AfricaPrototypePrefix = "Missions/AFRIKA5_MP/";
        private const string NormandySourcePrefix = "Missions/NORMANDY3_MP/";
        private const string NormandyPrototypePrefix = "Missions/NORMANDY3_MP_ZONE/";
        private const string AfricaScriptSourcePrefix = "Scripts/AFRICA5_MP/";
        private const string AfricaScriptTargetPrefix = "Scripts/AFRIKA5_MP/";

        private static readonly string[] NormandyBaseFiles = {
            "map.4ds", "tree.klz", "scene.4ds", "loader.4ds", "volumy.bin"
        };

        private static readonly string[] AfricaBaseFiles = {
            "map.4ds", "check2.bin", "loader.4ds", "mpscripts.dta",
            "sounds.bin", "Vertanim.bin"
        };

        internal const string NormandyPrototypeName =
            "PROTOTYPE - Normandy3 Zone (exploration libre)";
        internal const string AfricaPrototypeName =
            "PROTOTYPE - Africa5 (exploration libre)";

        public static string ValidateOnly(string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);
            string missionsPath = Path.Combine(gamePath, "missions.dta");
            int africaOwn;
            int africaCopies;
            int normandyOwn;
            int normandyCopies;
            using (DtaArchive archive = new DtaArchive(missionsPath))
            {
                Dictionary<string, DtaEntry> africaSource =
                    DirectFiles(archive, AfricaSourcePrefix);
                Dictionary<string, DtaEntry> africaPrototype =
                    DirectFiles(archive, AfricaPrototypePrefix);
                List<DtaEntry> africaMissing = MissingFiles(africaSource, africaPrototype);
                ValidateAfricaInventory(africaSource, africaPrototype, africaMissing);
                africaOwn = africaPrototype.Count;
                africaCopies = africaMissing.Count;

                Dictionary<string, DtaEntry> normandySource =
                    DirectFiles(archive, NormandySourcePrefix);
                Dictionary<string, DtaEntry> normandyPrototype =
                    DirectFiles(archive, NormandyPrototypePrefix);
                List<DtaEntry> normandyBase = NormandyComplements(
                    normandySource, normandyPrototype);
                ValidateNormandyInventory(
                    normandySource, normandyPrototype, normandyBase);
                normandyOwn = normandyPrototype.Count;
                normandyCopies = normandyBase.Count;
            }

            int scripts = ValidateAfricaScripts(gamePath);
            string original = File.ReadAllText(
                Path.Combine(gamePath, "mpmaplist.txt"), Encoding.GetEncoding(1252));
            string merged = AddVestiges(original);
            if (!ContainsDir(merged, "NORMANDY3_MP_ZONE")
                || !ContainsDir(merged, "AFRIKA5_MP")
                || merged.IndexOf(NormandyPrototypeName,
                    StringComparison.OrdinalIgnoreCase) < 0
                || merged.IndexOf(AfricaPrototypeName,
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException("Activation des vestiges incomplete.");
            return "Prototypes verifies : Normandy3 Zone " + normandyOwn
                + " fichiers propres + " + normandyCopies + " bases recuperables; Africa5 "
                + africaOwn + " fichiers propres + " + africaCopies
                + " bases recuperables + " + scripts + " scripts recuperables.";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Completion des deux cartes prototypes officielles...");
            int written = 0;
            string missionsPath = Path.Combine(gamePath, "missions.dta");
            using (DtaArchive archive = new DtaArchive(missionsPath))
            {
                Dictionary<string, DtaEntry> africaSource =
                    DirectFiles(archive, AfricaSourcePrefix);
                Dictionary<string, DtaEntry> africaPrototype =
                    DirectFiles(archive, AfricaPrototypePrefix);
                List<DtaEntry> africaMissing = MissingFiles(africaSource, africaPrototype);
                ValidateAfricaInventory(africaSource, africaPrototype, africaMissing);
                written += InstallEntries(archive, africaMissing, AfricaPrototypePrefix,
                    gamePath, journal, prepared);

                Dictionary<string, DtaEntry> normandySource =
                    DirectFiles(archive, NormandySourcePrefix);
                Dictionary<string, DtaEntry> normandyPrototype =
                    DirectFiles(archive, NormandyPrototypePrefix);
                List<DtaEntry> normandyBase = NormandyComplements(
                    normandySource, normandyPrototype);
                ValidateNormandyInventory(
                    normandySource, normandyPrototype, normandyBase);
                written += InstallEntries(archive, normandyBase, NormandyPrototypePrefix,
                    gamePath, journal, prepared);
            }

            string scriptsPath = Path.Combine(gamePath, "Scripts.dta");
            using (DtaArchive archive = new DtaArchive(scriptsPath))
            {
                Dictionary<string, DtaEntry> scripts =
                    DirectFiles(archive, AfricaScriptSourcePrefix);
                ValidateAfricaScriptEntries(scripts);
                written += InstallEntries(archive,
                    new List<DtaEntry>(scripts.Values), AfricaScriptTargetPrefix,
                    gamePath, journal, prepared);
            }

            Encoding ansi = Encoding.GetEncoding(1252);
            string relativeMapList = "mpmaplist.txt";
            string mapListPath = Path.Combine(gamePath, relativeMapList);
            string originalMapList = File.ReadAllText(mapListPath, ansi);
            string updatedMapList = AddVestiges(originalMapList);
            if (!String.Equals(updatedMapList, originalMapList, StringComparison.Ordinal))
            {
                InstallerCore.PrepareTarget(
                    gamePath, relativeMapList, mapListPath, journal, prepared);
                WriteTextAtomically(mapListPath, updatedMapList, ansi);
                journal.RecordHash(relativeMapList, CmpInstaller.ComputeSha256(mapListPath));
            }
            InstallerCore.Log("Prototypes completes : Normandy3 Zone et Africa5; "
                + written + " ressources officielles ecrites.");
            InstallerCore.Report(progress,
                "Deux cartes PROTOTYPE preparees pour exploration locale ("
                + written + " ressources completees ou verifiees). Africa5 : Deathmatch; "
                + "Normandy3 Zone : Occupation.");
        }

        internal static bool IsPrototypeInstalled(string gamePath, bool normandy)
        {
            if (!InstallerCore.IsGamePath(gamePath)) return false;
            if (normandy)
            {
                string folder = Path.Combine(
                    gamePath, "Missions", "NORMANDY3_MP_ZONE");
                return HasFile(folder, "map.4ds", 1000)
                    && HasFile(folder, "tree.klz", 1000000)
                    && HasFile(folder, "scene.4ds", 1000000)
                    && HasFile(folder, "loader.4ds", 1000)
                    && HasFile(folder, "volumy.bin", 100000);
            }

            string missionFolder = Path.Combine(gamePath, "Missions", "AFRIKA5_MP");
            foreach (string file in AfricaBaseFiles)
                if (!HasFile(missionFolder, file, 0)) return false;
            string scriptFolder = Path.Combine(gamePath, "Scripts", "AFRIKA5_MP");
            for (int number = 1; number <= 7; number++)
                if (!HasFile(scriptFolder,
                    "AF5_mp_cisterna" + number + ".scr", 0)) return false;
            return true;
        }

        internal static string AddVestiges(string mapList)
        {
            string result = AddMap(
                mapList, "teamplay", "Normandy3", "Normandy3_mp",
                NormandyPrototypeName, "NORMANDY3_MP_ZONE",
                "Official unfinished zone variant completed from Normandy3_MP base geometry.");
            result = AddMap(
                result, "deathmatch", "Africa5", "Africa5_mp",
                AfricaPrototypeName, "AFRIKA5_MP",
                "Recovered official prototype completed from Africa5_MP base assets.");
            return result;
        }

        private static int InstallEntries(
            DtaArchive archive, IList<DtaEntry> entries, string targetPrefix,
            string gamePath, StateJournal journal, HashSet<string> prepared)
        {
            List<DtaEntry> ordered = new List<DtaEntry>(entries);
            ordered.Sort(delegate(DtaEntry left, DtaEntry right) {
                return StringComparer.OrdinalIgnoreCase.Compare(left.Name, right.Name);
            });
            int written = 0;
            foreach (DtaEntry source in ordered)
            {
                string relative = targetPrefix + FileName(source.Name);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] data = archive.Read(source);
                string sourceHash = ComputeSha256(data);
                if (File.Exists(target)
                    && String.Equals(CmpInstaller.ComputeSha256(target), sourceHash,
                        StringComparison.OrdinalIgnoreCase)) continue;
                InstallerCore.PrepareTarget(gamePath, relative, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, data);
                    File.Copy(temporary, target, true);
                    journal.RecordHash(relative, sourceHash);
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                written++;
            }
            return written;
        }

        private static List<DtaEntry> NormandyComplements(
            Dictionary<string, DtaEntry> source,
            Dictionary<string, DtaEntry> prototype)
        {
            List<DtaEntry> result = new List<DtaEntry>();
            foreach (string file in NormandyBaseFiles)
            {
                DtaEntry sourceEntry;
                if (!source.TryGetValue(file, out sourceEntry))
                    throw new InvalidDataException(
                        "Base Normandy3 manquante : " + file + ".");
                DtaEntry prototypeEntry;
                if (!prototype.TryGetValue(file, out prototypeEntry)
                    || prototypeEntry.Size <= 19)
                    result.Add(sourceEntry);
            }
            return result;
        }

        private static int ValidateAfricaScripts(string gamePath)
        {
            using (DtaArchive archive = new DtaArchive(
                Path.Combine(gamePath, "Scripts.dta")))
            {
                Dictionary<string, DtaEntry> scripts =
                    DirectFiles(archive, AfricaScriptSourcePrefix);
                ValidateAfricaScriptEntries(scripts);
                return scripts.Count;
            }
        }

        private static void ValidateAfricaScriptEntries(
            Dictionary<string, DtaEntry> scripts)
        {
            if (scripts.Count != 7)
                throw new InvalidDataException(
                    "Les sept scripts officiels Africa5 sont incomplets.");
            for (int number = 1; number <= 7; number++)
                if (!scripts.ContainsKey("AF5_mp_cisterna" + number + ".scr"))
                    throw new InvalidDataException(
                        "Script Africa5 manquant : citerne " + number + ".");
        }

        private static void ValidateAfricaInventory(
            Dictionary<string, DtaEntry> source,
            Dictionary<string, DtaEntry> prototype,
            List<DtaEntry> missing)
        {
            if (source.Count != 13 || prototype.Count != 7 || missing.Count != 6
                || !source.ContainsKey("map.4ds")
                || !source.ContainsKey("loader.4ds")
                || !source.ContainsKey("mpscripts.dta")
                || !prototype.ContainsKey("actors.bin")
                || !prototype.ContainsKey("tree.klz"))
                throw new InvalidDataException(
                    "Structure du prototype AFRIKA5_MP differente de l'archive 1.12 attendue.");
        }

        private static void ValidateNormandyInventory(
            Dictionary<string, DtaEntry> source,
            Dictionary<string, DtaEntry> prototype,
            List<DtaEntry> complements)
        {
            if (source.Count != 14 || prototype.Count != 13 || complements.Count != 5
                || !prototype.ContainsKey("scene2.bin")
                || !prototype.ContainsKey("actors.bin")
                || !prototype.ContainsKey("items.dat")
                || prototype["tree.klz"].Size != 16
                || prototype["map.4ds"].Size != 19
                || prototype["scene.4ds"].Size != 19
                || prototype["loader.4ds"].Size != 19
                || prototype.ContainsKey("volumy.bin"))
                throw new InvalidDataException(
                    "Structure du prototype NORMANDY3_MP_ZONE differente de l'archive 1.12 attendue.");
        }

        private static Dictionary<string, DtaEntry> DirectFiles(
            DtaArchive archive, string prefix)
        {
            Dictionary<string, DtaEntry> result =
                new Dictionary<string, DtaEntry>(StringComparer.OrdinalIgnoreCase);
            foreach (DtaEntry entry in archive.Entries)
            {
                string normalized = entry.Name.Replace((char)92, '/');
                if (!normalized.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                    continue;
                string tail = normalized.Substring(prefix.Length);
                if (tail.Length == 0 || tail.IndexOf('/') >= 0) continue;
                result[tail] = entry;
            }
            return result;
        }

        private static List<DtaEntry> MissingFiles(
            Dictionary<string, DtaEntry> source,
            Dictionary<string, DtaEntry> prototype)
        {
            List<DtaEntry> missing = new List<DtaEntry>();
            foreach (KeyValuePair<string, DtaEntry> pair in source)
                if (!prototype.ContainsKey(pair.Key)) missing.Add(pair.Value);
            missing.Sort(delegate(DtaEntry left, DtaEntry right) {
                return StringComparer.OrdinalIgnoreCase.Compare(left.Name, right.Name);
            });
            return missing;
        }

        private static string AddMap(
            string mapList, string style, string sourceName, string sourceDir,
            string targetName, string targetDir, string comment)
        {
            Regex sectionPattern = new Regex(
                @"<GAMESTYLE\s+type=""" + Regex.Escape(style)
                + @"""[\s\S]*?</GAMESTYLE>", RegexOptions.IgnoreCase);
            Match section = sectionPattern.Match(mapList);
            if (!section.Success)
                throw new InvalidDataException("Section multijoueur introuvable : " + style);

            Match existing = Regex.Match(section.Value,
                @"<MAP\s+name=""[^""]*""\s+dir=""" + Regex.Escape(targetDir) + @"""",
                RegexOptions.IgnoreCase);
            if (existing.Success)
            {
                string renamed = Regex.Replace(existing.Value, @"name=""[^""]*""",
                    "name=\"" + targetName + "\"", RegexOptions.IgnoreCase);
                string updatedSection = section.Value.Substring(0, existing.Index) + renamed
                    + section.Value.Substring(existing.Index + existing.Length);
                return mapList.Substring(0, section.Index) + updatedSection
                    + mapList.Substring(section.Index + section.Length);
            }

            Regex mapPattern = new Regex(
                @"<MAP\s+name=""" + Regex.Escape(sourceName)
                + @"""\s+dir=""" + Regex.Escape(sourceDir)
                + @"""[\s\S]*?</MAP>", RegexOptions.IgnoreCase);
            Match template = mapPattern.Match(section.Value);
            if (!template.Success)
                throw new InvalidDataException(
                    "Modele de carte officiel introuvable : " + sourceDir);
            string restored = Regex.Replace(
                template.Value, @"name=""" + Regex.Escape(sourceName) + @"""",
                "name=\"" + targetName + "\"", RegexOptions.IgnoreCase);
            restored = Regex.Replace(
                restored, @"dir=""" + Regex.Escape(sourceDir) + @"""",
                "dir=\"" + targetDir + "\"", RegexOptions.IgnoreCase);
            int closing = section.Value.LastIndexOf(
                "</GAMESTYLE>", StringComparison.OrdinalIgnoreCase);
            if (closing < 0)
                throw new InvalidDataException("Section multijoueur non fermee.");
            string insertedSection = section.Value.Insert(
                closing, "        <!-- " + comment + " -->\r\n"
                + restored + "\r\n    ");
            return mapList.Substring(0, section.Index) + insertedSection
                + mapList.Substring(section.Index + section.Length);
        }

        private static bool ContainsDir(string mapList, string directory)
        {
            return Regex.IsMatch(
                mapList, @"dir\s*=\s*""" + Regex.Escape(directory) + @"""",
                RegexOptions.IgnoreCase);
        }

        private static bool HasFile(string folder, string name, long minimumSize)
        {
            string path = Path.Combine(folder, name);
            return File.Exists(path) && new FileInfo(path).Length > minimumSize;
        }

        private static string ComputeSha256(byte[] data)
        {
            using (System.Security.Cryptography.SHA256 sha =
                System.Security.Cryptography.SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(data)).Replace("-", "");
        }

        private static string FileName(string path)
        {
            string normalized = path.Replace((char)92, '/');
            int separator = normalized.LastIndexOf('/');
            return separator < 0 ? normalized : normalized.Substring(separator + 1);
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
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }
    }
}
