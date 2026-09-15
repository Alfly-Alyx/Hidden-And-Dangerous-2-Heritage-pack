using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace HD2CommunityInstaller
{
    internal static class Alps1CivilAlarmInstaller
    {
        private const string RegistryPath = "Missions/ALPS1/Scripts.dta";
        private const string Actor = "ci03alarmer1";
        private const string Script = "ci03alarmer1.scr";

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            DormantSource source = ResolveSource(
                gamePath, RegistryPath, MissionArchives);
            byte[] original = ReadSource(source);
            byte[] patched = PatchRegistry(original);
            ValidateBinding(patched);
            if (!BytesEqual(patched, PatchRegistry(patched)))
                throw new InvalidDataException(
                    "La restauration du detecteur Alps 1 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Vestige Alps 1 verifie : ci03alarmer1 rejoint la seconde approche du civil 03.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, RegistryPath);
                if (!File.Exists(target)) return false;
                ValidateBinding(File.ReadAllBytes(target));
                return true;
            }
            catch
            {
                return false;
            }
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Reactivation du second detecteur du civil 03 dans Alps 1...");
            DormantSource source = ResolveSource(
                gamePath, RegistryPath, MissionArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, RegistryPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchRegistry(original);
            ValidateBinding(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Second detecteur du civil 03 d'Alps 1 deja active; aucune modification.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, RegistryPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    RegistryPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log("Alps 1 : detecteur ci03alarmer1 reactive.");
            InstallerCore.Report(progress,
                "Le second detecteur du civil 03 d'Alps 1 a ete reactive.");
        }

        private static byte[] PatchRegistry(byte[] data)
        {
            List<KeyValuePair<string, string>> bindings = ReadBindings(data);
            foreach (KeyValuePair<string, string> binding in bindings)
            {
                if (!String.Equals(
                    binding.Key, Actor, StringComparison.OrdinalIgnoreCase))
                    continue;
                if (String.Equals(
                    binding.Value, Script, StringComparison.OrdinalIgnoreCase))
                    return data;
                throw new InvalidDataException(
                    "Le second detecteur du civil 03 possede deja un autre script : "
                    + binding.Value + ".");
            }

            Encoding ansi = Encoding.GetEncoding(1252);
            byte[] actor = ansi.GetBytes(Actor);
            byte[] script = ansi.GetBytes(Script);
            using (MemoryStream result = new MemoryStream(
                checked(data.Length + actor.Length + script.Length + 14)))
            using (BinaryWriter writer = new BinaryWriter(result, ansi))
            {
                writer.Write(data);
                WriteField(writer, actor);
                WriteField(writer, script);
                return result.ToArray();
            }
        }

        private static void WriteField(BinaryWriter writer, byte[] value)
        {
            writer.Write((ushort)1);
            writer.Write(checked((uint)(value.Length + 7)));
            writer.Write(value);
            writer.Write((byte)0);
        }

        private static List<KeyValuePair<string, string>> ReadBindings(byte[] data)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Alps 1 trop court.");
            Encoding ansi = Encoding.GetEncoding(1252);
            List<KeyValuePair<string, string>> result =
                new List<KeyValuePair<string, string>>();
            int offset = 6;
            while (offset < data.Length)
            {
                string actor = ReadField(data, ref offset, ansi);
                string script = ReadField(data, ref offset, ansi);
                result.Add(new KeyValuePair<string, string>(actor, script));
            }
            return result;
        }

        private static string ReadField(
            byte[] data, ref int offset, Encoding encoding)
        {
            if (offset < 0 || offset > data.Length - 6
                || BitConverter.ToUInt16(data, offset) != 1)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Alps 1.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Alps 1.");
            string value = encoding.GetString(
                data, offset + 6, (int)rawLength - 7);
            offset += (int)rawLength;
            return value;
        }

        private static void ValidateBinding(byte[] data)
        {
            int found = 0;
            foreach (KeyValuePair<string, string> binding in ReadBindings(data))
                if (String.Equals(
                    binding.Key, Actor, StringComparison.OrdinalIgnoreCase)
                    && String.Equals(
                    binding.Value, Script, StringComparison.OrdinalIgnoreCase))
                    found++;
            if (found != 1)
                throw new InvalidDataException(
                    "La liaison du second detecteur du civil 03 dans Alps 1 n'est pas unique.");
        }

        private static void ValidateAssets(string gamePath)
        {
            ValidateAsset(gamePath,
                "Scripts/ALPS1/ci03alarmer1.scr", ScriptArchives,
                new[] {
                    "FRM_FindFrame (ci03,\"ci_03\")",
                    "_PlayerInRange(2)",
                    "SendSignal (ci03,8)"
                });
            ValidateAsset(gamePath,
                "Scripts/ALPS1/ci_03.scr", ScriptArchives,
                new[] {
                    "Whenever alarm2(_SignalReceived(8))",
                    "SendSignal (alarm,1)"
                });
            ValidateAsset(gamePath,
                "Missions/ALPS1/scene2.bin", MissionArchives,
                new[] { "ci03alarmer", "ci03alarmer1" });
            ValidateAsset(gamePath,
                "Missions/ALPS1/actors.bin", MissionArchives,
                new[] { "ci_03" });

            DormantSource registry = ResolveSource(
                gamePath, RegistryPath, MissionArchives);
            List<KeyValuePair<string, string>> bindings =
                ReadBindings(ReadSource(registry));
            ValidateExistingBinding(bindings, "ci03alarmer", "ci03alarmer.scr");
            ValidateExistingBinding(bindings, "CI_03", "ci_03.scr");
        }

        private static void ValidateExistingBinding(
            List<KeyValuePair<string, string>> bindings,
            string actor, string script)
        {
            int found = 0;
            foreach (KeyValuePair<string, string> binding in bindings)
                if (String.Equals(binding.Key, actor,
                    StringComparison.OrdinalIgnoreCase)
                    && String.Equals(binding.Value, script,
                    StringComparison.OrdinalIgnoreCase))
                    found++;
            if (found != 1)
                throw new InvalidDataException(
                    "Liaison Alps 1 attendue absente : "
                    + actor + " -> " + script + ".");
        }

        private static void ValidateAsset(
            string gamePath, string relative, string[] archives,
            string[] markers)
        {
            DormantSource source = ResolveSource(gamePath, relative, archives);
            string text = Encoding.GetEncoding(1252).GetString(ReadSource(source));
            foreach (string marker in markers)
                if (text.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Element Alps 1 manquant dans " + relative + " : "
                        + marker + ".");
        }

        private static DormantSource ResolveSource(
            string gamePath, string relative, string[] archiveNames)
        {
            InstallerCore.ValidateGamePath(gamePath);
            DormantSource result = null;
            foreach (string archiveName in archiveNames)
            {
                string archivePath = Path.Combine(gamePath, archiveName);
                if (!File.Exists(archivePath))
                    throw new FileNotFoundException(
                        "Archive officielle manquante.", archivePath);
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                        if (String.Equals(
                            entry.Name.Replace((char)92, '/'), relative,
                            StringComparison.OrdinalIgnoreCase))
                            result = new DormantSource {
                                ArchivePath = archivePath,
                                EntryIndex = entry.Index
                            };
            }
            if (result == null)
                throw new InvalidDataException(
                    "Donnee officielle introuvable : " + relative);
            return result;
        }

        private static byte[] ReadSource(DormantSource source)
        {
            using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                return archive.Read(archive.Entries[source.EntryIndex]);
        }

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}
