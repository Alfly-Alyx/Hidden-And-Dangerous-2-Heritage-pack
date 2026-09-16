using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class CoBrestGeneratorObjectiveInstaller
    {
        private const string Actor = "OBJ_gener";
        private const string Script = "obj_gener.scr";
        private const string MapListPath = "mpmaplist.txt";
        private static readonly string[] RegistryPaths = {
            "Missions/Co_brest/Scripts.dta",
            "Missions/Co_brest/MPScripts.dta"
        };
        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };
        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (string relative in RegistryPaths)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, MissionArchives));
                byte[] patched = AddBinding(original);
                ValidateBinding(patched);
                if (!BytesEqual(patched, AddBinding(patched)))
                    throw new InvalidDataException(
                        "La liaison des generateurs Brest coop n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            string list = File.ReadAllText(Path.Combine(gamePath, MapListPath),
                Encoding.GetEncoding(1252));
            string updated = AddObjective(list);
            if (!String.Equals(updated, AddObjective(updated),
                StringComparison.Ordinal))
                throw new InvalidDataException(
                    "L'ajout de l'objectif Brest cooperatif n'est pas idempotent.");
            return "Brest cooperatif verifie : objectif 15504, acteur, deux explosifs, "
                + "script identique au solo et deux registres disponibles.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string relative in RegistryPaths)
                {
                    string target = InstallerCore.SafeGameTarget(gamePath, relative);
                    if (!File.Exists(target)) return false;
                    ValidateBinding(File.ReadAllBytes(target));
                }
                string list = File.ReadAllText(
                    Path.Combine(gamePath, MapListPath), Encoding.GetEncoding(1252));
                return ContainsObjective(list);
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
                "Reactivation de l'objectif des generateurs dans Brest cooperatif...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (string relative in RegistryPaths)
            {
                DormantSource source = ResolveSource(
                    gamePath, relative, MissionArchives);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = AddBinding(original);
                ValidateBinding(patched);
                if (BytesEqual(original, patched)) continue;
                InstallerCore.PrepareTarget(
                    gamePath, relative, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                WriteBytes(target, relative, patched, journal);
                changed++;
            }

            string mapTarget = InstallerCore.SafeGameTarget(gamePath, MapListPath);
            string originalList = File.ReadAllText(
                mapTarget, Encoding.GetEncoding(1252));
            string updatedList = AddObjective(originalList);
            if (!String.Equals(originalList, updatedList, StringComparison.Ordinal))
            {
                InstallerCore.PrepareTarget(
                    gamePath, MapListPath, mapTarget, journal, prepared);
                WriteText(mapTarget, MapListPath, updatedList, journal);
                changed++;
            }
            InstallerCore.Log("Brest coop : objectif generateurs, "
                + changed + " fichiers mis a jour.");
            InstallerCore.Report(progress,
                "Brest cooperatif : objectif des deux generateurs reactive.");
        }

        internal static string AddObjective(string mapList)
        {
            Match map = FindMission(mapList);
            if (!map.Success)
                throw new InvalidDataException(
                    "Entree Brest cooperative introuvable ou ambigue dans mpmaplist.txt.");
            if (Regex.IsMatch(map.Value,
                @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*""15504""[^>]*\baxis_text\s*=\s*""15504""",
                RegexOptions.IgnoreCase))
                return mapList;
            foreach (string textId in new[] { "15500", "15506", "15503", "15501" })
                if (!Regex.IsMatch(map.Value,
                    @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*"""
                    + textId + @"""", RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Objectif Brest cooperatif de reference manquant : " + textId + ".");
            if (Regex.Matches(map.Value, @"<OBJECTIVE\b",
                RegexOptions.IgnoreCase).Count != 4)
                throw new InvalidDataException(
                    "Structure inattendue des objectifs Brest cooperatif.");

            Regex closing = new Regex(@"(?m)^([ \t]*)</MAP>\s*$",
                RegexOptions.IgnoreCase);
            Match close = closing.Match(map.Value);
            if (!close.Success || closing.Matches(map.Value).Count != 1)
                throw new InvalidDataException(
                    "Fin de l'entree Brest cooperative introuvable.");
            string newline = map.Value.Contains("\r\n") ? "\r\n" : "\n";
            string indentation = close.Groups[1].Value;
            string replacement = indentation
                + "<OBJECTIVE allied_text=\"15504\" axis_text=\"15504\" value=\"03\"/>"
                + newline + indentation + "</MAP>";
            string updated = closing.Replace(map.Value, replacement, 1);
            return mapList.Substring(0, map.Index) + updated
                + mapList.Substring(map.Index + map.Length);
        }

        private static bool ContainsObjective(string mapList)
        {
            Match map = FindMission(mapList);
            return map.Success && Regex.IsMatch(map.Value,
                @"<OBJECTIVE\b[^>]*\ballied_text\s*=\s*""15504""[^>]*\baxis_text\s*=\s*""15504""",
                RegexOptions.IgnoreCase);
        }

        private static Match FindMission(string mapList)
        {
            Regex pattern = new Regex(
                @"<MAP\b(?=[^>]*\bdir\s*=\s*""Co_brest"")[\s\S]*?</MAP>",
                RegexOptions.IgnoreCase);
            MatchCollection matches = pattern.Matches(mapList);
            return matches.Count == 1 ? matches[0] : Match.Empty;
        }

        private static byte[] AddBinding(byte[] data)
        {
            List<KeyValuePair<string, string>> bindings = ReadBindings(data);
            foreach (KeyValuePair<string, string> binding in bindings)
            {
                if (!String.Equals(binding.Key, Actor,
                    StringComparison.OrdinalIgnoreCase)) continue;
                if (String.Equals(binding.Value, Script,
                    StringComparison.OrdinalIgnoreCase)) return data;
                throw new InvalidDataException(
                    "L'acteur des generateurs Brest coop possede deja le script "
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
                        StringComparison.OrdinalIgnoreCase)) found++;
            if (found != 1)
                throw new InvalidDataException(
                    "La liaison des generateurs Brest coop n'est pas unique.");
        }

        private static List<KeyValuePair<string, string>> ReadBindings(byte[] data)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException("Registre Brest coop trop court.");
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
                throw new InvalidDataException("Champ invalide du registre Brest coop.");
            uint length = BitConverter.ToUInt32(data, offset + 2);
            if (length < 7 || length > Int32.MaxValue
                || offset > data.Length - (int)length
                || data[offset + (int)length - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide du registre Brest coop.");
            string value = encoding.GetString(data, offset + 6, (int)length - 7);
            offset += (int)length;
            return value;
        }

        private static void WriteField(BinaryWriter writer, byte[] value)
        {
            writer.Write((ushort)1);
            writer.Write(checked((uint)(value.Length + 7)));
            writer.Write(value);
            writer.Write((byte)0);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] solo = ReadSource(ResolveSource(
                gamePath, "Scripts/Brest/obj_gener.scr", ScriptArchives));
            byte[] coop = ReadSource(ResolveSource(
                gamePath, "Scripts/Co_brest/obj_gener.scr", ScriptArchives));
            if (!BytesEqual(solo, coop))
                throw new InvalidDataException(
                    "Le script des generateurs Brest coop differe de sa version solo active.");
            string script = Encoding.GetEncoding(1252).GetString(coop);
            foreach (string marker in new[] {
                "FRM_FindFrame(expl1, \"explgen\")",
                "FRM_FindFrame(expl2, \"explgen2\")",
                "SetObjectiveStatus(5, 1)" })
                if (script.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Element manquant dans l'objectif des generateurs Brest : "
                        + marker + ".");
            string scene = Encoding.GetEncoding(1252).GetString(ReadSource(ResolveSource(
                gamePath, "Missions/Co_brest/scene2.bin", MissionArchives)));
            if (scene.IndexOf("OBJ_gener", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Acteur OBJ_gener absent de la scene Brest coop.");
        }

        private static DormantSource ResolveSource(
            string gamePath, string relative, string[] archiveNames)
        {
            InstallerCore.ValidateGamePath(gamePath);
            DormantSource result = null;
            foreach (string archiveName in archiveNames)
            {
                string archivePath = Path.Combine(gamePath, archiveName);
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                        if (String.Equals(entry.Name.Replace((char)92, '/'), relative,
                            StringComparison.OrdinalIgnoreCase))
                            result = new DormantSource {
                                ArchivePath = archivePath, EntryIndex = entry.Index };
            }
            if (result == null)
                throw new InvalidDataException(
                    "Donnee officielle Brest introuvable : " + relative);
            return result;
        }

        private static byte[] ReadSource(DormantSource source)
        {
            using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                return archive.Read(archive.Entries[source.EntryIndex]);
        }

        private static void WriteBytes(
            string target, string relative, byte[] data, StateJournal journal)
        {
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
        }

        private static void WriteText(
            string target, string relative, string text, StateJournal journal)
        {
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllText(temporary, text, Encoding.GetEncoding(1252));
                File.Copy(temporary, target, true);
                journal.RecordHash(relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
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