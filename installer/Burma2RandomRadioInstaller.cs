using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Burma2RandomRadioInstaller
    {
        private const string RegistryPath =
            "Missions/Burma2_obj/mpscripts.dta";
        private const string ScenePath =
            "Missions/Burma2_obj/scene2.bin";
        private const string ScriptPath =
            "Scripts/Burma2_obj/Burma2_mp_mrtvoly.scr";
        private const string Actor = "dummy_mrtvoly";
        private const string Script = "Burma2_mp_mrtvoly.scr";

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
            byte[] patched = AddBinding(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "Le choix aleatoire de la radio Burma 2 semble deja relie.");
            ValidateBinding(patched);
            if (!BytesEqual(patched, AddBinding(patched)))
                throw new InvalidDataException(
                    "La liaison radio Burma 2 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Burma 2 Objectif verifie : le controleur, les deux cadavres, "
                + "la radio et son emplacement alternatif officiel sont complets.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(
                    gamePath, RegistryPath);
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
                "Restauration du placement aleatoire de la radio dans Burma 2 Objectif...");
            ValidateAssets(gamePath);
            DormantSource source = ResolveSource(
                gamePath, RegistryPath, MissionArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, RegistryPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = AddBinding(original);
            ValidateBinding(patched);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Le placement aleatoire de la radio Burma 2 est deja relie.");
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
                "Burma 2 Objectif : controleur aleatoire de la radio relie.");
            InstallerCore.Report(progress,
                "La radio peut de nouveau apparaitre sur l'un des deux cadavres.");
        }

        private static byte[] AddBinding(byte[] data)
        {
            List<KeyValuePair<string, string>> bindings = ReadBindings(data);
            foreach (KeyValuePair<string, string> binding in bindings)
            {
                if (!String.Equals(binding.Key, Actor,
                        StringComparison.OrdinalIgnoreCase))
                    continue;
                if (String.Equals(binding.Value, Script,
                        StringComparison.OrdinalIgnoreCase))
                    return data;
                throw new InvalidDataException(
                    "Le controleur radio Burma 2 possede deja le script "
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

        private static void ValidateBinding(byte[] data)
        {
            int found = 0;
            foreach (KeyValuePair<string, string> binding in ReadBindings(data))
                if (String.Equals(binding.Key, Actor,
                        StringComparison.OrdinalIgnoreCase)
                    && String.Equals(binding.Value, Script,
                        StringComparison.OrdinalIgnoreCase))
                    found++;
            if (found != 1)
                throw new InvalidDataException(
                    "La liaison radio Burma 2 n'est pas unique.");
        }

        private static List<KeyValuePair<string, string>> ReadBindings(byte[] data)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre Burma 2 Objectif trop court.");
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
                    "Champ invalide du registre Burma 2 Objectif.");
            uint length = BitConverter.ToUInt32(data, offset + 2);
            if (length < 7 || length > Int32.MaxValue
                || offset > data.Length - (int)length
                || data[offset + (int)length - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide du registre Burma 2 Objectif.");
            string value = encoding.GetString(
                data, offset + 6, (int)length - 7);
            offset += (int)length;
            return value;
        }

        private static void WriteField(BinaryWriter writer, byte[] value)
        {
            writer.Write((ushort)1);
            writer.Write(checked(value.Length + 7));
            writer.Write(value);
            writer.Write((byte)0);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            foreach (string name in new[] {
                Actor, "l_mrtvol_01", "l_mrtvol_02", "dummy_vysilacka"
            })
                if (CountAscii(scene, name) != 1)
                    throw new InvalidDataException(
                        "Objet Burma 2 absent ou ambigu : " + name + ".");

            string script = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(
                    gamePath, ScriptPath, ScriptArchives)));
            Require(script,
                @"FRAME\s+mrtvola01\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*mrtvola01\s*,\s*""l_mrtvol_01""\s*\)",
                "Premier cadavre Burma 2 absent du controleur.");
            Require(script,
                @"FRAME\s+mrtvola02\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*mrtvola02\s*,\s*""l_mrtvol_02""\s*\)",
                "Second cadavre Burma 2 absent du controleur.");
            Require(script,
                @"FRAME\s+radio\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*radio\s*,\s*""d_radio""\s*\)",
                "Radio Burma 2 absente du controleur.");
            Require(script,
                @"FRAME\s+damac\s*;\s*FRM_FindFrame\s*"
                + @"\(\s*damac\s*,\s*""dummy_vysilacka""\s*\)",
                "Emplacement alternatif Burma 2 absent du controleur.");
            Require(script,
                @"INTEGER\s+rnd\s*=\s*_RandomInt\s*\(\s*2\s*\)"
                + @"[\s\S]{0,220}if\s*\(\s*rnd\s*==\s*1\s*\)"
                + @"\s*\{[\s\S]{0,120}ITEM_Teleport\s*"
                + @"\(\s*radio\s*,\s*damac\s*\)",
                "Choix aleatoire complet de la radio Burma 2 absent.");
        }

        private static int CountAscii(byte[] data, string value)
        {
            byte[] needle = Encoding.ASCII.GetBytes(value);
            int count = 0;
            for (int start = 0; start <= data.Length - needle.Length; start++)
            {
                int index = 0;
                while (index < needle.Length
                    && ToLowerAscii(data[start + index])
                        == ToLowerAscii(needle[index]))
                    index++;
                if (index == needle.Length) count++;
            }
            return count;
        }

        private static byte ToLowerAscii(byte value)
        {
            return value >= (byte)'A' && value <= (byte)'Z'
                ? (byte)(value + 32) : value;
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                    RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
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
