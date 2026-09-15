using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa1DormantInteractionsInstaller
    {
        private const string RegistryPath = "Missions/AFRICA1/Scripts.dta";
        private const string GuardPath = "Scripts/AFRICA1/AF1_06.scr";
        private const string DoorActor = "HL_dvh_x01";
        private const string DoorScript = "1s_HL_dvh_x01.scr";

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly Regex DormantMachineGun = new Regex(
            @"(?m)^(?<i>[ \t]*)//[ \t]*HUMAN_BoardVehicle\s*\(\s*""w_mg42Crouch_2""\s*,\s*true\s*,\s*0\s*\)\s*;[ \t]*\r?$",
            RegexOptions.IgnoreCase);

        private static readonly Regex ActiveMachineGun = new Regex(
            @"(?m)^[ \t]*HUMAN_BoardVehicle\s*\(\s*""w_mg42Crouch_2""\s*,\s*true\s*,\s*0\s*\)\s*;[ \t]*\r?$",
            RegexOptions.IgnoreCase);

        public static string ValidateOnly(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            byte[] guard = ReadSource(ResolveSource(
                gamePath, GuardPath, ScriptArchives));
            byte[] patchedRegistry = PatchRegistry(registry);
            byte[] patchedGuard = PatchGuard(guard);
            if (BytesEqual(registry, patchedRegistry)
                || BytesEqual(guard, patchedGuard))
                throw new InvalidDataException(
                    "Une interaction dormante d'Africa 1 semble deja active.");
            ValidatePatched(patchedRegistry, patchedGuard);
            if (!BytesEqual(patchedRegistry, PatchRegistry(patchedRegistry))
                || !BytesEqual(patchedGuard, PatchGuard(patchedGuard)))
                throw new InvalidDataException(
                    "La restauration des interactions Africa 1 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 1 verifiee : la porte HL retrouve son changement "
                + "de lumiere et le garde 06 reprend sa MG42.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string registry = InstallerCore.SafeGameTarget(
                    gamePath, RegistryPath);
                string guard = InstallerCore.SafeGameTarget(gamePath, GuardPath);
                if (!File.Exists(registry) || !File.Exists(guard)) return false;
                ValidatePatched(
                    File.ReadAllBytes(registry), File.ReadAllBytes(guard));
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
                "Restauration de la porte lumineuse et de la MG42 d'Africa 1...");
            ValidateAssets(gamePath);
            bool changed = false;
            changed |= InstallOne(
                gamePath, RegistryPath, MissionArchives,
                PatchRegistry, journal, prepared);
            changed |= InstallOne(
                gamePath, GuardPath, ScriptArchives,
                PatchGuard, journal, prepared);
            if (!changed)
            {
                InstallerCore.Report(progress,
                    "Les deux interactions Africa 1 sont deja actives.");
                return;
            }
            InstallerCore.Log(
                "Africa 1 : porte HL lumineuse et poste MG42 du garde 06 restaures.");
            InstallerCore.Report(progress,
                "La porte HL et le garde 06 d'Africa 1 retrouvent leurs actions.");
        }

        private static bool InstallOne(
            string gamePath, string relative, string[] archives,
            Func<byte[], byte[]> patch, StateJournal journal,
            HashSet<string> prepared)
        {
            DormantSource source = ResolveSource(gamePath, relative, archives);
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = patch(original);
            if (BytesEqual(original, patched)) return false;

            InstallerCore.PrepareTarget(
                gamePath, relative, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            return true;
        }

        private static byte[] PatchRegistry(byte[] data)
        {
            List<KeyValuePair<string, string>> bindings = ReadBindings(data);
            foreach (KeyValuePair<string, string> binding in bindings)
            {
                if (!String.Equals(
                    binding.Key, DoorActor, StringComparison.OrdinalIgnoreCase))
                    continue;
                if (String.Equals(
                    binding.Value, DoorScript, StringComparison.OrdinalIgnoreCase))
                    return data;
                throw new InvalidDataException(
                    "La porte HL d'Africa 1 possede deja un autre script : "
                    + binding.Value + ".");
            }

            Encoding ansi = Encoding.GetEncoding(1252);
            using (MemoryStream result = new MemoryStream())
            using (BinaryWriter writer = new BinaryWriter(result, ansi))
            {
                writer.Write(data);
                WriteField(writer, ansi.GetBytes(DoorActor));
                WriteField(writer, ansi.GetBytes(DoorScript));
                return result.ToArray();
            }
        }

        private static byte[] PatchGuard(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            int dormant = DormantMachineGun.Matches(text).Count;
            int active = ActiveMachineGun.Matches(text).Count;
            if (dormant == 0 && active == 1) return data;
            if (dormant != 1 || active != 0)
                throw new InvalidDataException(
                    "Poste MG42 dormant du garde 06 d'Africa 1 introuvable.");
            return ansi.GetBytes(DormantMachineGun.Replace(
                text, "${i}HUMAN_BoardVehicle(\"w_mg42Crouch_2\", true, 0);", 1));
        }

        private static void ValidatePatched(byte[] registry, byte[] guard)
        {
            int found = 0;
            foreach (KeyValuePair<string, string> binding in ReadBindings(registry))
                if (String.Equals(
                    binding.Key, DoorActor, StringComparison.OrdinalIgnoreCase)
                    && String.Equals(
                    binding.Value, DoorScript, StringComparison.OrdinalIgnoreCase))
                    found++;
            if (found != 1)
                throw new InvalidDataException(
                    "Liaison de la porte HL d'Africa 1 absente ou ambigue.");

            string text = Encoding.GetEncoding(1252).GetString(guard);
            if (DormantMachineGun.Matches(text).Count != 0
                || ActiveMachineGun.Matches(text).Count != 1
                || !Regex.IsMatch(text,
                    @"HUMAN_MOVE\s*\(\s*""AF1_06_kulomet""\s*\)\s*;[\s\S]{0,100}HUMAN_BoardVehicle",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Prise de poste MG42 du garde 06 d'Africa 1 incomplete.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            foreach (KeyValuePair<string, string> binding in ReadBindings(registry))
                if (String.Equals(
                    binding.Key, DoorActor, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "La porte HL d'Africa 1 n'est plus libre dans le registre source.");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, "Missions/AFRICA1/scene2.bin", MissionArchives));
            byte[] actors = ReadSource(ResolveSource(
                gamePath, "Missions/AFRICA1/actors.bin", MissionArchives));
            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, "Missions/AFRICA1/check2.bin", MissionArchives));
            if (CountTypedString(scene, DoorActor) != 1)
                throw new InvalidDataException(
                    "Cadre de porte HL absent ou ambigu dans Africa 1.");
            if (CountTypedString(actors, "w_mg42Crouch_2") != 1)
                throw new InvalidDataException(
                    "MG42 du garde 06 absente ou ambigue dans Africa 1.");
            if (CountAscii(checkpoints, "AF1_06_kulomet") != 1)
                throw new InvalidDataException(
                    "Checkpoint du garde 06 absent ou ambigu dans Africa 1.");

            string door = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath,
                    "Scripts/AFRICA1/" + DoorScript, ScriptArchives)));
            if (!Regex.IsMatch(door,
                @"OnUse\s*\(\s*\)[\s\S]{0,300}FRM_SetLightMap\s*\(\s*HL_dvh_x01",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Controleur lumineux de la porte HL incomplet.");

            string guard = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, GuardPath, ScriptArchives)));
            if (!Regex.IsMatch(guard,
                @"OnAlarm\s*\(\s*\)[\s\S]{0,500}HUMAN_MOVE\s*\(\s*""AF1_06_kulomet""",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Branche d'alarme du garde 06 incomplete.");
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
                    "Registre de scripts Africa 1 trop court.");
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
                    "Champ invalide dans le registre Africa 1.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Africa 1.");
            string value = encoding.GetString(
                data, offset + 6, (int)rawLength - 7);
            offset += (int)rawLength;
            return value;
        }

        private static int CountTypedString(byte[] data, string wanted)
        {
            int count = 0;
            for (int offset = 0; offset + 6 <= data.Length; offset++)
            {
                if (data[offset] != 0x10 || data[offset + 1] != 0x00)
                    continue;
                uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
                if (rawTotal < 7 || rawTotal > 4096) continue;
                int total = (int)rawTotal;
                if (offset + total > data.Length
                    || data[offset + total - 1] != 0)
                    continue;
                string value = Encoding.GetEncoding(1252).GetString(
                    data, offset + 6, total - 7);
                if (String.Equals(value, wanted,
                        StringComparison.OrdinalIgnoreCase))
                    count++;
            }
            return count;
        }

        private static int CountAscii(byte[] data, string wanted)
        {
            byte[] needle = Encoding.ASCII.GetBytes(wanted);
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
                    "Donnee officielle Africa 1 introuvable : " + relative);
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
