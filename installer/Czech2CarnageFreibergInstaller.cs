using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Czech2CarnageFreibergInstaller
    {
        private const string SelectorPath =
            "Scripts/CZECH2/setobjectives.scr";
        private const string CarnageScriptPath =
            "Scripts/CZECH2/carn_Big_Boss.scr";
        private const string RegistryPath = "Missions/CZECH2/Scripts.dta";
        private const string ScenePath = "Missions/CZECH2/scene2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, SelectorPath, ScriptArchives));
            byte[] patched = PatchSelector(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "La variante Carnage de Freiberg semble deja active dans Czech 2.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchSelector(patched)))
                throw new InvalidDataException(
                    "La restauration Carnage de Freiberg n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Czech 2 verifie : le selecteur Carnage peut reutiliser "
                + "le comportement hostile officiel de Freiberg.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(
                    gamePath, SelectorPath);
                if (!File.Exists(target)) return false;
                ValidatePatched(File.ReadAllBytes(target));
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
                "Restauration du comportement Carnage de Freiberg dans Czech 2...");
            DormantSource source = ResolveSource(
                gamePath, SelectorPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, SelectorPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchSelector(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Le comportement Carnage de Freiberg est deja actif.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, SelectorPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    SelectorPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Czech 2 : variante Carnage officielle de Freiberg reactivee.");
            InstallerCore.Report(progress,
                "En Carnage, Freiberg utilise de nouveau son comportement hostile historique.");
        }

        private static byte[] PatchSelector(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatched(text))
            {
                ValidatePatched(data);
                return data;
            }

            Regex assignment = new Regex(
                @"(?m)^(?<indent>[ \t]*)ScriptAssign\s*\(\s*obj\s*,\s*"
                + @"""objectives_carn(?:\.scr)?""\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (assignment.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Affectation du controleur Carnage Czech 2 introuvable.");
            string newline = text.IndexOf("\r\n", StringComparison.Ordinal) >= 0
                ? "\r\n" : "\n";
            text = assignment.Replace(text, match =>
                match.Value + newline + match.Groups["indent"].Value
                + "ScriptAssign(boss,\"carn_Big_Boss.scr\");", 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"if\s*\(\s*\(\s*mrd\s*==\s*3\s*\)\s*or\s*"
                + @"\(\s*mrd\s*==\s*7\s*\)\s*\)\s*\{[\s\S]{0,420}"
                + @"ScriptAssign\s*\(\s*obj\s*,\s*""objectives_carn(?:\.scr)?""\s*\)\s*;"
                + @"[\s\S]{0,220}ScriptAssign\s*\(\s*boss\s*,\s*"
                + @"""carn_big_boss\.scr""\s*\)\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsPatched(text))
                throw new InvalidDataException(
                    "Branche Carnage de Freiberg incomplete dans Czech 2.");
            if (Regex.Matches(text,
                    @"(?m)^[ \t]*ScriptAssign\s*\(\s*boss\s*,\s*"
                    + @"""carn_big_boss\.scr""\s*\)\s*;",
                    RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(
                    "Nombre inattendu d'affectations Carnage de Freiberg.");
            Require(text,
                @"Frame\s+boss\s*;[ \t]*FRM_FindFrame\s*"
                + @"\(\s*boss\s*,\s*""big_boss""\s*\)",
                "La declaration officielle de Freiberg a disparu du selecteur.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "setobjectives", "setobjectives.scr")
                || !HasBinding(registry, "big_boss", "R_Cz2_Big_Boss.scr"))
                throw new InvalidDataException(
                    "Liaisons commerciales de Freiberg ou du selecteur Czech 2 absentes.");

            string carnage = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, CarnageScriptPath, ScriptArchives)));
            Require(carnage, @"HUMAN_SETAIMODE_Aggressive\s*\(\s*\)",
                "Mode hostile absent du script Carnage de Freiberg.");
            Require(carnage, @"_PlayerInRange\s*\(\s*15\s*\)",
                "Declencheur de proximite absent du script Carnage de Freiberg.");
            Require(carnage, @"SetAlarmType\s*\(\s*1023\s*,\s*1\s*\)",
                "Activation d'alarme absente du script Carnage de Freiberg.");
            Require(carnage, @"HUMAN_WeaponOnArm\s*\(\s*1\s*\)",
                "Armement absent du script Carnage de Freiberg.");

            string scene = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, ScenePath, MissionArchives)));
            if (scene.IndexOf("big_boss",
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Acteur Freiberg absent de la scene Czech 2.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Czech 2 trop court.");
            int offset = 6;
            while (offset < data.Length)
            {
                string actor = ReadRegistryField(data, ref offset);
                string script = ReadRegistryField(data, ref offset);
                if (String.Equals(actor, wantedActor,
                        StringComparison.OrdinalIgnoreCase)
                    && String.Equals(script, wantedScript,
                        StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException(
                    "Registre de scripts Czech 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Czech 2.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
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