using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class NorwayTirpitzAmbienceInstaller
    {
        private const string RegistryPath = "Missions/Norway/Scripts.dta";
        private const string Owner = "m_tirpitz low.t_kotva41";
        private const string SenderScript = "R_Nor_action_Sender.scr";

        private static readonly int[] SenderGuards = {
            3, 4, 5, 8, 9, 11, 14, 15, 18
        };

        private static readonly int[] AnimatedGuards = {
            4, 5, 8, 9, 11, 14, 15, 18
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            byte[] patched = PatchRegistry(original);
            ValidateBinding(patched);
            if (!BytesEqual(patched, PatchRegistry(patched)))
                throw new InvalidDataException(
                    "La restauration de l'ambiance du Tirpitz n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Norway verifiee : le controleur commercial peut de nouveau "
                + "piloter les animations aleatoires de huit gardes du Tirpitz.";
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
                "Reactivation des animations aleatoires des gardes du Tirpitz...");
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
                    "Animations aleatoires du Tirpitz deja actives.");
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

            InstallerCore.Log(
                "Norway : controleur d'ambiance commercial du Tirpitz reactive.");
            InstallerCore.Report(progress,
                "Huit gardes presents du Tirpitz retrouvent leurs animations aleatoires.");
        }

        private static byte[] PatchRegistry(byte[] data)
        {
            List<KeyValuePair<string, string>> bindings = ReadBindings(data);
            foreach (KeyValuePair<string, string> binding in bindings)
            {
                if (!String.Equals(
                    binding.Key, Owner, StringComparison.OrdinalIgnoreCase))
                    continue;
                if (String.Equals(
                    binding.Value, SenderScript,
                    StringComparison.OrdinalIgnoreCase))
                    return data;
                throw new InvalidDataException(
                    "Le support d'ambiance du Tirpitz possede deja un autre script : "
                    + binding.Value + ".");
            }

            Encoding ansi = Encoding.GetEncoding(1252);
            byte[] actor = ansi.GetBytes(Owner);
            byte[] script = ansi.GetBytes(SenderScript);
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
                    "Registre de scripts Norway trop court.");
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
                    "Champ invalide dans le registre Norway.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Norway.");
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
                    binding.Key, Owner, StringComparison.OrdinalIgnoreCase)
                    && String.Equals(
                    binding.Value, SenderScript,
                    StringComparison.OrdinalIgnoreCase))
                    found++;
            if (found != 1)
                throw new InvalidDataException(
                    "Le controleur d'ambiance du Tirpitz n'est pas lie une seule fois.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            byte[] actors = ReadSource(ResolveSource(
                gamePath, "Missions/Norway/actors.bin", MissionArchives));
            byte[] tree = ReadSource(ResolveSource(
                gamePath, "Missions/Norway/tree.klz", MissionArchives));
            RequireBytes(tree, Owner,
                "Le support historique du controleur du Tirpitz est absent.");

            string sender = ReadText(ResolveSource(
                gamePath, "Scripts/Norway/" + SenderScript, ScriptArchives));
            Require(sender,
                @"what_signal\s*=\s*_RandomInt\s*\(\s*12\s*\)\s*\+\s*1",
                "Le tirage commercial des animations du Tirpitz est absent.");
            Require(sender,
                @"what_soldier\s*=\s*_RandomInt\s*\(\s*18\s*\)\s*\+\s*1",
                "Le tirage commercial des gardes du Tirpitz est absent.");

            foreach (int guard in SenderGuards)
            {
                string actor = "tirpic_guard_" + guard;
                string script = "R_Nor_Tirpic" + guard + ".scr";
                if (!HasBinding(registry, actor, script))
                    throw new InvalidDataException(
                        "Liaison commerciale absente pour " + actor + ".");
                RequireBytes(actors, actor,
                    "Acteur commercial absent : " + actor + ".");
                Require(sender,
                    @"(?m)^[ \t]*If\s*\(\s*what_soldier\s*==\s*"
                    + guard + @"\s*\)\s*\{\s*SendSignal\s*\(\s*T"
                    + guard + @"\s*,\s*what_signal\s*\)",
                    "Branche d'ambiance absente pour " + actor + ".");

            }

            foreach (int guard in AnimatedGuards)
            {
                string actor = "tirpic_guard_" + guard;
                string guardText = ReadText(ResolveSource(
                    gamePath, "Scripts/Norway/R_Nor_Tirpic"
                    + guard + ".scr", ScriptArchives));
                for (int signal = 1; signal <= 4; signal++)
                    Require(guardText,
                        @"OnSignal\s*\(\s*" + signal + @"\s*\)",
                        actor + " ne gere pas le signal d'ambiance "
                        + signal + ".");
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            foreach (KeyValuePair<string, string> binding in ReadBindings(data))
                if (String.Equals(
                    binding.Key, wantedActor, StringComparison.OrdinalIgnoreCase)
                    && String.Equals(
                    binding.Value, wantedScript,
                    StringComparison.OrdinalIgnoreCase))
                    return true;
            return false;
        }

        private static void RequireBytes(
            byte[] data, string marker, string message)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (text.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(message);
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static string ReadText(DormantSource source)
        {
            return Encoding.GetEncoding(1252).GetString(ReadSource(source));
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
