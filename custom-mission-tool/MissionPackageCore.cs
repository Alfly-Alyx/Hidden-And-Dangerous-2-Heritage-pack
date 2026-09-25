using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using HD2CommunityInstaller;

namespace HD2CustomMissionManager
{
    internal sealed class LocalizedText
    {
        public readonly Dictionary<string, string> Values =
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        public string ForLanguage(string language)
        {
            string value;
            if (Values.TryGetValue(language, out value)) return value;
            if (String.Equals(language, "EnglishUS", StringComparison.OrdinalIgnoreCase)
                && Values.TryGetValue("english", out value)) return value;
            if (String.Equals(language, "english", StringComparison.OrdinalIgnoreCase)
                && Values.TryGetValue("EnglishUS", out value)) return value;
            if (Values.TryGetValue("default", out value)) return value;
            if (Values.TryGetValue("english", out value)) return value;
            return Values["EnglishUS"];
        }
    }

    internal sealed class PayloadFile
    {
        public string Source;
        public string Relative;
    }

    internal sealed class MissionPackage
    {
        public string Id;
        public string Category;
        public string MissionDirectory;
        public string LoadingScreen;
        public string TemplateMission;
        public LocalizedText Title;
        public readonly List<LocalizedText> Objectives = new List<LocalizedText>();
        public readonly List<PayloadFile> Files = new List<PayloadFile>();
        public int TitleId;
        public bool PreserveTemplateObjectives;
        public readonly List<int> ObjectiveIds = new List<int>();
    }

    internal sealed class MissionLibrary
    {
        public string Root;
        public readonly List<MissionPackage> Packages = new List<MissionPackage>();
        public readonly Dictionary<string, int> Registry =
            new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        public bool RegistryChanged;
        public int FileCount
        {
            get { return Packages.Sum(item => item.Files.Count); }
        }
    }

    internal sealed class ManagedFile
    {
        public string Relative;
        public bool Created;
        public string Sha256;
        public string BackupSha256;
        public string PackageId;
    }

    internal sealed class GdtBlock
    {
        public ushort Kind;
        public byte[] Payload;
        public readonly List<GdtBlock> Children = new List<GdtBlock>();
    }

    internal sealed class FileTransactionOperation
    {
        public string Target;
        public byte[] Data;
        public bool Delete;
        public bool Existed;
        public string Snapshot;
        public string Staged;
    }

    internal sealed class FileTransaction
    {
        private readonly List<FileTransactionOperation> operations =
            new List<FileTransactionOperation>();
        private readonly HashSet<string> targets =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        private readonly string stagingParent;

        public FileTransaction(string stagingParent)
        {
            this.stagingParent = String.IsNullOrWhiteSpace(stagingParent)
                ? Path.Combine(Path.GetTempPath(), "HD2CustomMissionManager")
                : Path.GetFullPath(stagingParent);
        }

        public int Count { get { return operations.Count; } }

        public void AddWrite(string target, byte[] data)
        {
            if (data == null) throw new ArgumentNullException("data");
            Add(new FileTransactionOperation {
                Target = Path.GetFullPath(target), Data = (byte[])data.Clone(), Delete = false
            });
        }

        public void AddDelete(string target)
        {
            Add(new FileTransactionOperation {
                Target = Path.GetFullPath(target), Data = null, Delete = true
            });
        }

        private void Add(FileTransactionOperation operation)
        {
            if (!targets.Add(operation.Target))
                throw new InvalidOperationException(
                    "Le même fichier est présent deux fois dans la transaction : " + operation.Target);
            operations.Add(operation);
        }

        public void Commit()
        {
            Commit(-1);
        }

        internal void Commit(int failBeforeOperation)
        {
            Directory.CreateDirectory(stagingParent);
            string stagingRoot = Path.Combine(
                stagingParent, "transaction-" + Guid.NewGuid().ToString("N"));
            List<FileTransactionOperation> committed = new List<FileTransactionOperation>();
            try
            {
                Directory.CreateDirectory(stagingRoot);
                for (int index = 0; index < operations.Count; index++)
                {
                    FileTransactionOperation operation = operations[index];
                    operation.Existed = File.Exists(operation.Target);
                    if (operation.Existed)
                    {
                        operation.Snapshot = Path.Combine(stagingRoot, "old-" + index.ToString("D5"));
                        File.Copy(operation.Target, operation.Snapshot, false);
                    }
                    if (!operation.Delete)
                    {
                        operation.Staged = Path.Combine(stagingRoot, "new-" + index.ToString("D5"));
                        File.WriteAllBytes(operation.Staged, operation.Data);
                        if (!File.ReadAllBytes(operation.Staged).SequenceEqual(operation.Data))
                            throw new IOException("La vérification du fichier préparé a échoué : "
                                + operation.Target);
                    }
                }

                for (int index = 0; index < operations.Count; index++)
                {
                    if (index == failBeforeOperation)
                        throw new IOException("Échec simulé avant l'écriture " + index + ".");
                    FileTransactionOperation operation = operations[index];
                    if (operation.Delete)
                    {
                        if (File.Exists(operation.Target)) File.Delete(operation.Target);
                    }
                    else
                        MissionPackageCore.WriteAtomic(
                            operation.Target, File.ReadAllBytes(operation.Staged));
                    committed.Add(operation);
                }
            }
            catch (Exception primary)
            {
                List<Exception> rollbackErrors = new List<Exception>();
                for (int index = committed.Count - 1; index >= 0; index--)
                {
                    FileTransactionOperation operation = committed[index];
                    try
                    {
                        if (operation.Existed)
                            MissionPackageCore.WriteAtomic(
                                operation.Target, File.ReadAllBytes(operation.Snapshot));
                        else if (File.Exists(operation.Target))
                            File.Delete(operation.Target);
                    }
                    catch (Exception rollbackError)
                    {
                        rollbackErrors.Add(rollbackError);
                    }
                }
                if (rollbackErrors.Count > 0)
                {
                    rollbackErrors.Insert(0, primary);
                    throw new IOException(
                        "L'installation a échoué et sa restauration automatique est incomplète.",
                        new AggregateException(rollbackErrors));
                }
                throw;
            }
            finally
            {
                if (Directory.Exists(stagingRoot)) Directory.Delete(stagingRoot, true);
            }
        }
    }

    internal static class MissionPackageCore
    {
        private const string ExpectedExecutableSha256 =
            "1EEBDE4710F800F712A05B1ECEE2BA862C144F478DF89B58E54C912E857EE78C";
        private const string MenuModuleResource =
            "HD2CustomMissionManager.CustomMenu.asi";
        private const string RuntimeOwner = "__custom-menu-runtime__";
        private const int MaximumMenuRows = 255;
        private const string ExpectedAsiLoaderSha256 =
            "A07F2B90B0EA9CFFB568218E500EA3280B750C195E83D82A6BB7A252642708E3";
        private const int TextIdStart = 22000;
        private const int TextIdEnd = 65000;
        private const int TextIdBlock = 32;
        private const string RegistryName = ".catalogue-ids.json";
        private static readonly string[] CategoryOrder = {
            "multiplayer-adaptation", "user-mission", "free-exploration"
        };
        private static readonly Dictionary<string, int> CategoryIds =
            new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase) {
                { "multiplayer-adaptation", 20410 },
                { "user-mission", 20411 },
                { "free-exploration", 20412 }
            };
        private static readonly Dictionary<string, Dictionary<string, string>> CategoryNames =
            new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase) {
                { "multiplayer-adaptation", new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
                    { "default", "Multiplayer adaptations" }, { "english", "Multiplayer adaptations" },
                    { "EnglishUS", "Multiplayer adaptations" }, { "french", "Adaptations multijoueur" },
                    { "german", "Mehrspieler-Anpassungen" }, { "italian", "Adattamenti multigiocatore" },
                    { "spanish", "Adaptaciones multijugador" }, { "czech", "Adaptace hry více hráčů" },
                    { "japan", "マルチプレイ移植" }
                } },
                { "user-mission", new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
                    { "default", "User missions" }, { "english", "User missions" },
                    { "EnglishUS", "User missions" }, { "french", "Missions utilisateur" },
                    { "german", "Benutzermissionen" }, { "italian", "Missioni utente" },
                    { "spanish", "Misiones de usuario" }, { "czech", "Uživatelské mise" },
                    { "japan", "ユーザーミッション" }
                } },
                { "free-exploration", new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
                    { "default", "Free exploration / weapon tests" },
                    { "english", "Free exploration / weapon tests" },
                    { "EnglishUS", "Free exploration / weapon tests" },
                    { "french", "Exploration libre / tests d'armes" },
                    { "german", "Freie Erkundung / Waffentests" },
                    { "italian", "Esplorazione libera / prove armi" },
                    { "spanish", "Exploración libre / pruebas de armas" },
                    { "czech", "Volný průzkum / testy zbraní" },
                    { "japan", "自由探索 / 武器テスト" }
                } }
            };
        private static readonly Dictionary<int, Dictionary<string, string>> MenuNames =
            new Dictionary<int, Dictionary<string, string>> {
                { 20402, new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
                    { "default", "CUSTOM MISSIONS" }, { "english", "CUSTOM MISSIONS" },
                    { "EnglishUS", "CUSTOM MISSIONS" }, { "french", "MISSIONS PERSONNALISÉES" },
                    { "german", "EIGENE MISSIONEN" }, { "italian", "MISSIONI PERSONALIZZATE" },
                    { "spanish", "MISIONES PERSONALIZADAS" }, { "czech", "VLASTNÍ MISE" },
                    { "japan", "カスタムミッション" }
                } },
                { 20413, new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
                    { "default", "BACK" }, { "english", "BACK" }, { "EnglishUS", "BACK" },
                    { "french", "RETOUR" }, { "german", "ZURÜCK" },
                    { "italian", "INDIETRO" }, { "spanish", "ATRÁS" },
                    { "czech", "ZPĚT" }, { "japan", "戻る" }
                } }
            };
        private static readonly HashSet<string> AllowedRoots =
            new HashSet<string>(new[] {
                "Maps", "Missions", "Models", "Scripts", "Sounds", "Tables", "Text"
            }, StringComparer.OrdinalIgnoreCase);
        private static readonly HashSet<string> ForbiddenPayloadExtensions =
            new HashSet<string>(new[] {
                ".asi", ".dll", ".exe", ".com", ".bat", ".cmd", ".ps1",
                ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".hta",
                ".msi", ".msp", ".lnk", ".url", ".pif", ".cpl", ".drv", ".sys"
            }, StringComparer.OrdinalIgnoreCase);
        private static readonly HashSet<string> TranslationKeys =
            new HashSet<string>(new[] {
                "default", "czech", "english", "EnglishUS", "french", "german",
                "italian", "japan", "spanish"
            }, StringComparer.OrdinalIgnoreCase);
        private static readonly Regex PackageIdPattern =
            new Regex("^[a-z0-9][a-z0-9._-]{2,63}$", RegexOptions.CultureInvariant);
        private static readonly Regex MissionDirectoryPattern =
            new Regex("^[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}$", RegexOptions.CultureInvariant);
        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer {
            MaxJsonLength = 16 * 1024 * 1024
        };

        public static string[] Categories
        {
            get { return (string[])CategoryOrder.Clone(); }
        }

        private static string CategoryName(string category, string language)
        {
            Dictionary<string, string> values = CategoryNames[category];
            string value;
            if (values.TryGetValue(language, out value)) return value;
            return values["default"];
        }

        private static string MenuName(int textId, string language)
        {
            Dictionary<string, string> values = MenuNames[textId];
            string value;
            if (values.TryGetValue(language, out value)) return value;
            return values["default"];
        }

        private static Dictionary<string, object> AsObject(object value, string label)
        {
            Dictionary<string, object> result = value as Dictionary<string, object>;
            if (result == null) throw new InvalidDataException(label + " doit être un objet JSON.");
            return result;
        }

        private static string RequiredString(
            Dictionary<string, object> data, string key, string label, int maximum)
        {
            object raw;
            string value = data.TryGetValue(key, out raw) ? raw as string : null;
            if (String.IsNullOrWhiteSpace(value))
                throw new InvalidDataException(label + " doit contenir du texte.");
            value = value.Trim();
            if (value.Length > maximum || value.IndexOf('"') >= 0
                || value.Any(character => character < 32))
                throw new InvalidDataException(label + " est trop long ou contient un caractère interdit.");
            return value;
        }

        private static string OptionalString(
            Dictionary<string, object> data, string key, string label, int maximum)
        {
            object value;
            if (!data.TryGetValue(key, out value) || value == null) return null;
            Dictionary<string, object> wrapper = new Dictionary<string, object>();
            wrapper[key] = value;
            return RequiredString(wrapper, key, label, maximum);
        }

        private static LocalizedText ReadLocalized(object raw, string label)
        {
            LocalizedText result = new LocalizedText();
            string direct = raw as string;
            if (direct != null)
            {
                Dictionary<string, object> wrapper = new Dictionary<string, object>();
                wrapper["value"] = direct;
                result.Values["default"] = RequiredString(wrapper, "value", label, 180);
                return result;
            }
            Dictionary<string, object> values = AsObject(raw, label);
            foreach (KeyValuePair<string, object> pair in values)
            {
                if (!TranslationKeys.Contains(pair.Key))
                    throw new InvalidDataException(label + " contient une langue inconnue : " + pair.Key);
                Dictionary<string, object> wrapper = new Dictionary<string, object>();
                wrapper["value"] = pair.Value;
                result.Values[pair.Key] = RequiredString(wrapper, "value", label + "." + pair.Key, 180);
            }
            if (!result.Values.ContainsKey("default")
                && !result.Values.ContainsKey("english")
                && !result.Values.ContainsKey("EnglishUS"))
                throw new InvalidDataException(label + " doit contenir default, english ou EnglishUS.");
            return result;
        }

        private static IEnumerable<object> AsList(object value, string label)
        {
            object[] array = value as object[];
            if (array != null) return array;
            ArrayList list = value as ArrayList;
            if (list != null) return list.Cast<object>();
            throw new InvalidDataException(label + " doit être une liste.");
        }

        private static MissionPackage ReadPackage(string packageRoot)
        {
            string manifest = Path.Combine(packageRoot, "mission.json");
            Dictionary<string, object> document;
            try
            {
                document = AsObject(Json.DeserializeObject(File.ReadAllText(manifest, Encoding.UTF8)), manifest);
            }
            catch (ArgumentException error)
            {
                throw new InvalidDataException("JSON invalide : " + manifest, error);
            }
            object format;
            if (!document.TryGetValue("format", out format) || Convert.ToInt32(format) != 1)
                throw new InvalidDataException(Path.GetFileName(packageRoot) + " : format doit valoir 1.");
            MissionPackage package = new MissionPackage();
            package.Id = RequiredString(document, "id", Path.GetFileName(packageRoot) + ".id", 64).ToLowerInvariant();
            if (!PackageIdPattern.IsMatch(package.Id))
                throw new InvalidDataException(Path.GetFileName(packageRoot) + " : id invalide.");
            package.Category = RequiredString(document, "category", package.Id + ".category", 64);
            if (String.Equals(package.Category, "original-creation", StringComparison.OrdinalIgnoreCase))
                package.Category = "user-mission";
            else if (String.Equals(package.Category, "weapon-test", StringComparison.OrdinalIgnoreCase))
                package.Category = "free-exploration";
            if (!CategoryIds.ContainsKey(package.Category))
                throw new InvalidDataException(package.Id + " : catégorie inconnue.");
            package.MissionDirectory = RequiredString(
                document, "missionDirectory", package.Id + ".missionDirectory", 64);
            if (!MissionDirectoryPattern.IsMatch(package.MissionDirectory))
                throw new InvalidDataException(package.Id + " : missionDirectory invalide.");
            package.LoadingScreen = OptionalString(document, "loadingScreen", package.Id + ".loadingScreen", 96);
            if (package.LoadingScreen != null && !MissionDirectoryPattern.IsMatch(package.LoadingScreen))
                throw new InvalidDataException(package.Id + " : loadingScreen invalide.");
            package.TemplateMission = OptionalString(document, "templateMission", package.Id + ".templateMission", 64);
            if (package.TemplateMission != null && !MissionDirectoryPattern.IsMatch(package.TemplateMission))
                throw new InvalidDataException(package.Id + " : templateMission invalide.");
            object preserveObjectives;
            if (document.TryGetValue("preserveTemplateObjectives", out preserveObjectives))
            {
                if (!(preserveObjectives is bool))
                    throw new InvalidDataException(
                        package.Id + " : preserveTemplateObjectives doit être un booléen.");
                package.PreserveTemplateObjectives = (bool)preserveObjectives;
            }
            if (package.PreserveTemplateObjectives
                && (package.TemplateMission == null || document.ContainsKey("objectives")))
                throw new InvalidDataException(package.Id
                    + " : preserveTemplateObjectives exige templateMission et interdit le champ objectives.");
            object title;
            if (!document.TryGetValue("title", out title))
                throw new InvalidDataException(package.Id + " : titre absent.");
            package.Title = ReadLocalized(title, package.Id + ".title");
            object objectives;
            if (document.TryGetValue("objectives", out objectives))
            {
                foreach (object objective in AsList(objectives, package.Id + ".objectives"))
                    package.Objectives.Add(ReadLocalized(objective, package.Id + ".objective"));
            }
            if (package.Objectives.Count > 31)
                throw new InvalidDataException(package.Id + " : 31 objectifs au maximum.");
            ReadPayload(packageRoot, package);
            return package;
        }

        private static void ReadPayload(string packageRoot, MissionPackage package)
        {
            string payload = Path.Combine(packageRoot, "payload");
            if (!Directory.Exists(payload))
                throw new InvalidDataException(package.Id + " : dossier payload absent.");
            ReadPayloadFiles(payload, "", package, false);
            RequireMissionTree(package);
        }

        private static void RejectReparsePoint(string path)
        {
            if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
                throw new InvalidDataException("Lien ou jonction interdit : " + path);
        }

        private static void ReadPayloadFiles(
            string payload, string targetPrefix, MissionPackage package,
            bool separateResourceRoots)
        {
            payload = Path.GetFullPath(payload).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            Stack<string> pending = new Stack<string>();
            pending.Push(payload.TrimEnd(Path.DirectorySeparatorChar));
            while (pending.Count > 0)
            {
                string directory = pending.Pop();
                RejectReparsePoint(directory);
                foreach (string child in Directory.GetDirectories(directory)) pending.Push(child);
                foreach (string file in Directory.GetFiles(directory))
                {
                    RejectReparsePoint(file);
                    string full = Path.GetFullPath(file);
                    if (!full.StartsWith(payload, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException(package.Id + " : chemin hors du paquet.");
                    string relative = full.Substring(payload.Length).Replace('\\', '/');
                    string[] parts = relative.Split('/');
                    bool resource = separateResourceRoots && parts.Length > 1
                        && AllowedRoots.Contains(parts[0])
                        && !String.Equals(parts[0], "Missions", StringComparison.OrdinalIgnoreCase);
                    if (!resource) relative = targetPrefix + relative;
                    parts = relative.Split('/');
                    if (parts.Length == 0 || !AllowedRoots.Contains(parts[0])
                        || parts.Any(part => part == "." || part == ".." || part.IndexOf(':') >= 0))
                        throw new InvalidDataException(package.Id + " : chemin interdit : " + relative);
                    string extension = Path.GetExtension(relative);
                    if (ForbiddenPayloadExtensions.Contains(extension))
                        throw new InvalidDataException(package.Id
                            + " : type de fichier exécutable interdit dans un paquet : "
                            + relative);
                    if (String.Equals(relative, "Models/singleplayer.4ds", StringComparison.OrdinalIgnoreCase)
                        || String.Equals(relative, "Models/single mission 2.4ds", StringComparison.OrdinalIgnoreCase)
                        || String.Equals(relative, "Scripts/HD2.CustomMenu.asi", StringComparison.OrdinalIgnoreCase)
                        || (String.Equals(parts[0], "Text", StringComparison.OrdinalIgnoreCase)
                            && String.Equals(parts[parts.Length - 1], "TEXTY_DD.txt", StringComparison.OrdinalIgnoreCase)))
                        throw new InvalidDataException(package.Id + " : fichier réservé : " + relative);
                    package.Files.Add(new PayloadFile { Source = full, Relative = relative });
                }
            }
        }

        private static void RequireMissionTree(MissionPackage package)
        {
            string expectedTree = "Missions/" + package.MissionDirectory + "/tree.klz";
            if (!package.Files.Any(file => String.Equals(
                file.Relative, expectedTree, StringComparison.OrdinalIgnoreCase)))
                throw new InvalidDataException(package.Id + " : Missions/"
                    + package.MissionDirectory + "/tree.klz absent.");
        }

        private static MissionPackage ReadMissionFolder(string folder)
        {
            RejectReparsePoint(folder);
            string folderName = Path.GetFileName(folder);
            string stem = ImportIdStem(folderName).Substring("import.".Length);
            MissionPackage package = new MissionPackage {
                Id = "folder." + stem.Substring(0, Math.Min(stem.Length, 40)) + "."
                    + Sha256(Encoding.UTF8.GetBytes(folderName.ToUpperInvariant()))
                        .Substring(0, 16).ToLowerInvariant(),
                Category = "user-mission",
                Title = ReadLocalized(folderName, folderName + ".title")
            };
            if (File.Exists(Path.Combine(folder, "tree.klz")))
            {
                if (Directory.Exists(Path.Combine(folder, "Missions")))
                    throw new InvalidDataException(folderName
                        + " : structure ambiguë (tree.klz et dossier Missions ensemble)."
                        + " Utilisez soit les fichiers directs, soit Missions/<nom de mission>.");
                package.MissionDirectory = folderName;
                if (!MissionDirectoryPattern.IsMatch(package.MissionDirectory))
                    throw new InvalidDataException("Nom de dossier de mission invalide : " + folderName);
                ReadPayloadFiles(folder, "Missions/" + folderName + "/", package, true);
            }
            else
            {
                string payload = Path.Combine(folder, "payload");
                string content = Directory.Exists(Path.Combine(payload, "Missions"))
                    ? payload : folder;
                RejectReparsePoint(content);
                string missions = Path.Combine(content, "Missions");
                if (!Directory.Exists(missions))
                    throw new InvalidDataException(folderName
                        + " : tree.klz absent. Placez les fichiers de la mission dans ce dossier"
                        + " ou dans Missions/<nom de mission>.");
                RejectReparsePoint(missions);
                List<string> candidates = new List<string>();
                foreach (string mission in Directory.GetDirectories(missions))
                {
                    RejectReparsePoint(mission);
                    if (File.Exists(Path.Combine(mission, "tree.klz"))) candidates.Add(mission);
                }
                if (candidates.Count != 1)
                    throw new InvalidDataException(folderName
                        + " : exactement une mission contenant tree.klz est requise dans Missions.");
                package.MissionDirectory = Path.GetFileName(candidates[0]);
                if (!MissionDirectoryPattern.IsMatch(package.MissionDirectory))
                    throw new InvalidDataException("Nom de dossier de mission invalide : "
                        + package.MissionDirectory);
                foreach (string rootName in AllowedRoots)
                {
                    string resourceRoot = Path.Combine(content, rootName);
                    if (Directory.Exists(resourceRoot))
                        ReadPayloadFiles(resourceRoot, rootName + "/", package, false);
                }
            }
            RequireMissionTree(package);
            return package;
        }

        public static MissionLibrary LoadLibrary(string libraryRoot, bool assignIds)
        {
            MissionLibrary library = new MissionLibrary();
            library.Root = Path.GetFullPath(libraryRoot);
            if (!Directory.Exists(library.Root))
                throw new DirectoryNotFoundException("Bibliothèque introuvable : " + library.Root);
            RejectReparsePoint(library.Root);
            foreach (string directory in Directory.GetDirectories(library.Root)
                .OrderBy(item => item, StringComparer.OrdinalIgnoreCase))
            {
                string name = Path.GetFileName(directory);
                if (name.StartsWith("_", StringComparison.Ordinal)
                    || name.StartsWith(".", StringComparison.Ordinal)) continue;
                RejectReparsePoint(directory);
                string manifest = Path.Combine(directory, "mission.json");
                if (File.Exists(manifest))
                {
                    RejectReparsePoint(manifest);
                    library.Packages.Add(ReadPackage(directory));
                }
                else library.Packages.Add(ReadMissionFolder(directory));
            }
            ReadRegistry(library);
            AssignIds(library);
            ValidateUniqueness(library);
            if (assignIds && library.RegistryChanged) WriteRegistry(library);
            return library;
        }

        private static void ValidateUniqueness(MissionLibrary library)
        {
            HashSet<string> ids = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            HashSet<string> directories = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            HashSet<string> files = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (MissionPackage package in library.Packages)
            {
                if (!ids.Add(package.Id)) throw new InvalidDataException("Identifiant dupliqué : " + package.Id);
                if (!directories.Add(package.MissionDirectory))
                    throw new InvalidDataException("Dossier de mission dupliqué : " + package.MissionDirectory);
                foreach (PayloadFile file in package.Files)
                    if (!files.Add(file.Relative))
                        throw new InvalidDataException("Fichier fourni par deux paquets : " + file.Relative);
            }
        }

        private static void ReadRegistry(MissionLibrary library)
        {
            string path = Path.Combine(library.Root, RegistryName);
            if (!File.Exists(path)) return;
            Dictionary<string, object> document = AsObject(
                Json.DeserializeObject(File.ReadAllText(path, Encoding.UTF8)), path);
            object format;
            if (!document.TryGetValue("format", out format) || Convert.ToInt32(format) != 1)
                throw new InvalidDataException("Format du registre invalide.");
            object rawAssignments;
            Dictionary<string, object> assignments = document.TryGetValue("assignments", out rawAssignments)
                ? AsObject(rawAssignments, path + ".assignments") : null;
            if (assignments == null) throw new InvalidDataException("Affectations du registre absentes.");
            HashSet<int> occupied = new HashSet<int>();
            foreach (KeyValuePair<string, object> pair in assignments)
            {
                int value = Convert.ToInt32(pair.Value);
                if (value < TextIdStart || value + TextIdBlock - 1 > TextIdEnd
                    || (value - TextIdStart) % TextIdBlock != 0 || !occupied.Add(value))
                    throw new InvalidDataException("Plage invalide ou dupliquée dans le registre.");
                library.Registry[pair.Key] = value;
            }
        }

        private static void AssignIds(MissionLibrary library)
        {
            HashSet<int> occupied = new HashSet<int>(library.Registry.Values);
            foreach (MissionPackage package in library.Packages)
            {
                int baseId;
                if (!library.Registry.TryGetValue(package.Id, out baseId))
                {
                    baseId = -1;
                    for (int candidate = TextIdStart;
                        candidate + TextIdBlock - 1 <= TextIdEnd; candidate += TextIdBlock)
                        if (!occupied.Contains(candidate)) { baseId = candidate; break; }
                    if (baseId < 0) throw new InvalidDataException("Plus aucun emplacement de texte disponible.");
                    library.Registry[package.Id] = baseId;
                    occupied.Add(baseId);
                    library.RegistryChanged = true;
                }
                package.TitleId = baseId;
                for (int index = 0; index < package.Objectives.Count; index++)
                    package.ObjectiveIds.Add(baseId + index + 1);
            }
        }

        private static byte[] RegistryBytes(MissionLibrary library)
        {
            SortedDictionary<string, int> assignments =
                new SortedDictionary<string, int>(library.Registry, StringComparer.OrdinalIgnoreCase);
            Dictionary<string, object> document = new Dictionary<string, object>();
            document["format"] = 1;
            document["assignments"] = assignments;
            return new UTF8Encoding(false).GetBytes(Json.Serialize(document));
        }

        private static void WriteRegistry(MissionLibrary library)
        {
            WriteAtomic(Path.Combine(library.Root, RegistryName), RegistryBytes(library));
            library.RegistryChanged = false;
        }

        public static string CreatePackage(
            string libraryRoot, string id, string missionDirectory, string title, string category)
        {
            return CreatePackage(libraryRoot, id, missionDirectory, title, category, "french");
        }

        public static string CreatePackage(
            string libraryRoot, string id, string missionDirectory, string title, string category,
            string language)
        {
            id = (id ?? "").Trim().ToLowerInvariant();
            missionDirectory = (missionDirectory ?? "").Trim();
            title = (title ?? "").Trim();
            language = (language ?? "english").Trim();
            if (!TranslationKeys.Contains(language) ||
                String.Equals(language, "default", StringComparison.OrdinalIgnoreCase))
                language = "english";
            if (!PackageIdPattern.IsMatch(id)) throw new InvalidDataException("Identifiant invalide.");
            if (!MissionDirectoryPattern.IsMatch(missionDirectory))
                throw new InvalidDataException("Nom de dossier de mission invalide.");
            if (String.IsNullOrWhiteSpace(title) || title.IndexOf('"') >= 0 || title.Length > 180)
                throw new InvalidDataException("Titre invalide.");
            if (!CategoryIds.ContainsKey(category)) throw new InvalidDataException("Catégorie invalide.");
            string root = Path.Combine(Path.GetFullPath(libraryRoot), id);
            if (Directory.Exists(root)) throw new IOException("Ce paquet existe déjà : " + root);
            string mission = Path.Combine(root, "payload", "Missions", missionDirectory);
            Directory.CreateDirectory(mission);
            string content = "{\r\n"
                + "  \"$schema\": \"../mission.schema.json\",\r\n"
                + "  \"format\": 1,\r\n"
                + "  \"id\": " + Json.Serialize(id) + ",\r\n"
                + "  \"category\": " + Json.Serialize(category) + ",\r\n"
                + "  \"missionDirectory\": " + Json.Serialize(missionDirectory) + ",\r\n"
                + "  \"title\": {\r\n"
                + "    \"default\": " + Json.Serialize(title) + ",\r\n"
                + "    " + Json.Serialize(language) + ": " + Json.Serialize(title) + "\r\n"
                + "  },\r\n"
                + "  \"objectives\": []\r\n"
                + "}\r\n";
            File.WriteAllText(Path.Combine(root, "mission.json"), content, new UTF8Encoding(false));
            return mission;
        }

        public static string ImportUserMission(
            string sourceRoot, string libraryRoot, string title, string language)
        {
            if (String.IsNullOrWhiteSpace(sourceRoot))
                throw new InvalidDataException("Dossier de mission absent.");
            string source = Path.GetFullPath(sourceRoot).TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            if (!Directory.Exists(source))
                throw new DirectoryNotFoundException("Dossier de mission introuvable : " + source);
            if ((File.GetAttributes(source) & FileAttributes.ReparsePoint) != 0)
                throw new InvalidDataException("Les liens et jonctions ne peuvent pas être importés.");

            string library = Path.GetFullPath(libraryRoot).TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            Directory.CreateDirectory(library);
            string libraryPrefix = library + Path.DirectorySeparatorChar;
            if (String.Equals(source, library, StringComparison.OrdinalIgnoreCase)
                || source.StartsWith(libraryPrefix, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Choisissez une mission située hors de CustomMissions.");

            string contentRoot = null;
            string missionSource = null;
            string missionDirectory = null;
            string packagedPayload = Path.Combine(source, "payload");
            if (Directory.Exists(Path.Combine(packagedPayload, "Missions")))
                contentRoot = packagedPayload;
            else if (Directory.Exists(Path.Combine(source, "Missions")))
                contentRoot = source;

            if (contentRoot != null)
            {
                string missionsRoot = Path.Combine(contentRoot, "Missions");
                string[] candidates = Directory.GetDirectories(missionsRoot)
                    .Where(item => File.Exists(Path.Combine(item, "tree.klz"))).ToArray();
                if (candidates.Length != 1)
                    throw new InvalidDataException(
                        "Le dossier choisi doit contenir exactement une mission avec tree.klz.");
                missionSource = candidates[0];
                missionDirectory = Path.GetFileName(missionSource);
            }
            else if (File.Exists(Path.Combine(source, "tree.klz")))
            {
                missionSource = source;
                missionDirectory = Path.GetFileName(source);
            }
            else
                throw new InvalidDataException(
                    "Aucun tree.klz trouvé. Choisissez le dossier de la mission ou son paquet complet.");

            if (!MissionDirectoryPattern.IsMatch(missionDirectory))
                throw new InvalidDataException("Nom de dossier de mission invalide : " + missionDirectory);
            title = (title ?? "").Trim();
            if (String.IsNullOrWhiteSpace(title) || title.IndexOf('"') >= 0 || title.Length > 180)
                throw new InvalidDataException("Titre invalide.");
            language = (language ?? "english").Trim();
            if (!TranslationKeys.Contains(language)
                || String.Equals(language, "default", StringComparison.OrdinalIgnoreCase))
                language = "english";

            MissionLibrary loaded = LoadLibrary(library, false);
            if (loaded.Packages.Any(item => String.Equals(
                item.MissionDirectory, missionDirectory, StringComparison.OrdinalIgnoreCase)))
                throw new InvalidDataException("Cette mission existe déjà : " + missionDirectory);

            string stem = ImportIdStem(missionDirectory);
            string id = stem;
            int suffix = 2;
            while (loaded.Packages.Any(item => String.Equals(item.Id, id, StringComparison.OrdinalIgnoreCase))
                || Directory.Exists(Path.Combine(library, id)))
            {
                string tail = "-" + suffix.ToString();
                id = stem.Substring(0, Math.Min(stem.Length, 64 - tail.Length)) + tail;
                suffix++;
            }

            string staging = Path.Combine(library, "_import-" + Guid.NewGuid().ToString("N"));
            string destination = Path.Combine(library, id);
            try
            {
                string payload = Path.Combine(staging, "payload");
                Directory.CreateDirectory(payload);
                if (contentRoot == null)
                    CopyDirectorySafe(missionSource,
                        Path.Combine(payload, "Missions", missionDirectory));
                else
                    foreach (string rootName in AllowedRoots)
                    {
                        string rootSource = Path.Combine(contentRoot, rootName);
                        if (Directory.Exists(rootSource))
                            CopyDirectorySafe(rootSource, Path.Combine(payload, rootName));
                    }

                string manifest = "{\r\n"
                    + "  \"$schema\": \"../mission.schema.json\",\r\n"
                    + "  \"format\": 1,\r\n"
                    + "  \"id\": " + Json.Serialize(id) + ",\r\n"
                    + "  \"category\": \"user-mission\",\r\n"
                    + "  \"missionDirectory\": " + Json.Serialize(missionDirectory) + ",\r\n"
                    + "  \"title\": {\r\n"
                    + "    \"default\": " + Json.Serialize(title) + ",\r\n"
                    + "    " + Json.Serialize(language) + ": " + Json.Serialize(title) + "\r\n"
                    + "  },\r\n"
                    + "  \"objectives\": []\r\n"
                    + "}\r\n";
                File.WriteAllText(Path.Combine(staging, "mission.json"), manifest,
                    new UTF8Encoding(false));
                MissionPackage imported = ReadPackage(staging);
                if (!String.Equals(imported.Category, "user-mission", StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("La mission importée n'est pas une mission utilisateur.");
                Directory.Move(staging, destination);
                return destination;
            }
            catch
            {
                if (Directory.Exists(staging)) Directory.Delete(staging, true);
                throw;
            }
        }

        private static string ImportIdStem(string missionDirectory)
        {
            StringBuilder slug = new StringBuilder();
            foreach (char character in missionDirectory.ToLowerInvariant())
            {
                if (character >= 'a' && character <= 'z' || character >= '0' && character <= '9'
                    || character == '.' || character == '_' || character == '-')
                    slug.Append(character);
                else if (slug.Length == 0 || slug[slug.Length - 1] != '-') slug.Append('-');
            }
            string value = slug.ToString().Trim('-', '.', '_');
            if (value.Length == 0) value = "mission";
            value = "import." + value;
            return value.Substring(0, Math.Min(value.Length, 64));
        }

        private static void CopyDirectorySafe(string sourceRoot, string destinationRoot)
        {
            string source = Path.GetFullPath(sourceRoot).TrimEnd(Path.DirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            Stack<Tuple<string, string>> pending = new Stack<Tuple<string, string>>();
            pending.Push(Tuple.Create(source.TrimEnd(Path.DirectorySeparatorChar), destinationRoot));
            while (pending.Count > 0)
            {
                Tuple<string, string> item = pending.Pop();
                if ((File.GetAttributes(item.Item1) & FileAttributes.ReparsePoint) != 0)
                    throw new InvalidDataException("Lien ou jonction interdit : " + item.Item1);
                Directory.CreateDirectory(item.Item2);
                foreach (string file in Directory.GetFiles(item.Item1))
                {
                    if ((File.GetAttributes(file) & FileAttributes.ReparsePoint) != 0)
                        throw new InvalidDataException("Lien interdit : " + file);
                    string full = Path.GetFullPath(file);
                    if (!full.StartsWith(source, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("Chemin hors de la mission : " + file);
                    File.Copy(full, Path.Combine(item.Item2, Path.GetFileName(file)), false);
                }
                foreach (string directory in Directory.GetDirectories(item.Item1))
                    pending.Push(Tuple.Create(directory,
                        Path.Combine(item.Item2, Path.GetFileName(directory))));
            }
        }

        private static bool TryParseBlocks(
            byte[] data, int start, int end, out List<GdtBlock> result)
        {
            result = new List<GdtBlock>();
            int cursor = start;
            while (cursor < end)
            {
                if (cursor > end - 6) { result = null; return false; }
                ushort kind = BitConverter.ToUInt16(data, cursor);
                uint rawSize = BitConverter.ToUInt32(data, cursor + 2);
                if (rawSize < 6 || rawSize > Int32.MaxValue || cursor > end - (int)rawSize)
                {
                    result = null;
                    return false;
                }
                int payloadStart = cursor + 6;
                int blockEnd = cursor + (int)rawSize;
                GdtBlock block = new GdtBlock { Kind = kind };
                block.Payload = new byte[blockEnd - payloadStart];
                Buffer.BlockCopy(data, payloadStart, block.Payload, 0, block.Payload.Length);
                List<GdtBlock> children;
                if (TryParseBlocks(data, payloadStart, blockEnd, out children) && children.Count > 0)
                    block.Children.AddRange(children);
                result.Add(block);
                cursor = blockEnd;
            }
            return cursor == end;
        }

        private static IEnumerable<GdtBlock> Walk(IEnumerable<GdtBlock> blocks)
        {
            foreach (GdtBlock block in blocks)
            {
                yield return block;
                foreach (GdtBlock child in Walk(block.Children)) yield return child;
            }
        }

        private static GdtBlock Direct(GdtBlock block, ushort kind)
        {
            return block.Children.FirstOrDefault(child => child.Kind == kind);
        }

        private static string BlockString(GdtBlock block)
        {
            int count = block.Payload.Length;
            while (count > 0 && block.Payload[count - 1] == 0) count--;
            return Encoding.GetEncoding(1252).GetString(block.Payload, 0, count);
        }

        private static byte[] EncodeBlock(ushort kind, byte[] payload)
        {
            byte[] result = new byte[payload.Length + 6];
            Buffer.BlockCopy(BitConverter.GetBytes(kind), 0, result, 0, 2);
            Buffer.BlockCopy(BitConverter.GetBytes(result.Length), 0, result, 2, 4);
            Buffer.BlockCopy(payload, 0, result, 6, payload.Length);
            return result;
        }

        private static byte[] Join(IEnumerable<byte[]> pieces)
        {
            int length = pieces.Sum(piece => piece.Length);
            byte[] result = new byte[length];
            int offset = 0;
            foreach (byte[] piece in pieces)
            {
                Buffer.BlockCopy(piece, 0, result, offset, piece.Length);
                offset += piece.Length;
            }
            return result;
        }

        private static byte[] EncodeExisting(GdtBlock block)
        {
            byte[] payload = block.Children.Count > 0
                ? Join(block.Children.Select(EncodeExisting)) : block.Payload;
            return EncodeBlock(block.Kind, payload);
        }

        private static byte[] EncodeInteger(ushort kind, int value)
        {
            return EncodeBlock(kind, BitConverter.GetBytes(value));
        }

        private static byte[] EncodeString(ushort kind, string value, byte[] model)
        {
            byte[] text = Encoding.ASCII.GetBytes(value);
            bool terminated = model.Length > 0 && model[model.Length - 1] == 0;
            byte[] payload = new byte[text.Length + (terminated ? 1 : 0)];
            Buffer.BlockCopy(text, 0, payload, 0, text.Length);
            return EncodeBlock(kind, payload);
        }

        private static byte[] RewriteObjective(GdtBlock objective, int textId)
        {
            bool replaced = false;
            List<byte[]> content = new List<byte[]>();
            foreach (GdtBlock child in objective.Children)
            {
                if (child.Kind == 0x29 && !replaced)
                {
                    content.Add(EncodeInteger(0x29, textId));
                    replaced = true;
                }
                else content.Add(EncodeExisting(child));
            }
            if (!replaced) throw new InvalidDataException("Identifiant d'objectif absent du gabarit.");
            return EncodeBlock(objective.Kind, Join(content));
        }

        private static byte[] RewriteMission(GdtBlock model, MissionPackage mission)
        {
            bool title = false;
            bool directory = false;
            bool loading = mission.LoadingScreen == null;
            bool objectives = mission.PreserveTemplateObjectives;
            GdtBlock objectiveModel = model.Children.FirstOrDefault(child => child.Kind == 0x28);
            List<byte[]> content = new List<byte[]>();
            foreach (GdtBlock child in model.Children)
            {
                if (child.Kind == 0x33 && !title)
                {
                    content.Add(EncodeInteger(0x33, mission.TitleId));
                    title = true;
                }
                else if (child.Kind == 0x35 && !loading)
                {
                    content.Add(EncodeString(0x35, mission.LoadingScreen, child.Payload));
                    loading = true;
                }
                else if (child.Kind == 0x36 && !directory)
                {
                    content.Add(EncodeString(0x36, mission.MissionDirectory, child.Payload));
                    directory = true;
                }
                else if (child.Kind == 0x28)
                {
                    if (mission.PreserveTemplateObjectives)
                        content.Add(EncodeExisting(child));
                    else if (!objectives)
                    {
                        if (objectiveModel == null && mission.ObjectiveIds.Count > 0)
                            throw new InvalidDataException("Le gabarit ne contient aucun objectif.");
                        foreach (int textId in mission.ObjectiveIds)
                            content.Add(RewriteObjective(objectiveModel, textId));
                        objectives = true;
                    }
                }
                else content.Add(EncodeExisting(child));
            }
            if (!title || !directory || !loading)
                throw new InvalidDataException("Champs requis absents de la mission gabarit.");
            return EncodeBlock(model.Kind, Join(content));
        }

        private static byte[] RewriteCampaign(
            GdtBlock campaign, int headerId, IList<MissionPackage> missions,
            Dictionary<string, GdtBlock> templates)
        {
            GdtBlock defaultTemplate = Walk(campaign.Children)
                .FirstOrDefault(block => block.Kind == 0x32);
            if (defaultTemplate == null) throw new InvalidDataException("Campagne gabarit sans mission.");
            bool header = false;
            bool written = false;
            List<byte[]> content = new List<byte[]>();
            foreach (GdtBlock child in campaign.Children)
            {
                if (child.Kind == 0x3D && !header)
                {
                    content.Add(EncodeInteger(0x3D, headerId));
                    header = true;
                }
                else if (child.Kind == 0x05)
                {
                    List<byte[]> container = new List<byte[]>();
                    foreach (GdtBlock item in child.Children)
                    {
                        if (item.Kind == 0x32)
                        {
                            if (!written)
                            {
                                foreach (MissionPackage mission in missions)
                                {
                                    GdtBlock template = defaultTemplate;
                                    if (!String.IsNullOrWhiteSpace(mission.TemplateMission)
                                        && !templates.TryGetValue(mission.TemplateMission, out template))
                                        throw new InvalidDataException(
                                            "Mission gabarit inconnue : " + mission.TemplateMission);
                                    container.Add(RewriteMission(template, mission));
                                }
                                written = true;
                            }
                        }
                        else container.Add(EncodeExisting(item));
                    }
                    content.Add(EncodeBlock(0x05, Join(container)));
                }
                else content.Add(EncodeExisting(child));
            }
            if (!header || !written) throw new InvalidDataException("Campagne gabarit incomplète.");
            return EncodeBlock(campaign.Kind, Join(content));
        }

        private static byte[] ReadArchiveEntry(string originalGame, string entryName)
        {
            string archivePath = Path.Combine(Path.GetFullPath(originalGame), "SabreSquadron.dta");
            if (!File.Exists(archivePath)) throw new FileNotFoundException("SabreSquadron.dta introuvable.", archivePath);
            using (DtaArchive archive = new DtaArchive(archivePath))
            {
                DtaEntry entry = archive.Entries.FirstOrDefault(item =>
                    String.Equals(item.Name.Replace('/', '\\'), entryName.Replace('/', '\\'),
                        StringComparison.OrdinalIgnoreCase));
                if (entry == null) throw new InvalidDataException(entryName + " absent de l'archive.");
                return archive.Read(entry);
            }
        }

        public static byte[] ReadSourceCatalogue(string originalGame)
        {
            return ReadArchiveEntry(originalGame, "GameData\\Gamedata01.gdt");
        }

        private static Dictionary<string, GdtBlock> MissionTemplates(
            byte[] expansionSource, byte[] originalSource)
        {
            Dictionary<string, GdtBlock> templates =
                new Dictionary<string, GdtBlock>(StringComparer.OrdinalIgnoreCase);
            foreach (byte[] data in new[] { expansionSource, originalSource })
            {
                if (data == null) continue;
                List<GdtBlock> parsed;
                if (!TryParseBlocks(data, 0, data.Length, out parsed))
                    throw new InvalidDataException("Catalogue de gabarits illisible.");
                GdtBlock top = parsed.FirstOrDefault(block => block.Kind == 0x01);
                GdtBlock main = top == null ? null : Direct(top, 0x05);
                if (main == null) throw new InvalidDataException("Catalogue de gabarits sans campagnes.");
                foreach (GdtBlock mission in Walk(main.Children).Where(block => block.Kind == 0x32))
                {
                    GdtBlock directory = Direct(mission, 0x36);
                    if (directory == null) continue;
                    string name = BlockString(directory);
                    if (templates.ContainsKey(name))
                        throw new InvalidDataException("Gabarit de mission ambigu : " + name);
                    templates.Add(name, mission);
                }
            }
            return templates;
        }

        public static byte[] BuildCatalogue(
            byte[] source, MissionLibrary library, byte[] originalSource = null)
        {
            List<GdtBlock> root;
            if (!TryParseBlocks(source, 0, source.Length, out root))
                throw new InvalidDataException("Catalogue Sabre Squadron illisible.");
            GdtBlock top = root.FirstOrDefault(block => block.Kind == 0x01);
            GdtBlock main = top == null ? null : Direct(top, 0x05);
            if (main == null) throw new InvalidDataException("Liste des campagnes absente.");
            List<GdtBlock> sourceCampaigns = main.Children.Where(block => block.Kind == 0x3C).ToList();
            if (sourceCampaigns.Count < 3) throw new InvalidDataException("Trois gabarits de campagne requis.");
            Dictionary<string, GdtBlock> templates = MissionTemplates(source, originalSource);
            List<string> officialDirectories = Walk(main.Children)
                .Where(block => block.Kind == 0x32)
                .Select(block => Direct(block, 0x36)).Where(block => block != null)
                .Select(BlockString).ToList();
            HashSet<string> officialSet = new HashSet<string>(
                templates.Keys, StringComparer.OrdinalIgnoreCase);
            foreach (MissionPackage package in library.Packages)
                if (officialSet.Contains(package.MissionDirectory))
                    throw new InvalidDataException(
                        "Le dossier de mission entre en conflit avec une mission officielle : "
                        + package.MissionDirectory);
            Dictionary<int, List<MissionPackage>> grouped = new Dictionary<int, List<MissionPackage>>();
            for (int index = 0; index < CategoryOrder.Length; index++)
            {
                string category = CategoryOrder[index];
                List<MissionPackage> matches = library.Packages
                    .Where(item => String.Equals(item.Category, category, StringComparison.OrdinalIgnoreCase))
                    .ToList();
                if (matches.Count > 0) grouped[index] = matches;
            }
            List<byte[]> mainContent = main.Children.Select(EncodeExisting).ToList();
            for (int campaignIndex = 0; campaignIndex < CategoryOrder.Length; campaignIndex++)
            {
                List<MissionPackage> missions;
                if (grouped.TryGetValue(campaignIndex, out missions))
                    mainContent.Add(RewriteCampaign(
                        sourceCampaigns[campaignIndex],
                        CategoryIds[CategoryOrder[campaignIndex]], missions, templates));
            }
            byte[] rebuiltMain = EncodeBlock(0x05, Join(mainContent));
            List<byte[]> topContent = new List<byte[]>();
            foreach (GdtBlock child in top.Children)
                topContent.Add(Object.ReferenceEquals(child, main) ? rebuiltMain : EncodeExisting(child));
            byte[] rebuiltTop = EncodeBlock(0x01, Join(topContent));
            byte[] result = Join(root.Select(block =>
                Object.ReferenceEquals(block, top) ? rebuiltTop : EncodeExisting(block)));
            ValidateCatalogue(result, officialDirectories, library);
            return result;
        }

        private static byte[] BuildCustomCatalogue(
            byte[] source, IList<MissionPackage> packages, byte[] originalSource = null)
        {
            List<GdtBlock> root;
            if (!TryParseBlocks(source, 0, source.Length, out root))
                throw new InvalidDataException("Catalogue Sabre Squadron illisible.");
            GdtBlock top = root.FirstOrDefault(block => block.Kind == 0x01);
            GdtBlock main = top == null ? null : Direct(top, 0x05);
            if (main == null) throw new InvalidDataException("Liste des campagnes absente.");
            List<GdtBlock> sourceCampaigns = main.Children
                .Where(block => block.Kind == 0x3C).ToList();
            if (sourceCampaigns.Count < CategoryOrder.Length)
                throw new InvalidDataException("Trois gabarits de campagne requis.");

            Dictionary<string, GdtBlock> templates = MissionTemplates(source, originalSource);

            Dictionary<int, List<MissionPackage>> grouped =
                new Dictionary<int, List<MissionPackage>>();
            for (int index = 0; index < CategoryOrder.Length; index++)
            {
                string category = CategoryOrder[index];
                List<MissionPackage> matches = packages.Where(item =>
                    String.Equals(item.Category, category, StringComparison.OrdinalIgnoreCase))
                    .ToList();
                if (matches.Count > 0) grouped[index] = matches;
            }

            int campaignIndex = 0;
            List<byte[]> mainContent = new List<byte[]>();
            foreach (GdtBlock child in main.Children)
            {
                if (child.Kind == 0x3C)
                {
                    List<MissionPackage> missions;
                    if (grouped.TryGetValue(campaignIndex, out missions))
                        mainContent.Add(RewriteCampaign(
                            child, CategoryIds[CategoryOrder[campaignIndex]], missions, templates));
                    campaignIndex++;
                }
                else mainContent.Add(EncodeExisting(child));
            }

            byte[] rebuiltMain = EncodeBlock(0x05, Join(mainContent));
            List<byte[]> topContent = new List<byte[]>();
            foreach (GdtBlock child in top.Children)
                topContent.Add(Object.ReferenceEquals(child, main)
                    ? rebuiltMain : EncodeExisting(child));
            byte[] rebuiltTop = EncodeBlock(0x01, Join(topContent));
            byte[] result = Join(root.Select(block =>
                Object.ReferenceEquals(block, top) ? rebuiltTop : EncodeExisting(block)));
            ValidateCustomCatalogue(result, packages);
            return result;
        }

        private static void ValidateCustomCatalogue(
            byte[] data, IList<MissionPackage> packages)
        {
            List<GdtBlock> root;
            if (!TryParseBlocks(data, 0, data.Length, out root))
                throw new InvalidDataException("Validation du catalogue personnalisé impossible.");
            List<string> expected = CategoryOrder.SelectMany(category => packages
                .Where(item => String.Equals(item.Category, category,
                    StringComparison.OrdinalIgnoreCase))
                .Select(item => item.MissionDirectory)).ToList();
            List<string> actual = Walk(root).Where(block => block.Kind == 0x32)
                .Select(block => Direct(block, 0x36)).Where(block => block != null)
                .Select(BlockString).ToList();
            if (!actual.SequenceEqual(expected, StringComparer.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Le catalogue personnalisé ne contient pas les missions attendues.");
        }

        private static MissionPackage TechnicalPackage(
            string category, int titleId, string missionDirectory)
        {
            return new MissionPackage {
                Id = RuntimeOwner + "." + category,
                Category = category,
                MissionDirectory = missionDirectory,
                TemplateMission = missionDirectory,
                TitleId = titleId,
                PreserveTemplateObjectives = true,
                Title = new LocalizedText()
            };
        }

        private static List<string> CatalogueMissionDirectories(
            byte[] source, string catalogueName)
        {
            List<GdtBlock> root;
            if (!TryParseBlocks(source, 0, source.Length, out root))
                throw new InvalidDataException(catalogueName + " illisible.");
            GdtBlock top = root.FirstOrDefault(block => block.Kind == 0x01);
            GdtBlock main = top == null ? null : Direct(top, 0x05);
            if (main == null)
                throw new InvalidDataException("Liste des campagnes absente de "
                    + catalogueName + ".");
            return Walk(main.Children).Where(block => block.Kind == 0x32)
                .Select(block => Direct(block, 0x36)).Where(block => block != null)
                .Select(BlockString).ToList();
        }

        private static Dictionary<string, byte[]> BuildCustomCatalogues(
            byte[] source, byte[] originalSource, MissionLibrary library)
        {
            List<GdtBlock> root;
            if (!TryParseBlocks(source, 0, source.Length, out root))
                throw new InvalidDataException("Catalogue Sabre Squadron illisible.");
            GdtBlock top = root.FirstOrDefault(block => block.Kind == 0x01);
            GdtBlock main = top == null ? null : Direct(top, 0x05);
            if (main == null) throw new InvalidDataException("Liste des campagnes absente.");
            List<string> expansionDirectories = Walk(main.Children)
                .Where(block => block.Kind == 0x32)
                .Select(block => Direct(block, 0x36)).Where(block => block != null)
                .Select(BlockString).ToList();
            List<string> originalDirectories = CatalogueMissionDirectories(
                originalSource, "Gamedata00.gdt");
            List<string> officialDirectories = originalDirectories
                .Concat(expansionDirectories).ToList();
            HashSet<string> official = new HashSet<string>(
                officialDirectories, StringComparer.OrdinalIgnoreCase);
            foreach (MissionPackage package in library.Packages)
                if (official.Contains(package.MissionDirectory))
                    throw new InvalidDataException(
                        "Le dossier de mission entre en conflit avec une mission officielle : "
                        + package.MissionDirectory);
            ValidateMenuRowLimit(officialDirectories.Count, library.Packages.Count);

            List<MissionPackage> categories = new List<MissionPackage> {
                TechnicalPackage("multiplayer-adaptation", 20410, "Brest"),
                TechnicalPackage("user-mission", 20411, "Libye1"),
                TechnicalPackage("free-exploration", 20412, "Sicily1")
            };
            Dictionary<string, byte[]> result =
                new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
            result["Gamedata02.gdt"] = BuildCustomCatalogue(source, categories, originalSource);
            for (int index = 0; index < CategoryOrder.Length; index++)
            {
                string category = CategoryOrder[index];
                List<MissionPackage> detail = library.Packages.Where(item =>
                    String.Equals(item.Category, category, StringComparison.OrdinalIgnoreCase))
                    .ToList();
                result["Gamedata" + (index + 3).ToString("D2") + ".gdt"] =
                    BuildCustomCatalogue(source, detail, originalSource);
            }
            return result;
        }

        private static void ValidateMenuRowLimit(int officialRows, int packageRows)
        {
            int totalRows = officialRows + CategoryOrder.Length + packageRows;
            if (totalRows > MaximumMenuRows)
                throw new InvalidDataException(
                    "Trop de missions pour le moteur du jeu : " + totalRows + "/"
                    + MaximumMenuRows + " lignes.");
        }

        private static void ValidateCatalogue(
            byte[] data, IList<string> officialDirectories, MissionLibrary library)
        {
            List<GdtBlock> root;
            if (!TryParseBlocks(data, 0, data.Length, out root))
                throw new InvalidDataException("Validation du catalogue généré impossible.");
            List<string> expected = officialDirectories.Concat(
                CategoryOrder.SelectMany(category => library.Packages
                .Where(item => String.Equals(item.Category, category, StringComparison.OrdinalIgnoreCase))
                .Select(item => item.MissionDirectory))).ToList();
            List<string> actual = Walk(root).Where(block => block.Kind == 0x32)
                .Select(block => Direct(block, 0x36)).Where(block => block != null)
                .Select(BlockString).ToList();
            if (!actual.SequenceEqual(expected, StringComparer.OrdinalIgnoreCase))
                throw new InvalidDataException("Le catalogue généré ne contient pas les missions attendues.");
        }

        private static Dictionary<string, byte[]> BuildTextTables(
            string testGame, MissionLibrary library)
        {
            string textRoot = Path.Combine(testGame, "Text");
            if (!Directory.Exists(textRoot)) throw new DirectoryNotFoundException("Dossier Text introuvable.");
            Dictionary<string, byte[]> result = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
            foreach (string languageRoot in Directory.GetDirectories(textRoot))
            {
                string path = Path.Combine(languageRoot, "TEXTY_DD.txt");
                if (!File.Exists(path)) continue;
                string language = Path.GetFileName(languageRoot);
                Encoding encoding = String.Equals(language, "czech", StringComparison.OrdinalIgnoreCase)
                    ? Encoding.GetEncoding(1250)
                    : String.Equals(language, "japan", StringComparison.OrdinalIgnoreCase)
                        ? new UTF8Encoding(false) : Encoding.GetEncoding(1252);
                string relative = Path.GetFullPath(path).Substring(
                    Path.GetFullPath(testGame).TrimEnd(Path.DirectorySeparatorChar).Length)
                    .TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
                string backup = Path.Combine(testGame, "STATIC_MENU_BACKUP", relative);
                byte[] original = File.ReadAllBytes(
                    File.Exists(backup) ? backup : path);
                string text = encoding.GetString(original);
                string separator = text.Contains("\r\n") ? "\r\n" : "\n";
                Dictionary<int, string> values = new Dictionary<int, string>();
                values[20499] = " ";
                values[20402] = MenuName(20402, language);
                values[20413] = MenuName(20413, language);
                foreach (string category in CategoryOrder)
                    values[CategoryIds[category]] = CategoryName(category, language);
                foreach (MissionPackage package in library.Packages)
                {
                    values[package.TitleId] = package.Title.ForLanguage(language);
                    for (int index = 0; index < package.Objectives.Count; index++)
                        values[package.ObjectiveIds[index]] = package.Objectives[index].ForLanguage(language);
                }
                foreach (KeyValuePair<int, string> pair in values)
                {
                    string line = pair.Key + "\t\"" + pair.Value + "\"";
                    Regex pattern = new Regex(
                        "^[ \\t]*" + pair.Key + "\\b[^\\r\\n]*", RegexOptions.Multiline);
                    if (pattern.IsMatch(text))
                        text = pattern.Replace(text, delegate(Match ignored) { return line; });
                    else
                    {
                        if (text.Length > 0 && !text.EndsWith("\r") && !text.EndsWith("\n"))
                            text += separator;
                        text += line + separator;
                    }
                }
                result[path] = encoding.GetBytes(text);
            }
            if (result.Count == 0) throw new InvalidDataException("Aucune table TEXTY_DD.txt trouvée.");
            return result;
        }

        private static void WriteUInt16(byte[] data, int offset, ushort value)
        {
            byte[] encoded = BitConverter.GetBytes(value);
            Buffer.BlockCopy(encoded, 0, data, offset, encoded.Length);
        }

        private static void WriteSingle(byte[] data, int offset, float value)
        {
            byte[] encoded = BitConverter.GetBytes(value);
            Buffer.BlockCopy(encoded, 0, data, offset, encoded.Length);
        }

        private static byte[] CloneSceneRecord(
            byte[] source, int start, int end,
            int nameLengthOffset, int nameOffset, int oldNameLength, string replacement,
            int parentOffset, ushort parentId, int positionOffset, float[] position)
        {
            byte[] name = Encoding.ASCII.GetBytes(replacement);
            if (name.Length > Byte.MaxValue)
                throw new InvalidDataException("Nom de contrôle 4DS trop long.");
            int prefixLength = nameLengthOffset - start;
            int suffixOffset = nameOffset + oldNameLength;
            byte[] record = new byte[prefixLength + 1 + name.Length + end - suffixOffset];
            Buffer.BlockCopy(source, start, record, 0, prefixLength);
            record[prefixLength] = (byte)name.Length;
            Buffer.BlockCopy(name, 0, record, prefixLength + 1, name.Length);
            Buffer.BlockCopy(source, suffixOffset, record, prefixLength + 1 + name.Length,
                end - suffixOffset);
            WriteUInt16(record, parentOffset - start, parentId);
            if (position != null)
                for (int axis = 0; axis < 3; axis++)
                    WriteSingle(record, positionOffset - start + axis * 4, position[axis]);
            return record;
        }

        private static byte[] AssembleScene(
            byte[] source, int tableEnd, int nodeCountOffset, ushort nodeCount,
            IEnumerable<byte[]> clones)
        {
            List<byte[]> records = clones.ToList();
            int length = source.Length + records.Sum(record => record.Length);
            byte[] result = new byte[length];
            Buffer.BlockCopy(source, 0, result, 0, tableEnd);
            int cursor = tableEnd;
            foreach (byte[] record in records)
            {
                Buffer.BlockCopy(record, 0, result, cursor, record.Length);
                cursor += record.Length;
            }
            Buffer.BlockCopy(source, tableEnd, result, cursor, source.Length - tableEnd);
            WriteUInt16(result, nodeCountOffset, nodeCount);
            return result;
        }

        private static byte[] BuildSinglePlayerScene(byte[] source)
        {
            const string sourceHash =
                "2B5737C979063BEDADCB2F716CE2CB84E2DDB8DD9BE5EF98E7DF9743A2EAC97D";
            const string resultHash =
                "7A605F3077DBAD273A08D76934731FC7EFBDB15692BDD0922781DB5E49809A62";
            if (!String.Equals(Sha256(source), sourceHash, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Modèle Models/singleplayer.4ds non pris en charge.");
            List<byte[]> clones = new List<byte[]> {
                CloneSceneRecord(source, 3790, 3887, 3838, 3839, 15,
                    "bcampaign02", 3791, 0, 3793,
                    new[] { 1.223745346069336f, 0.08429983258247375f,
                        -3.6848626372432136e-09f }),
                CloneSceneRecord(source, 3887, 4107, 3938, 3939, 9,
                    "actived10", 3891, 43, 3893,
                    new[] { 0.03888195753097534f, 0.06750348210334778f,
                        -0.684241533279419f }),
                CloneSceneRecord(source, 4107, 4326, 4158, 4159, 8,
                    "normal10", 4111, 43, 4113,
                    new[] { -0.5084920525550842f, 0.06750348210334778f,
                        -0.6833477020263672f })
            };
            byte[] result = AssembleScene(source, 11718, 2199, 45, clones);
            if (!String.Equals(Sha256(result), resultHash, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Validation du nouveau menu Solo impossible.");
            return result;
        }

        private static byte[] BuildSingleMissionScene(byte[] source)
        {
            const string sourceHash =
                "BE8A5A85230BC67E335E469EE7093C77816C51D4E12C829BF737CA7B6727E50F";
            const string resultHash =
                "A18B5883DF7EAC40A32ECBDC40D5D7968A30DCC0F51D8565F38807711B89B084";
            if (!String.Equals(Sha256(source), sourceHash, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Modèle Models/single mission 2.4ds non pris en charge.");
            List<byte[]> clones = new List<byte[]>();
            string[] roots = { "bcustom user", "bcustom multi", "bcustom explore" };
            string[] normals = { "normal11", "normal12", "normal13" };
            string[] actives = { "actived11", "actived12", "actived13" };
            ushort[] parents = { 41, 44, 47 };
            float[] normalZ = { -0.2370000034570694f, -0.3230000138282776f,
                -0.4090000092983246f };
            float[] activeZ = { -0.2409999966621399f, -0.3269999921321869f,
                -0.4129999876022339f };
            for (int index = 0; index < roots.Length; index++)
            {
                clones.Add(CloneSceneRecord(source, 2563, 2650, 2611, 2612, 5,
                    roots[index], 2564, 0, 2566, null));
                clones.Add(CloneSceneRecord(source, 2650, 2869, 2701, 2702, 8,
                    normals[index], 2654, parents[index], 2656,
                    new[] { -0.3327277898788452f, 0.06750348210334778f,
                        normalZ[index] }));
                clones.Add(CloneSceneRecord(source, 2869, 3089, 2920, 2921, 9,
                    actives[index], 2873, parents[index], 2875,
                    new[] { 0.21464622020721436f, 0.06750348210334778f,
                        activeZ[index] }));
            }
            byte[] result = AssembleScene(source, 12213, 1747, 49, clones);
            if (!String.Equals(Sha256(result), resultHash, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Validation du sous-menu de missions personnalisées impossible.");
            return result;
        }

        private static byte[] ReadMenuModule()
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(MenuModuleResource))
            {
                if (stream == null)
                    throw new InvalidDataException(
                        "Module HD2.CustomMenu.asi absent du gestionnaire.");
                using (MemoryStream output = new MemoryStream())
                {
                    stream.CopyTo(output);
                    byte[] result = output.ToArray();
                    if (result.Length < 4096 || result[0] != (byte)'M'
                        || result[1] != (byte)'Z')
                        throw new InvalidDataException("Module HD2.CustomMenu.asi invalide.");
                    int peOffset = BitConverter.ToInt32(result, 0x3c);
                    if (peOffset < 0x40 || peOffset + 6 > result.Length
                        || result[peOffset] != (byte)'P' || result[peOffset + 1] != (byte)'E'
                        || result[peOffset + 2] != 0 || result[peOffset + 3] != 0
                        || BitConverter.ToUInt16(result, peOffset + 4) != 0x014c)
                        throw new InvalidDataException(
                            "Module HD2.CustomMenu.asi invalide ou non x86.");
                    return result;
                }
            }
        }

        private static Dictionary<string, byte[]> BuildRuntimeFiles(
            string originalGame, MissionLibrary library, byte[] sourceCatalogue)
        {
            Dictionary<string, byte[]> result =
                new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
            foreach (KeyValuePair<string, byte[]> catalogue in
                BuildCustomCatalogues(sourceCatalogue,
                    ReadArchiveEntry(originalGame, "GameData\\Gamedata00.gdt"), library))
                result["GameData/" + catalogue.Key] = catalogue.Value;
            result["Models/singleplayer.4ds"] = BuildSinglePlayerScene(
                ReadArchiveEntry(originalGame, "Models\\singleplayer.4ds"));
            result["Models/single mission 2.4ds"] = BuildSingleMissionScene(
                ReadArchiveEntry(originalGame, "Models\\single mission 2.4ds"));
            result["Scripts/HD2.CustomMenu.asi"] = ReadMenuModule();
            return result;
        }

        private static string SafeGameTarget(string game, string relative)
        {
            string root = Path.GetFullPath(game).TrimEnd(Path.DirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            string target = Path.GetFullPath(Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
            if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Chemin hors de la copie de test : " + relative);
            return target;
        }

        private static void PlanBackupIfNeeded(
            FileTransaction transaction, string game, string target)
        {
            if (!File.Exists(target)) return;
            string root = Path.GetFullPath(game).TrimEnd(Path.DirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            string full = Path.GetFullPath(target);
            if (!full.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Sauvegarde hors de la copie de test.");
            string relative = full.Substring(root.Length);
            string backup = Path.Combine(game, "STATIC_MENU_BACKUP", relative);
            if (File.Exists(backup)) return;
            transaction.AddWrite(backup, File.ReadAllBytes(full));
        }

        internal static void WriteAtomic(string path, byte[] data)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path)));
            string temporary = path + ".custom-mission.tmp";
            try
            {
                File.WriteAllBytes(temporary, data);
                if (File.Exists(path)) File.Replace(temporary, path, null);
                else File.Move(temporary, path);
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        private static string Sha256(byte[] data)
        {
            using (SHA256 algorithm = SHA256.Create())
                return BitConverter.ToString(algorithm.ComputeHash(data)).Replace("-", "");
        }

        private static string Sha256File(string path)
        {
            using (FileStream input = File.OpenRead(path))
            using (SHA256 algorithm = SHA256.Create())
                return BitConverter.ToString(algorithm.ComputeHash(input)).Replace("-", "");
        }

        private static Dictionary<string, ManagedFile> ReadManagedState(string game)
        {
            Dictionary<string, ManagedFile> result =
                new Dictionary<string, ManagedFile>(StringComparer.OrdinalIgnoreCase);
            string path = Path.Combine(game, "STATIC_MENU_MANAGED_FILES.json");
            if (!File.Exists(path)) return result;
            Dictionary<string, object> document = AsObject(
                Json.DeserializeObject(File.ReadAllText(path, Encoding.UTF8)), path);
            object format;
            if (!document.TryGetValue("format", out format) || Convert.ToInt32(format) != 1)
                throw new InvalidDataException("Journal des fichiers personnalisés invalide.");
            object rawFiles;
            if (!document.TryGetValue("files", out rawFiles)) return result;
            foreach (object raw in AsList(rawFiles, path + ".files"))
            {
                Dictionary<string, object> item = AsObject(raw, path + ".file");
                string relative = Convert.ToString(item["relative"]);
                ManagedFile file = new ManagedFile {
                    Relative = relative,
                    Created = Convert.ToBoolean(item["created"]),
                    Sha256 = Convert.ToString(item["sha256"]),
                    BackupSha256 = item.ContainsKey("backup_sha256")
                        ? Convert.ToString(item["backup_sha256"]) : "",
                    PackageId = item.ContainsKey("package_id") ? Convert.ToString(item["package_id"]) : ""
                };
                result[relative] = file;
            }
            return result;
        }

        private static byte[] ManagedStateBytes(Dictionary<string, ManagedFile> managed)
        {
            List<Dictionary<string, object>> files = new List<Dictionary<string, object>>();
            foreach (ManagedFile file in managed.Values.OrderBy(item => item.Relative, StringComparer.OrdinalIgnoreCase))
            {
                Dictionary<string, object> record = new Dictionary<string, object>();
                record["relative"] = file.Relative;
                record["created"] = file.Created;
                record["sha256"] = file.Sha256;
                if (!file.Created) record["backup_sha256"] = file.BackupSha256;
                record["package_id"] = file.PackageId;
                files.Add(record);
            }
            Dictionary<string, object> document = new Dictionary<string, object>();
            document["format"] = 1;
            document["files"] = files;
            return new UTF8Encoding(false).GetBytes(Json.Serialize(document));
        }

        private static void WriteManagedState(
            string game, Dictionary<string, ManagedFile> managed)
        {
            WriteAtomic(Path.Combine(game, "STATIC_MENU_MANAGED_FILES.json"),
                ManagedStateBytes(managed));
        }

        private static void ValidatePreparedTestGame(string originalGame, string testGame)
        {
            string original = Path.GetFullPath(originalGame).TrimEnd(Path.DirectorySeparatorChar);
            string target = Path.GetFullPath(testGame).TrimEnd(Path.DirectorySeparatorChar);
            if (!File.Exists(Path.Combine(original, "SabreSquadron.dta")))
                throw new InvalidDataException("Installation originale Sabre Squadron introuvable.");
            string executable = Path.Combine(target, "HD2_SabreSquadron.exe");
            if (!File.Exists(executable) || !File.Exists(Path.Combine(target, "SabreSquadron.dta")))
                throw new InvalidDataException("Installation Sabre Squadron incomplète.");
            string executableHash = Sha256File(executable);
            if (!String.Equals(executableHash, ExpectedExecutableSha256,
                StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Version de HD2_SabreSquadron.exe non prise en charge. "
                    + "Le menu personnalisé exige le client 1.12 original vérifié.");
            string asiLoader = Path.Combine(target, "d3d8.dll");
            if (!File.Exists(asiLoader))
                throw new InvalidDataException(
                    "Chargeur ASI absent (d3d8.dll). Installez d'abord le correctif écran large "
                    + "fourni avec le Heritage Pack.");
            if (!String.Equals(Sha256File(asiLoader), ExpectedAsiLoaderSha256,
                StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Le fichier d3d8.dll n'est pas le chargeur ASI vérifié du Heritage Pack. "
                    + "Réinstallez le correctif écran large avant le menu personnalisé.");
            byte[] executableBytes = File.ReadAllBytes(executable);
            if (Encoding.ASCII.GetString(executableBytes).Contains(".patch"))
                throw new InvalidDataException(
                    "L'exécutable du jeu contient l'ancien correctif détecté par les antivirus. "
                    + "Restaurez d'abord HD2_SabreSquadron.exe depuis l'original.");
            string executableBackup = Path.Combine(target, "HD2_SabreSquadron.original.exe");
            if (File.Exists(executableBackup)
                && !String.Equals(Sha256File(executable), Sha256File(executableBackup),
                    StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "L'exécutable actif diffère de sa sauvegarde originale; intégration refusée.");
            ValidateNoGameProcess();
        }

        public static string ValidateLibrary(string libraryRoot)
        {
            MissionLibrary library = LoadLibrary(libraryRoot, false);
            return "Bibliothèque valide : " + library.Packages.Count + " mission(s), "
                + library.FileCount + " fichier(s).";
        }

        public static string BuildCatalogueForTest(
            string libraryRoot, string originalGame, string outputPath)
        {
            MissionLibrary library = LoadLibrary(libraryRoot, false);
            if (library.Packages.Count == 0) throw new InvalidDataException("Bibliothèque vide.");
            byte[] result = BuildCatalogue(ReadSourceCatalogue(originalGame), library,
                ReadArchiveEntry(originalGame, "GameData\\Gamedata00.gdt"));
            if (!String.IsNullOrWhiteSpace(outputPath)) WriteAtomic(outputPath, result);
            return Sha256(result);
        }

        public static string RuntimeHashesForTest(
            string libraryRoot, string originalGame)
        {
            MissionLibrary library = LoadLibrary(libraryRoot, false);
            Dictionary<string, byte[]> files = BuildRuntimeFiles(
                Path.GetFullPath(originalGame), library, ReadSourceCatalogue(originalGame));
            Dictionary<string, string> hashes = new Dictionary<string, string>();
            foreach (KeyValuePair<string, byte[]> file in files)
                hashes[file.Key] = Sha256(file.Value);
            return Json.Serialize(hashes);
        }

        private static Dictionary<string, ManagedFile> CloneManagedState(
            Dictionary<string, ManagedFile> source)
        {
            Dictionary<string, ManagedFile> result =
                new Dictionary<string, ManagedFile>(StringComparer.OrdinalIgnoreCase);
            foreach (KeyValuePair<string, ManagedFile> pair in source)
                result[pair.Key] = new ManagedFile {
                    Relative = pair.Value.Relative,
                    Created = pair.Value.Created,
                    Sha256 = pair.Value.Sha256,
                    BackupSha256 = pair.Value.BackupSha256,
                    PackageId = pair.Value.PackageId
                };
            return result;
        }

        private static bool CurrentMatchesManaged(string game, ManagedFile file)
        {
            string target = SafeGameTarget(game, file.Relative);
            return File.Exists(target)
                && !String.IsNullOrWhiteSpace(file.Sha256)
                && String.Equals(
                    Sha256File(target), file.Sha256, StringComparison.OrdinalIgnoreCase);
        }

        private static void EnsureManagedOverwriteSafe(
            string game, ManagedFile previous)
        {
            if (!CurrentMatchesManaged(game, previous))
                throw new InvalidDataException(
                    "Le fichier déjà géré a été modifié ou supprimé depuis la dernière intégration : "
                    + previous.Relative + ". Il est conservé; remettez-le en état ou restaurez-le "
                    + "explicitement avant de réintégrer ce paquet.");
            if (!previous.Created)
            {
                string backup = Path.Combine(game, "STATIC_MENU_BACKUP",
                    previous.Relative.Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(backup))
                    throw new FileNotFoundException(
                        "Sauvegarde d'origine absente pour le fichier déjà géré : "
                        + previous.Relative, backup);
                string actual = Sha256File(backup);
                if (!String.IsNullOrWhiteSpace(previous.BackupSha256)
                    && !String.Equals(actual, previous.BackupSha256,
                        StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "La sauvegarde d'origine a été modifiée : " + previous.Relative);
                previous.BackupSha256 = actual;
            }
        }

        private static byte[] ReadManagedBackup(string game, ManagedFile file)
        {
            string backup = Path.Combine(game, "STATIC_MENU_BACKUP",
                file.Relative.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(backup))
                throw new FileNotFoundException(
                    "Sauvegarde absente pour le fichier géré : " + file.Relative, backup);
            byte[] data = File.ReadAllBytes(backup);
            string actual = Sha256(data);
            if (!String.IsNullOrWhiteSpace(file.BackupSha256)
                && !String.Equals(actual, file.BackupSha256,
                    StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "La sauvegarde d'origine a été modifiée : " + file.Relative);
            file.BackupSha256 = actual;
            return data;
        }

        private static void PlanRemovedManagedFiles(
            string game, HashSet<string> desired,
            Dictionary<string, ManagedFile> managed, FileTransaction transaction,
            ref int cleaned, ref int preserved)
        {
            foreach (ManagedFile file in managed.Values.ToList())
            {
                if (desired.Contains(file.Relative)) continue;
                if (!CurrentMatchesManaged(game, file))
                {
                    preserved++;
                    continue;
                }
                string target = SafeGameTarget(game, file.Relative);
                if (file.Created)
                    transaction.AddDelete(target);
                else
                    transaction.AddWrite(target, ReadManagedBackup(game, file));
                managed.Remove(file.Relative);
                cleaned++;
            }
        }

        private static void PlanRestoreManagedFiles(
            string game, Dictionary<string, ManagedFile> managed,
            FileTransaction transaction, ref int restored, ref int preserved)
        {
            foreach (ManagedFile file in managed.Values.ToList())
            {
                if (!CurrentMatchesManaged(game, file))
                {
                    preserved++;
                    continue;
                }
                string target = SafeGameTarget(game, file.Relative);
                if (file.Created)
                    transaction.AddDelete(target);
                else
                    transaction.AddWrite(target, ReadManagedBackup(game, file));
                managed.Remove(file.Relative);
                restored++;
            }
        }

        private static Dictionary<string, string> ReadInstallHashMap(
            string game, string section)
        {
            Dictionary<string, string> result =
                new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            string path = Path.Combine(game, "CUSTOM_MISSIONS_INSTALL.json");
            if (!File.Exists(path)) return result;
            Dictionary<string, object> document = AsObject(
                Json.DeserializeObject(File.ReadAllText(path, Encoding.UTF8)), path);
            object raw;
            if (!document.TryGetValue(section, out raw) || raw == null) return result;
            foreach (KeyValuePair<string, object> pair in AsObject(raw, path + "." + section))
                result[pair.Key] = Convert.ToString(pair.Value);
            return result;
        }

        private static void PlanRestoreGeneratedFile(
            string game, string relative, string installedHash,
            FileTransaction transaction, ref int restored, ref int preserved)
        {
            string target = SafeGameTarget(game, relative);
            if (String.IsNullOrWhiteSpace(installedHash) || !File.Exists(target)
                || !String.Equals(
                    Sha256File(target), installedHash, StringComparison.OrdinalIgnoreCase))
            {
                preserved++;
                return;
            }
            string backup = Path.Combine(game, "STATIC_MENU_BACKUP",
                relative.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(backup))
                throw new FileNotFoundException(
                    "Sauvegarde absente pour le fichier généré : " + relative, backup);
            transaction.AddWrite(target, File.ReadAllBytes(backup));
            restored++;
        }

        private static bool PlanLegacyCatalogueMigration(
            string game, FileTransaction transaction)
        {
            Dictionary<string, string> hashes =
                ReadInstallHashMap(game, "catalogue_sha256");
            string installedHash;
            if (!hashes.TryGetValue("Gamedata01.gdt", out installedHash))
                return false;
            string relative = "GameData/Gamedata01.gdt";
            string target = SafeGameTarget(game, relative);
            if (!File.Exists(target) || String.IsNullOrWhiteSpace(installedHash)
                || !String.Equals(Sha256File(target), installedHash,
                    StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "L'ancien catalogue personnalisé a été modifié. Restaurez-le avec "
                    + "l'ancienne version du gestionnaire avant la migration.");
            string backup = Path.Combine(game, "STATIC_MENU_BACKUP", "GameData",
                "Gamedata01.gdt");
            if (!File.Exists(backup))
                throw new FileNotFoundException(
                    "Sauvegarde de l'ancien Gamedata01.gdt absente; migration refusée.",
                    backup);
            transaction.AddWrite(target, File.ReadAllBytes(backup));
            return true;
        }

        private static void RegisterManagedOutput(
            string game, Dictionary<string, ManagedFile> managed,
            HashSet<string> desired, string relative, byte[] data, string owner)
        {
            relative = relative.Replace('\\', '/');
            string target = SafeGameTarget(game, relative);
            ManagedFile previous;
            bool created;
            string backupSha256 = "";
            if (managed.TryGetValue(relative, out previous))
            {
                EnsureManagedOverwriteSafe(game, previous);
                created = previous.Created;
                backupSha256 = previous.BackupSha256;
            }
            else
            {
                created = !File.Exists(target);
                if (!created)
                {
                    string backup = Path.Combine(game, "STATIC_MENU_BACKUP",
                        relative.Replace('/', Path.DirectorySeparatorChar));
                    backupSha256 = File.Exists(backup)
                        ? Sha256File(backup) : Sha256File(target);
                }
            }
            managed[relative] = new ManagedFile {
                Relative = relative,
                Created = created,
                Sha256 = Sha256(data),
                BackupSha256 = backupSha256,
                PackageId = owner
            };
            desired.Add(relative);
        }

        public static string Integrate(
            string libraryRoot, string originalGame, string testGame)
        {
            MissionLibrary library = LoadLibrary(libraryRoot, false);
            originalGame = Path.GetFullPath(originalGame);
            testGame = Path.GetFullPath(testGame);
            ValidatePreparedTestGame(originalGame, testGame);
            byte[] sourceCatalogue = ReadSourceCatalogue(originalGame);
            Dictionary<string, byte[]> outputs =
                BuildRuntimeFiles(originalGame, library, sourceCatalogue);
            Dictionary<string, byte[]> textTables = BuildTextTables(testGame, library);
            string gameRoot = testGame.TrimEnd(Path.DirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            foreach (KeyValuePair<string, byte[]> table in textTables)
            {
                string relative = Path.GetFullPath(table.Key).Substring(gameRoot.Length)
                    .Replace('\\', '/');
                if (outputs.ContainsKey(relative))
                    throw new InvalidDataException("Fichier généré deux fois : " + relative);
                outputs[relative] = table.Value;
            }
            Dictionary<string, ManagedFile> managed =
                CloneManagedState(ReadManagedState(testGame));
            HashSet<string> desired =
                new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            List<Tuple<MissionPackage, PayloadFile, string, byte[]>> payload =
                new List<Tuple<MissionPackage, PayloadFile, string, byte[]>>();
            foreach (KeyValuePair<string, byte[]> output in outputs)
                RegisterManagedOutput(
                    testGame, managed, desired, output.Key, output.Value, RuntimeOwner);
            foreach (MissionPackage package in library.Packages)
                foreach (PayloadFile file in package.Files)
                {
                    if (outputs.ContainsKey(file.Relative))
                        throw new InvalidDataException(
                            "Un paquet tente de remplacer un fichier réservé au menu : "
                            + file.Relative);
                    string target = SafeGameTarget(testGame, file.Relative);
                    byte[] data = File.ReadAllBytes(file.Source);
                    RegisterManagedOutput(
                        testGame, managed, desired, file.Relative, data, package.Id);
                    payload.Add(Tuple.Create(package, file, target, data));
                }

            FileTransaction transaction = new FileTransaction(null);
            int cleaned = 0;
            int preserved = 0;
            bool migratedLegacyCatalogue =
                PlanLegacyCatalogueMigration(testGame, transaction);
            PlanRemovedManagedFiles(
                testGame, desired, managed, transaction, ref cleaned, ref preserved);
            foreach (string relative in outputs.Keys)
                if (!managed[relative].Created)
                    PlanBackupIfNeeded(
                        transaction, testGame, SafeGameTarget(testGame, relative));
            foreach (Tuple<MissionPackage, PayloadFile, string, byte[]> item in payload)
                if (!managed[item.Item2.Relative].Created)
                    PlanBackupIfNeeded(transaction, testGame, item.Item3);

            foreach (KeyValuePair<string, byte[]> output in outputs)
                transaction.AddWrite(
                    SafeGameTarget(testGame, output.Key), output.Value);
            foreach (Tuple<MissionPackage, PayloadFile, string, byte[]> item in payload)
                transaction.AddWrite(item.Item3, item.Item4);
            transaction.AddWrite(
                Path.Combine(testGame, "STATIC_MENU_MANAGED_FILES.json"),
                ManagedStateBytes(managed));
            if (library.RegistryChanged)
                transaction.AddWrite(
                    Path.Combine(library.Root, RegistryName), RegistryBytes(library));

            Dictionary<string, object> report = new Dictionary<string, object>();
            report["status"] =
                "CUSTOM_MISSIONS_INSTALLED_THREE_LIST_GUI_GAME_NOT_LAUNCHED";
            report["missions"] = library.Packages.Count;
            report["payload_files"] = library.FileCount;
            report["migrated_legacy_catalogue"] = migratedLegacyCatalogue;
            Dictionary<string, string> catalogueHashes = new Dictionary<string, string>();
            foreach (KeyValuePair<string, byte[]> output in outputs)
                if (output.Key.StartsWith("GameData/", StringComparison.OrdinalIgnoreCase))
                    catalogueHashes[Path.GetFileName(output.Key)] = Sha256(output.Value);
            report["catalogue_sha256"] = catalogueHashes;
            Dictionary<string, string> textHashes = new Dictionary<string, string>();
            foreach (KeyValuePair<string, byte[]> output in outputs)
                if (output.Key.StartsWith("Text/", StringComparison.OrdinalIgnoreCase))
                    textHashes[output.Key] = Sha256(output.Value);
            report["text_table_sha256"] = textHashes;
            Dictionary<string, string> runtimeHashes = new Dictionary<string, string>();
            foreach (KeyValuePair<string, byte[]> output in outputs)
                runtimeHashes[output.Key] = Sha256(output.Value);
            report["runtime_sha256"] = runtimeHashes;
            report["library"] = library.Root;
            transaction.AddWrite(
                Path.Combine(testGame, "CUSTOM_MISSIONS_INSTALL.json"),
                new UTF8Encoding(false).GetBytes(Json.Serialize(report)));
            transaction.Commit();
            library.RegistryChanged = false;
            return library.Packages.Count + " mission(s) intégrée(s), " + library.FileCount
                + " fichier(s) copiés, " + cleaned + " ancien(s) fichier(s) retiré(s), "
                + preserved + " fichier(s) modifié(s) conservé(s). Les trois listes et le menu "
                + "personnalisé sont installés. Le jeu n'a pas été lancé.";
        }

        public static string Restore(string testGame)
        {
            testGame = Path.GetFullPath(testGame);
            ValidateNoGameProcess();
            Dictionary<string, ManagedFile> managed =
                CloneManagedState(ReadManagedState(testGame));
            bool currentRuntime = managed.Values.Any(file =>
                String.Equals(file.PackageId, RuntimeOwner, StringComparison.OrdinalIgnoreCase));
            int restored = 0;
            int preserved = 0;
            FileTransaction transaction = new FileTransaction(null);
            PlanRestoreManagedFiles(
                testGame, managed, transaction, ref restored, ref preserved);
            Dictionary<string, string> catalogueHashes =
                ReadInstallHashMap(testGame, "catalogue_sha256");
            string catalogueExpected;
            if (catalogueHashes.TryGetValue("Gamedata01.gdt", out catalogueExpected))
                PlanRestoreGeneratedFile(
                    testGame, "GameData/Gamedata01.gdt", catalogueExpected,
                    transaction, ref restored, ref preserved);
            if (!currentRuntime)
            {
                Dictionary<string, string> textHashes = ReadInstallHashMap(
                    testGame, "text_table_sha256");
                foreach (KeyValuePair<string, string> table in textHashes)
                    PlanRestoreGeneratedFile(
                        testGame, table.Key, table.Value,
                        transaction, ref restored, ref preserved);
            }
            transaction.AddWrite(
                Path.Combine(testGame, "STATIC_MENU_MANAGED_FILES.json"),
                ManagedStateBytes(managed));
            string reportPath = Path.Combine(testGame, "CUSTOM_MISSIONS_INSTALL.json");
            if (preserved == 0 && managed.Count == 0)
            {
                if (File.Exists(reportPath)) transaction.AddDelete(reportPath);
            }
            else
            {
                Dictionary<string, object> restoreReport = new Dictionary<string, object>();
                restoreReport["status"] = "CUSTOM_MISSIONS_PARTIALLY_RESTORED_GAME_NOT_LAUNCHED";
                restoreReport["preserved_files"] = preserved;
                transaction.AddWrite(reportPath,
                    new UTF8Encoding(false).GetBytes(Json.Serialize(restoreReport)));
            }
            transaction.Commit();
            return restored + " fichier(s) restauré(s). " + preserved
                + " fichier(s) modifié(s) conservé(s). Le jeu n'a pas été lancé.";
        }

        private static void SafetyAssert(bool condition, string message)
        {
            if (!condition) throw new InvalidOperationException("Auto-test : " + message);
        }

        private static void SafetyWrite(string path, string value)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, value, new UTF8Encoding(false));
        }

        private static void SafetyLibraryRefused(string library, string message)
        {
            bool refused = false;
            try { LoadLibrary(library, false); }
            catch (InvalidDataException) { refused = true; }
            SafetyAssert(refused, message);
        }

        private static void RunMissionFolderSelfTests(string root)
        {
            string library = Path.Combine(root, "direct-folders");
            string mission = Path.Combine(library, "Operation Test Joueur");
            SafetyWrite(Path.Combine(mission, "tree.klz"), "test-tree");
            SafetyWrite(Path.Combine(mission, "briefing.txt"), "briefing");
            SafetyWrite(Path.Combine(mission, "Objects", "object.bin"), "object");
            foreach (string resource in AllowedRoots.Where(item => item != "Missions"))
                SafetyWrite(Path.Combine(mission, resource, "resource.bin"), resource);
            Directory.CreateDirectory(Path.Combine(library, "_modele"));
            Directory.CreateDirectory(Path.Combine(library, ".cache"));
            Dictionary<string, string> before = Directory.GetFiles(
                library, "*", SearchOption.AllDirectories).ToDictionary(
                    path => path, path => Sha256File(path), StringComparer.OrdinalIgnoreCase);
            MissionLibrary direct = LoadLibrary(library, false);
            MissionPackage first = direct.Packages.Single();
            SafetyAssert(first.Category == "user-mission"
                && first.MissionDirectory == "Operation Test Joueur"
                && first.Title.ForLanguage("french") == "Operation Test Joueur",
                "le dossier brut avec espaces n'a pas gardé son nom/titre/catégorie.");
            HashSet<string> destinations = new HashSet<string>(
                first.Files.Select(file => file.Relative), StringComparer.OrdinalIgnoreCase);
            SafetyAssert(destinations.Contains("Missions/Operation Test Joueur/tree.klz")
                && destinations.Contains("Missions/Operation Test Joueur/briefing.txt")
                && destinations.Contains("Missions/Operation Test Joueur/Objects/object.bin")
                && AllowedRoots.Where(item => item != "Missions").All(
                    resource => destinations.Contains(resource + "/resource.bin"))
                && destinations.Count == 9,
                "les fichiers directs ou les ressources du dossier brut sont mal orientés.");
            MissionPackage again = LoadLibrary(library, false).Packages.Single();
            SafetyAssert(first.Id == again.Id && first.TitleId == again.TitleId
                && PackageIdPattern.IsMatch(first.Id),
                "l'identifiant du dossier brut n'est pas stable.");
            SafetyAssert(Directory.GetFiles(library, "*", SearchOption.AllDirectories)
                    .Length == before.Count
                && before.All(file => Sha256File(file.Key) == file.Value)
                && !File.Exists(Path.Combine(mission, "mission.json"))
                && !File.Exists(Path.Combine(library, RegistryName)),
                "le scan a modifié les sources ou créé un manifeste/registre.");

            string similar = Path.Combine(library, "Operation-Test-Joueur");
            SafetyWrite(Path.Combine(similar, "tree.klz"), "test-tree-2");
            MissionLibrary similarNames = LoadLibrary(library, false);
            SafetyAssert(similarNames.Packages.Select(item => item.Id).Distinct().Count() == 2
                && similarNames.Packages.First(item => item.MissionDirectory
                    == "Operation Test Joueur").Id == first.Id,
                "deux noms normalisés similaires produisent le même identifiant.");

            string structuredLibrary = Path.Combine(root, "structured-folders");
            string structured = Path.Combine(structuredLibrary, "Titre du joueur");
            SafetyWrite(Path.Combine(structured, "Missions", "InternalName", "tree.klz"), "tree");
            SafetyWrite(Path.Combine(structured, "Maps", "map.bin"), "map");
            SafetyWrite(Path.Combine(structured, "README.txt"), "readme non installé");
            MissionPackage structure = LoadLibrary(structuredLibrary, false).Packages.Single();
            SafetyAssert(structure.MissionDirectory == "InternalName"
                && structure.Title.ForLanguage("english") == "Titre du joueur"
                && structure.Files.Any(file => file.Relative == "Maps/map.bin")
                && structure.Files.Any(file => file.Relative == "Missions/InternalName/tree.klz")
                && structure.Files.Count == 2,
                "la structure Missions et ses ressources ne sont pas reconnues.");

            string wrapped = Path.Combine(structuredLibrary, "Paquet sans manifeste", "payload");
            SafetyWrite(Path.Combine(wrapped, "Missions", "WrappedName", "tree.klz"), "tree");
            SafetyWrite(Path.Combine(wrapped, "Models", "model.bin"), "model");
            MissionPackage wrappedPackage = LoadLibrary(structuredLibrary, false).Packages
                .Single(item => item.MissionDirectory == "WrappedName");
            SafetyAssert(wrappedPackage.Title.ForLanguage("english") == "Paquet sans manifeste"
                && wrappedPackage.Files.Any(file => file.Relative == "Models/model.bin"),
                "la structure payload sans manifeste n'est pas reconnue.");

            string manifestMission = CreatePackage(structuredLibrary, "test.manifest-priority",
                "ManifestName", "Titre du manifeste", "free-exploration", "french");
            SafetyWrite(Path.Combine(manifestMission, "tree.klz"), "tree");
            SafetyWrite(Path.Combine(structuredLibrary, "test.manifest-priority", "tree.klz"),
                "ne doit pas changer le choix du manifeste");
            MissionPackage manifest = LoadLibrary(structuredLibrary, false).Packages
                .Single(item => item.Id == "test.manifest-priority");
            SafetyAssert(manifest.Category == "free-exploration"
                && manifest.Title.ForLanguage("french") == "Titre du manifeste"
                && manifest.MissionDirectory == "ManifestName" && manifest.Files.Count == 1,
                "un paquet avec manifeste a été reclassé en dossier brut.");

            string duplicateMission = CreatePackage(library, "test.directory-conflict",
                "Operation Test Joueur", "Collision", "user-mission", "english");
            SafetyWrite(Path.Combine(duplicateMission, "tree.klz"), "tree");
            SafetyLibraryRefused(library, "une collision de dossier brut/paquet a été acceptée.");

            string collisionLibrary = Path.Combine(root, "folder-resource-conflict");
            foreach (string name in new[] { "First", "Second" })
            {
                SafetyWrite(Path.Combine(collisionLibrary, name, "tree.klz"), "tree");
                SafetyWrite(Path.Combine(collisionLibrary, name, "Maps", "same.bin"), name);
            }
            SafetyLibraryRefused(collisionLibrary,
                "deux dossiers bruts peuvent écraser la même ressource.");

            string invalidLibrary = Path.Combine(root, "folder-missing-tree");
            SafetyWrite(Path.Combine(invalidLibrary, "Mission incomplete", "briefing.txt"), "briefing");
            SafetyLibraryRefused(invalidLibrary, "un dossier sans tree.klz a été ignoré.");

            string multipleLibrary = Path.Combine(root, "folder-multiple-trees");
            foreach (string name in new[] { "First", "Second" })
                SafetyWrite(Path.Combine(multipleLibrary, "Deux missions", "Missions", name,
                    "tree.klz"), "tree");
            SafetyLibraryRefused(multipleLibrary, "un dossier avec deux missions a été accepté.");

            string ambiguousLibrary = Path.Combine(root, "folder-ambiguous-tree");
            SafetyWrite(Path.Combine(ambiguousLibrary, "Ambiguous", "tree.klz"), "tree");
            SafetyWrite(Path.Combine(ambiguousLibrary, "Ambiguous", "Missions", "Other",
                "tree.klz"), "tree");
            SafetyLibraryRefused(ambiguousLibrary, "une structure directe/complète ambiguë a été acceptée.");

            string unsafeLibrary = Path.Combine(root, "folder-unsafe-payload");
            SafetyWrite(Path.Combine(unsafeLibrary, "Unsafe", "tree.klz"), "tree");
            SafetyWrite(Path.Combine(unsafeLibrary, "Unsafe", "Scripts", "evil.asi"), "MZ-test");
            SafetyLibraryRefused(unsafeLibrary,
                "un dossier brut peut installer un fichier exécutable .asi.");
        }

        private static byte[] SafetyCatalogue(params byte[][] missions)
        {
            return EncodeBlock(0x01, EncodeBlock(0x05, Join(missions.Select(
                mission => EncodeBlock(0x3C, Join(new[] {
                    EncodeInteger(0x3D, 999), EncodeBlock(0x05, mission) }))))));
        }

        private static void RunObjectiveTemplateSelfTests(string root)
        {
            string library = Path.Combine(root, "preserve-objectives");
            string missionPath = CreatePackage(library, "test.preserve-objectives",
                "LabMission", "Laboratoire", "user-mission", "english");
            SafetyWrite(Path.Combine(missionPath, "tree.klz"), "invented-tree");
            string manifestPath = Path.Combine(library, "test.preserve-objectives", "mission.json");
            Dictionary<string, object> document = AsObject(
                Json.DeserializeObject(File.ReadAllText(manifestPath)), "test manifest");
            document.Remove("objectives");
            document["templateMission"] = "SourceMission";
            document["preserveTemplateObjectives"] = true;
            SafetyWrite(manifestPath, Json.Serialize(document));
            MissionPackage package = LoadLibrary(library, false).Packages.Single();
            SafetyAssert(package.PreserveTemplateObjectives && package.ObjectiveIds.Count == 0,
                "le manifeste n'a pas conservé les objectifs du gabarit.");
            byte[] first = EncodeBlock(0x28, Join(new[] {
                EncodeInteger(0x29, 111), EncodeInteger(0x2A, 7) }));
            byte[] second = EncodeBlock(0x28, Join(new[] {
                EncodeInteger(0x29, 222), EncodeInteger(0x2A, 9) }));
            byte[] source = EncodeBlock(0x32, Join(new[] {
                EncodeInteger(0x33, 333), EncodeBlock(0x36,
                    Encoding.ASCII.GetBytes("SourceMission\0")), first, second }));
            List<GdtBlock> parsed;
            SafetyAssert(TryParseBlocks(source, 0, source.Length, out parsed),
                "le gabarit synthétique est invalide.");
            byte[] rebuilt = RewriteMission(parsed.Single(), package);
            List<GdtBlock> result;
            SafetyAssert(TryParseBlocks(rebuilt, 0, rebuilt.Length, out result),
                "la mission reconstruite est invalide.");
            List<byte[]> objectives = result.Single().Children.Where(
                block => block.Kind == 0x28).Select(EncodeExisting).ToList();
            SafetyAssert(objectives.Count == 2 && objectives[0].SequenceEqual(first)
                && objectives[1].SequenceEqual(second),
                "les objectifs hérités ont perdu un texte, un drapeau ou leur ordre.");
            byte[] originalCatalogue = SafetyCatalogue(source);
            byte[][] expansionMissions = Enumerable.Range(0, 3).Select(index =>
                EncodeBlock(0x32, Join(new[] { EncodeInteger(0x33, 444),
                    EncodeBlock(0x36, Encoding.ASCII.GetBytes("Expansion" + index + "\0")),
                    first }))).ToArray();
            byte[] expansionCatalogue = SafetyCatalogue(expansionMissions);
            byte[] custom = BuildCustomCatalogue(expansionCatalogue,
                new List<MissionPackage> { package }, originalCatalogue);
            List<GdtBlock> customBlocks;
            SafetyAssert(TryParseBlocks(custom, 0, custom.Length, out customBlocks),
                "le catalogue avec gabarit Base est invalide.");
            GdtBlock cloned = Walk(customBlocks).Single(block => block.Kind == 0x32);
            List<byte[]> inherited = cloned.Children.Where(block => block.Kind == 0x28)
                .Select(EncodeExisting).ToList();
            SafetyAssert(BlockString(Direct(cloned, 0x36)) == "LabMission"
                && inherited.Count == 2 && inherited[1].SequenceEqual(second),
                "la mission Base n'a pas été copiée dans le catalogue personnalisé.");
            bool ambiguous = false;
            try { MissionTemplates(originalCatalogue, originalCatalogue); }
            catch (InvalidDataException) { ambiguous = true; }
            SafetyAssert(ambiguous, "un gabarit Base/Sabre ambigu a été accepté.");
            document["objectives"] = new object[0];
            SafetyWrite(manifestPath, Json.Serialize(document));
            SafetyLibraryRefused(library, "conservation et objectifs explicites acceptés ensemble.");
            document.Remove("objectives");
            document.Remove("templateMission");
            SafetyWrite(manifestPath, Json.Serialize(document));
            SafetyLibraryRefused(library, "conservation sans gabarit acceptée.");
            document["templateMission"] = "SourceMission";
            document["preserveTemplateObjectives"] = "true";
            SafetyWrite(manifestPath, Json.Serialize(document));
            SafetyLibraryRefused(library, "conservation non booléenne acceptée.");
        }

        public static string RunSafetySelfTests(string parentRoot)
        {
            parentRoot = Path.GetFullPath(parentRoot);
            Directory.CreateDirectory(parentRoot);
            string guardedParent = parentRoot.TrimEnd(Path.DirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            string root = Path.Combine(
                guardedParent, "hd2-manager-safety-" + Guid.NewGuid().ToString("N"));
            root = Path.GetFullPath(root);
            if (!root.StartsWith(guardedParent, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Dossier d'auto-test hors de la zone autorisée.");
            try
            {
                Directory.CreateDirectory(root);
                RunMissionFolderSelfTests(root);
                RunObjectiveTemplateSelfTests(root);

                string conflictGame = Path.Combine(root, "conflict");
                string conflictRelative = "Maps/conflict.bin";
                string conflictTarget = SafeGameTarget(conflictGame, conflictRelative);
                Directory.CreateDirectory(Path.GetDirectoryName(conflictTarget));
                byte[] installed = Encoding.UTF8.GetBytes("installed");
                byte[] authorChange = Encoding.UTF8.GetBytes("author-change");
                File.WriteAllBytes(conflictTarget, installed);
                ManagedFile conflict = new ManagedFile {
                    Relative = conflictRelative, Created = true, Sha256 = Sha256(installed),
                    PackageId = "test.conflict"
                };
                File.WriteAllBytes(conflictTarget, authorChange);
                bool conflictRefused = false;
                try { EnsureManagedOverwriteSafe(conflictGame, conflict); }
                catch (InvalidDataException) { conflictRefused = true; }
                SafetyAssert(conflictRefused, "la réintégration a accepté un fichier modifié.");
                SafetyAssert(File.ReadAllBytes(conflictTarget).SequenceEqual(authorChange),
                    "le fichier modifié a changé pendant le refus.");

                string missingBackupGame = Path.Combine(root, "missing-backup");
                string missingBackupRelative = "Models/missing-backup.bin";
                string missingBackupTarget = SafeGameTarget(
                    missingBackupGame, missingBackupRelative);
                Directory.CreateDirectory(Path.GetDirectoryName(missingBackupTarget));
                File.WriteAllBytes(missingBackupTarget, installed);
                ManagedFile missingBackup = new ManagedFile {
                    Relative = missingBackupRelative, Created = false,
                    Sha256 = Sha256(installed), PackageId = "test.missing-backup"
                };
                bool missingBackupRefused = false;
                try { EnsureManagedOverwriteSafe(missingBackupGame, missingBackup); }
                catch (FileNotFoundException) { missingBackupRefused = true; }
                SafetyAssert(missingBackupRefused,
                    "la réintégration a recréé une sauvegarde originale absente.");

                string changedBackupGame = Path.Combine(root, "changed-backup");
                string changedBackupRelative = "Models/changed-backup.bin";
                string changedBackupTarget = SafeGameTarget(
                    changedBackupGame, changedBackupRelative);
                Directory.CreateDirectory(Path.GetDirectoryName(changedBackupTarget));
                File.WriteAllBytes(changedBackupTarget, installed);
                byte[] expectedOriginal = Encoding.UTF8.GetBytes("expected-original");
                string changedBackupPath = Path.Combine(
                    changedBackupGame, "STATIC_MENU_BACKUP", "Models",
                    "changed-backup.bin");
                Directory.CreateDirectory(Path.GetDirectoryName(changedBackupPath));
                File.WriteAllBytes(changedBackupPath, authorChange);
                ManagedFile changedBackup = new ManagedFile {
                    Relative = changedBackupRelative, Created = false,
                    Sha256 = Sha256(installed), BackupSha256 = Sha256(expectedOriginal),
                    PackageId = "test.changed-backup"
                };
                bool changedBackupRefused = false;
                try { EnsureManagedOverwriteSafe(changedBackupGame, changedBackup); }
                catch (InvalidDataException) { changedBackupRefused = true; }
                SafetyAssert(changedBackupRefused,
                    "la réintégration a accepté une sauvegarde originale modifiée.");

                string unsafeLibrary = Path.Combine(root, "unsafe-library");
                string unsafeMission = CreatePackage(
                    unsafeLibrary, "test.unsafe-payload", "UnsafePayload",
                    "Unsafe payload", "user-mission", "english");
                File.WriteAllBytes(Path.Combine(unsafeMission, "tree.klz"),
                    Encoding.ASCII.GetBytes("test-tree"));
                string unsafeScript = Path.Combine(
                    unsafeLibrary, "test.unsafe-payload", "payload", "Scripts",
                    "evil.asi");
                Directory.CreateDirectory(Path.GetDirectoryName(unsafeScript));
                File.WriteAllBytes(unsafeScript, Encoding.ASCII.GetBytes("MZ-test"));
                bool executablePayloadRefused = false;
                try { LoadLibrary(unsafeLibrary, false); }
                catch (InvalidDataException) { executablePayloadRefused = true; }
                SafetyAssert(executablePayloadRefused,
                    "un paquet a pu installer un fichier exécutable .asi.");

                ValidateMenuRowLimit(33, 219);
                bool rowOverflowRefused = false;
                try { ValidateMenuRowLimit(33, 220); }
                catch (InvalidDataException) { rowOverflowRefused = true; }
                SafetyAssert(rowOverflowRefused,
                    "la limite du moteur a accepté plus de 255 lignes de menu.");

                string restoreGame = Path.Combine(root, "restore-modified");
                string restoreRelative = "Models/replaced.bin";
                string restoreTarget = SafeGameTarget(restoreGame, restoreRelative);
                Directory.CreateDirectory(Path.GetDirectoryName(restoreTarget));
                File.WriteAllBytes(restoreTarget, authorChange);
                string restoreBackup = Path.Combine(
                    restoreGame, "STATIC_MENU_BACKUP", "Models", "replaced.bin");
                Directory.CreateDirectory(Path.GetDirectoryName(restoreBackup));
                File.WriteAllBytes(restoreBackup, Encoding.UTF8.GetBytes("original"));
                Dictionary<string, ManagedFile> restoreManaged =
                    new Dictionary<string, ManagedFile>(StringComparer.OrdinalIgnoreCase);
                restoreManaged[restoreRelative] = new ManagedFile {
                    Relative = restoreRelative, Created = false, Sha256 = Sha256(installed),
                    PackageId = "test.restore"
                };
                int restored = 0;
                int preserved = 0;
                FileTransaction restoreTransaction =
                    new FileTransaction(Path.Combine(root, "staging-restore"));
                PlanRestoreManagedFiles(
                    restoreGame, restoreManaged, restoreTransaction, ref restored, ref preserved);
                restoreTransaction.Commit();
                SafetyAssert(restored == 0 && preserved == 1 && restoreManaged.Count == 1,
                    "la restauration n'a pas conservé le suivi du fichier modifié.");
                SafetyAssert(File.ReadAllBytes(restoreTarget).SequenceEqual(authorChange),
                    "la restauration a écrasé un fichier remplacé puis modifié.");

                string removedGame = Path.Combine(root, "removed");
                Dictionary<string, ManagedFile> removedManaged =
                    new Dictionary<string, ManagedFile>(StringComparer.OrdinalIgnoreCase);
                string createdRelative = "Maps/created.bin";
                string changedRelative = "Maps/changed.bin";
                string replacedRelative = "Models/replace-me.bin";
                foreach (string relative in new[] {
                    createdRelative, changedRelative, replacedRelative })
                {
                    string target = SafeGameTarget(removedGame, relative);
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    File.WriteAllBytes(target, installed);
                }
                File.WriteAllBytes(
                    SafeGameTarget(removedGame, changedRelative), authorChange);
                string removedBackup = Path.Combine(
                    removedGame, "STATIC_MENU_BACKUP", "Models", "replace-me.bin");
                Directory.CreateDirectory(Path.GetDirectoryName(removedBackup));
                byte[] original = Encoding.UTF8.GetBytes("original");
                File.WriteAllBytes(removedBackup, original);
                removedManaged[createdRelative] = new ManagedFile {
                    Relative = createdRelative, Created = true, Sha256 = Sha256(installed)
                };
                removedManaged[changedRelative] = new ManagedFile {
                    Relative = changedRelative, Created = true, Sha256 = Sha256(installed)
                };
                removedManaged[replacedRelative] = new ManagedFile {
                    Relative = replacedRelative, Created = false, Sha256 = Sha256(installed)
                };
                int cleaned = 0;
                preserved = 0;
                FileTransaction removedTransaction =
                    new FileTransaction(Path.Combine(root, "staging-removed"));
                PlanRemovedManagedFiles(
                    removedGame, new HashSet<string>(StringComparer.OrdinalIgnoreCase),
                    removedManaged, removedTransaction, ref cleaned, ref preserved);
                removedTransaction.Commit();
                SafetyAssert(cleaned == 2 && preserved == 1 && removedManaged.Count == 1
                    && removedManaged.ContainsKey(changedRelative),
                    "le nettoyage d'un paquet retiré a un résultat incohérent.");
                SafetyAssert(!File.Exists(SafeGameTarget(removedGame, createdRelative)),
                    "un fichier créé par un paquet retiré est resté présent.");
                SafetyAssert(File.ReadAllBytes(
                    SafeGameTarget(removedGame, changedRelative)).SequenceEqual(authorChange),
                    "un fichier modifié d'un paquet retiré a été supprimé.");
                SafetyAssert(File.ReadAllBytes(
                    SafeGameTarget(removedGame, replacedRelative)).SequenceEqual(original),
                    "un ancien fichier remplacé n'a pas été restauré depuis sa sauvegarde.");

                for (int failure = 0; failure < 6; failure++)
                {
                    string rollbackRoot = Path.Combine(root, "rollback-" + failure);
                    Directory.CreateDirectory(rollbackRoot);
                    List<string> paths = new List<string>();
                    List<byte[]> before = new List<byte[]>();
                    List<bool> existed = new List<bool>();
                    FileTransaction rollbackTransaction =
                        new FileTransaction(Path.Combine(root, "staging-rollback"));
                    for (int index = 0; index < 6; index++)
                    {
                        string path = Path.Combine(rollbackRoot, "step-" + index + ".bin");
                        paths.Add(path);
                        bool hadFile = index % 2 == 0;
                        existed.Add(hadFile);
                        byte[] prior = Encoding.UTF8.GetBytes("before-" + index);
                        before.Add(prior);
                        if (hadFile) File.WriteAllBytes(path, prior);
                        rollbackTransaction.AddWrite(
                            path, Encoding.UTF8.GetBytes("after-" + index));
                    }
                    bool failed = false;
                    try { rollbackTransaction.Commit(failure); }
                    catch (IOException) { failed = true; }
                    SafetyAssert(failed, "la panne simulée " + failure + " n'a pas été déclenchée.");
                    for (int index = 0; index < paths.Count; index++)
                    {
                        SafetyAssert(File.Exists(paths[index]) == existed[index],
                            "la panne " + failure + " a laissé un fichier partiel.");
                        if (existed[index])
                            SafetyAssert(File.ReadAllBytes(paths[index]).SequenceEqual(before[index]),
                                "la panne " + failure + " n'a pas restauré un fichier initial.");
                    }
                }
                return "Auto-tests de sécurité réussis : 8/8, conservation des objectifs Base/Sabre et scan des dossiers bruts "
                    + "(fichiers directs, ressources, espaces, stabilité, sources intactes, "
                    + "Missions, payload, priorité du manifeste, collisions, dossiers invalides). "
                    + "Sécurité : conflit, sauvegarde absente, "
                    + "sauvegarde modifiée, charge utile exécutable, restauration, retrait, "
                    + "limite de lignes, annulation transactionnelle.";
            }
            finally
            {
                if (Directory.Exists(root))
                {
                    string checkedRoot = Path.GetFullPath(root);
                    if (!checkedRoot.StartsWith(guardedParent, StringComparison.OrdinalIgnoreCase)
                        || Path.GetFileName(checkedRoot).IndexOf(
                            "hd2-manager-safety-", StringComparison.OrdinalIgnoreCase) != 0)
                        throw new InvalidOperationException(
                            "Nettoyage d'auto-test refusé : chemin inattendu.");
                    Directory.Delete(checkedRoot, true);
                }
            }
        }

        private static void ValidateNoGameProcess()
        {
            System.Diagnostics.Process[] first =
                System.Diagnostics.Process.GetProcessesByName("HD2_SabreSquadron");
            System.Diagnostics.Process[] second =
                System.Diagnostics.Process.GetProcessesByName("HD2");
            bool running = first.Length > 0 || second.Length > 0;
            foreach (System.Diagnostics.Process process in first) process.Dispose();
            foreach (System.Diagnostics.Process process in second) process.Dispose();
            if (running) throw new InvalidOperationException("Fermez le jeu avant de continuer.");
        }
    }
}
