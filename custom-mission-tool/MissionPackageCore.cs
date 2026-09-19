using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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
        private static readonly HashSet<string> AllowedRoots =
            new HashSet<string>(new[] {
                "Maps", "Missions", "Models", "Scripts", "Sounds", "Tables", "Text"
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
            payload = Path.GetFullPath(payload).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            Stack<string> pending = new Stack<string>();
            pending.Push(payload.TrimEnd(Path.DirectorySeparatorChar));
            bool foundTree = false;
            while (pending.Count > 0)
            {
                string directory = pending.Pop();
                if ((File.GetAttributes(directory) & FileAttributes.ReparsePoint) != 0)
                    throw new InvalidDataException(package.Id + " : lien ou jonction interdit : " + directory);
                foreach (string child in Directory.GetDirectories(directory)) pending.Push(child);
                foreach (string file in Directory.GetFiles(directory))
                {
                    if ((File.GetAttributes(file) & FileAttributes.ReparsePoint) != 0)
                        throw new InvalidDataException(package.Id + " : lien interdit : " + file);
                    string full = Path.GetFullPath(file);
                    if (!full.StartsWith(payload, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException(package.Id + " : chemin hors du paquet.");
                    string relative = full.Substring(payload.Length).Replace('\\', '/');
                    string[] parts = relative.Split('/');
                    if (parts.Length == 0 || !AllowedRoots.Contains(parts[0])
                        || parts.Any(part => part == "." || part == ".." || part.IndexOf(':') >= 0))
                        throw new InvalidDataException(package.Id + " : chemin interdit : " + relative);
                    if (String.Equals(relative, "Models/singleplayer.4ds", StringComparison.OrdinalIgnoreCase)
                        || (String.Equals(parts[0], "Text", StringComparison.OrdinalIgnoreCase)
                            && String.Equals(parts[parts.Length - 1], "TEXTY_DD.txt", StringComparison.OrdinalIgnoreCase)))
                        throw new InvalidDataException(package.Id + " : fichier réservé : " + relative);
                    string expectedTree = "Missions/" + package.MissionDirectory + "/tree.klz";
                    if (String.Equals(relative, expectedTree, StringComparison.OrdinalIgnoreCase)) foundTree = true;
                    package.Files.Add(new PayloadFile { Source = full, Relative = relative });
                }
            }
            if (!foundTree)
                throw new InvalidDataException(package.Id + " : payload/Missions/"
                    + package.MissionDirectory + "/tree.klz absent.");
        }

        public static MissionLibrary LoadLibrary(string libraryRoot, bool assignIds)
        {
            MissionLibrary library = new MissionLibrary();
            library.Root = Path.GetFullPath(libraryRoot);
            if (!Directory.Exists(library.Root))
                throw new DirectoryNotFoundException("Bibliothèque introuvable : " + library.Root);
            foreach (string directory in Directory.GetDirectories(library.Root)
                .OrderBy(item => item, StringComparer.OrdinalIgnoreCase))
            {
                if (Path.GetFileName(directory).StartsWith("_", StringComparison.Ordinal)
                    || !File.Exists(Path.Combine(directory, "mission.json"))) continue;
                library.Packages.Add(ReadPackage(directory));
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
            bool objectives = false;
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
                    if (!objectives)
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

        public static byte[] ReadSourceCatalogue(string originalGame)
        {
            string archivePath = Path.Combine(Path.GetFullPath(originalGame), "SabreSquadron.dta");
            if (!File.Exists(archivePath)) throw new FileNotFoundException("SabreSquadron.dta introuvable.", archivePath);
            using (DtaArchive archive = new DtaArchive(archivePath))
            {
                DtaEntry entry = archive.Entries.FirstOrDefault(item =>
                    String.Equals(item.Name.Replace('/', '\\'), "GameData\\Gamedata01.gdt",
                        StringComparison.OrdinalIgnoreCase));
                if (entry == null) throw new InvalidDataException("Gamedata01.gdt absent de l'archive.");
                return archive.Read(entry);
            }
        }

        public static byte[] BuildCatalogue(byte[] source, MissionLibrary library)
        {
            List<GdtBlock> root;
            if (!TryParseBlocks(source, 0, source.Length, out root))
                throw new InvalidDataException("Catalogue Sabre Squadron illisible.");
            GdtBlock top = root.FirstOrDefault(block => block.Kind == 0x01);
            GdtBlock main = top == null ? null : Direct(top, 0x05);
            if (main == null) throw new InvalidDataException("Liste des campagnes absente.");
            List<GdtBlock> sourceCampaigns = main.Children.Where(block => block.Kind == 0x3C).ToList();
            if (sourceCampaigns.Count < 3) throw new InvalidDataException("Trois gabarits de campagne requis.");
            Dictionary<string, GdtBlock> templates =
                new Dictionary<string, GdtBlock>(StringComparer.OrdinalIgnoreCase);
            foreach (GdtBlock mission in Walk(main.Children).Where(block => block.Kind == 0x32))
            {
                GdtBlock directory = Direct(mission, 0x36);
                if (directory != null) templates[BlockString(directory)] = mission;
            }
            List<string> officialDirectories = Walk(main.Children)
                .Where(block => block.Kind == 0x32)
                .Select(block => Direct(block, 0x36)).Where(block => block != null)
                .Select(BlockString).ToList();
            HashSet<string> officialSet = new HashSet<string>(
                officialDirectories, StringComparer.OrdinalIgnoreCase);
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
                byte[] original = File.ReadAllBytes(path);
                string text = encoding.GetString(original);
                string separator = text.Contains("\r\n") ? "\r\n" : "\n";
                Dictionary<int, string> values = new Dictionary<int, string>();
                foreach (string category in CategoryOrder)
                    values[CategoryIds[category]] = CategoryName(category, language);
                foreach (MissionPackage package in library.Packages)
                {
                    values[package.TitleId] = "[" + CategoryName(package.Category, language)
                        + "] " + package.Title.ForLanguage(language);
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
            byte[] result = BuildCatalogue(ReadSourceCatalogue(originalGame), library);
            if (!String.IsNullOrWhiteSpace(outputPath)) WriteAtomic(outputPath, result);
            return Sha256(result);
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
                {
                    string backup = Path.Combine(game, "STATIC_MENU_BACKUP",
                        file.Relative.Replace('/', Path.DirectorySeparatorChar));
                    if (!File.Exists(backup))
                        throw new FileNotFoundException(
                            "Sauvegarde absente pour le fichier retiré : " + file.Relative, backup);
                    transaction.AddWrite(target, File.ReadAllBytes(backup));
                }
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
                {
                    string backup = Path.Combine(game, "STATIC_MENU_BACKUP",
                        file.Relative.Replace('/', Path.DirectorySeparatorChar));
                    if (!File.Exists(backup))
                        throw new FileNotFoundException(
                            "Sauvegarde absente pour le fichier à restaurer : " + file.Relative, backup);
                    transaction.AddWrite(target, File.ReadAllBytes(backup));
                }
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

        public static string Integrate(
            string libraryRoot, string originalGame, string testGame)
        {
            MissionLibrary library = LoadLibrary(libraryRoot, false);
            if (library.Packages.Count == 0)
                throw new InvalidDataException("Aucune mission dans la bibliothèque; aucun fichier n'a été modifié.");
            originalGame = Path.GetFullPath(originalGame);
            testGame = Path.GetFullPath(testGame);
            ValidatePreparedTestGame(originalGame, testGame);
            byte[] sourceCatalogue = ReadSourceCatalogue(originalGame);
            Dictionary<string, byte[]> catalogues = new Dictionary<string, byte[]> {
                { "Gamedata01.gdt", BuildCatalogue(sourceCatalogue, library) }
            };
            Dictionary<string, byte[]> textTables = BuildTextTables(testGame, library);
            Dictionary<string, ManagedFile> managed =
                CloneManagedState(ReadManagedState(testGame));
            HashSet<string> desired =
                new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            List<Tuple<MissionPackage, PayloadFile, string, byte[]>> payload =
                new List<Tuple<MissionPackage, PayloadFile, string, byte[]>>();
            foreach (MissionPackage package in library.Packages)
                foreach (PayloadFile file in package.Files)
                {
                    string target = SafeGameTarget(testGame, file.Relative);
                    byte[] data = File.ReadAllBytes(file.Source);
                    ManagedFile previous;
                    bool created;
                    if (managed.TryGetValue(file.Relative, out previous))
                    {
                        EnsureManagedOverwriteSafe(testGame, previous);
                        created = previous.Created;
                    }
                    else
                        created = !File.Exists(target);
                    managed[file.Relative] = new ManagedFile {
                        Relative = file.Relative, Created = created, Sha256 = Sha256(data),
                        PackageId = package.Id
                    };
                    desired.Add(file.Relative);
                    payload.Add(Tuple.Create(package, file, target, data));
                }

            FileTransaction transaction = new FileTransaction(null);
            int cleaned = 0;
            int preserved = 0;
            PlanRemovedManagedFiles(
                testGame, desired, managed, transaction, ref cleaned, ref preserved);
            foreach (string name in catalogues.Keys)
            {
                string catalogueTarget = Path.Combine(testGame, "GameData", name);
                string catalogueBackup = Path.Combine(
                    testGame, "STATIC_MENU_BACKUP", "GameData", name);
                if (!File.Exists(catalogueTarget) && !File.Exists(catalogueBackup))
                    transaction.AddWrite(catalogueBackup, sourceCatalogue);
                else
                    PlanBackupIfNeeded(transaction, testGame, catalogueTarget);
            }
            foreach (string path in textTables.Keys)
                PlanBackupIfNeeded(transaction, testGame, path);
            foreach (Tuple<MissionPackage, PayloadFile, string, byte[]> item in payload)
                PlanBackupIfNeeded(transaction, testGame, item.Item3);

            foreach (KeyValuePair<string, byte[]> catalogue in catalogues)
                transaction.AddWrite(
                    Path.Combine(testGame, "GameData", catalogue.Key), catalogue.Value);
            foreach (KeyValuePair<string, byte[]> table in textTables)
                transaction.AddWrite(table.Key, table.Value);
            foreach (Tuple<MissionPackage, PayloadFile, string, byte[]> item in payload)
                transaction.AddWrite(item.Item3, item.Item4);
            transaction.AddWrite(
                Path.Combine(testGame, "STATIC_MENU_MANAGED_FILES.json"),
                ManagedStateBytes(managed));
            if (library.RegistryChanged)
                transaction.AddWrite(
                    Path.Combine(library.Root, RegistryName), RegistryBytes(library));

            Dictionary<string, object> report = new Dictionary<string, object>();
            report["status"] = "CUSTOM_MISSIONS_INSTALLED_NATIVE_CATALOGUE_GAME_NOT_LAUNCHED";
            report["missions"] = library.Packages.Count;
            report["payload_files"] = library.FileCount;
            Dictionary<string, string> catalogueHashes = new Dictionary<string, string>();
            foreach (KeyValuePair<string, byte[]> catalogue in catalogues)
                catalogueHashes[catalogue.Key] = Sha256(catalogue.Value);
            report["catalogue_sha256"] = catalogueHashes;
            Dictionary<string, string> textHashes = new Dictionary<string, string>();
            string gameRoot = testGame.TrimEnd(Path.DirectorySeparatorChar)
                + Path.DirectorySeparatorChar;
            foreach (KeyValuePair<string, byte[]> table in textTables)
                textHashes[Path.GetFullPath(table.Key).Substring(gameRoot.Length).Replace('\\', '/')]
                    = Sha256(table.Value);
            report["text_table_sha256"] = textHashes;
            report["library"] = library.Root;
            transaction.AddWrite(
                Path.Combine(testGame, "CUSTOM_MISSIONS_INSTALL.json"),
                new UTF8Encoding(false).GetBytes(Json.Serialize(report)));
            transaction.Commit();
            library.RegistryChanged = false;
            return library.Packages.Count + " mission(s) intégrée(s), " + library.FileCount
                + " fichier(s) copiés, " + cleaned + " ancien(s) fichier(s) retiré(s), "
                + preserved + " fichier(s) modifié(s) conservé(s). Le jeu n'a pas été lancé.";
        }

        public static string Restore(string testGame)
        {
            testGame = Path.GetFullPath(testGame);
            ValidateNoGameProcess();
            Dictionary<string, ManagedFile> managed =
                CloneManagedState(ReadManagedState(testGame));
            int restored = 0;
            int preserved = 0;
            FileTransaction transaction = new FileTransaction(null);
            PlanRestoreManagedFiles(
                testGame, managed, transaction, ref restored, ref preserved);
            Dictionary<string, string> catalogueHashes =
                ReadInstallHashMap(testGame, "catalogue_sha256");
            string catalogueName = "Gamedata01.gdt";
            string catalogueExpected;
            catalogueHashes.TryGetValue(catalogueName, out catalogueExpected);
            PlanRestoreGeneratedFile(
                testGame, "GameData/" + catalogueName, catalogueExpected,
                transaction, ref restored, ref preserved);
            Dictionary<string, string> textHashes =
                ReadInstallHashMap(testGame, "text_table_sha256");
            foreach (KeyValuePair<string, string> table in textHashes)
                PlanRestoreGeneratedFile(
                    testGame, table.Key, table.Value,
                    transaction, ref restored, ref preserved);
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
                return "Auto-tests de sécurité réussis : 4/4 (conflit, restauration, retrait, annulation transactionnelle).";
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
