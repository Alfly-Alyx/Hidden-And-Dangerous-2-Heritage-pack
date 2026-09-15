using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa5SchumannAmbushInstaller
    {
        private const string ScriptPath = "Scripts/AFRICA5/AF4_23.scr";
        private const string RegistryPath = "Missions/AFRICA5/scripts.dta";
        private const string CheckpointsPath = "Missions/AFRICA5/check2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, ScriptPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "La mise en place de Schumann semble deja active.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration de l'embuscade Africa 5 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 5 verifie : Schumann rejoint de nouveau son point "
                + "de mise en scene pendant l'embuscade du tireur.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
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
                "Restauration de la mise en place de Schumann dans Africa 5...");
            DormantSource source = ResolveSource(
                gamePath, ScriptPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "La mise en place de Schumann dans Africa 5 est deja active.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, ScriptPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    ScriptPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Africa 5 : mise en place de Schumann pendant l'embuscade reactivee.");
            InstallerCore.Report(progress,
                "Schumann rejoint de nouveau sa position historique pendant l'embuscade.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (ActiveSequenceRegex().Matches(text).Count == 1)
            {
                ValidatePatched(data);
                return data;
            }

            Regex dormant = new Regex(
                @"(?ms)^(?<indent>[ \t]*)//[ \t]*OnCutscene\s*"
                + @"\(\s*20\s*\)\s*\{[ \t]*\r?\n"
                + @"(?:(?:\k<indent>//[^\r\n]*\r?\n)|(?:[ \t]*\r?\n))*?"
                + @"\k<indent>//[ \t]*\}[ \t]*\r?\n"
                + @"(?:[ \t]*\r?\n)*"
                + @"\k<indent>//[ \t]*OnCutsceneDone\s*"
                + @"\(\s*20\s*\)\s*\{[ \t]*\r?\n"
                + @"(?:(?:\k<indent>//[^\r\n]*\r?\n)|(?:[ \t]*\r?\n))*?"
                + @"\k<indent>//[ \t]*\}[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            Match match = dormant.Match(text);
            if (!match.Success || dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Bloc commente de l'embuscade de Schumann introuvable.");

            string uncommented = Regex.Replace(match.Value,
                @"(?m)^(?<indent>[ \t]*)//[ \t]?", "${indent}");
            text = text.Substring(0, match.Index) + uncommented
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(text);
        }

        private static Regex ActiveSequenceRegex()
        {
            return new Regex(
                @"^[ \t]*OnCutscene\s*\(\s*20\s*\)\s*\{[ \t]*(?=\r?$)"
                + @"[\s\S]{0,350}?^[ \t]*HUMAN_Stop\s*\(\s*\)\s*;"
                + @"[\s\S]{0,180}?^[ \t]*HUMAN_Move\s*"
                + @"\(\s*""AF4_blesz_end""\s*\)\s*;"
                + @"[\s\S]{0,180}?^[ \t]*HUMAN_SetMODE_Crouch\s*\(\s*\)\s*;"
                + @"[\s\S]{0,120}?^[ \t]*goto\s+END\s*;"
                + @"[\s\S]{0,80}?^[ \t]*\}[ \t]*(?=\r?$)"
                + @"[\s\S]{0,160}?^[ \t]*OnCutsceneDone\s*\(\s*20\s*\)"
                + @"\s*\{[ \t]*(?=\r?$)[\s\S]{0,100}?"
                + @"^[ \t]*EndScript\s*\(\s*\)\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveSequenceRegex().Matches(text).Count != 1)
                throw new InvalidDataException(
                    "La sequence restauree de Schumann est incomplete.");
            RequireCount(text,
                @"(?m)^[ \t]*//[ \t]*(?:OnCutscene|OnCutsceneDone)"
                + @"\s*\(\s*20\s*\)",
                0, "Un gestionnaire de l'embuscade de Schumann reste desactive.");
            RequireCount(text,
                @"(?m)^[ \t]*HUMAN_Move\s*"
                + @"\(\s*""AF4_blesz_end""\s*\)",
                1, "Le point final de Schumann est absent ou duplique.");
        }

        private static void RequireCount(
            string text, string pattern, int expected, string message)
        {
            if (Regex.Matches(text, pattern,
                    RegexOptions.IgnoreCase).Count != expected)
                throw new InvalidDataException(message);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF4_23", "AF4_23.scr"))
                throw new InvalidDataException(
                    "Schumann n'est plus relie a son script Africa 5.");
            if (!HasBinding(registry,
                    "dummy_attack_schumann", "AF4_schumann_detector.scr"))
                throw new InvalidDataException(
                    "Le detecteur d'embuscade de Schumann n'est plus relie.");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            if (CountAscii(checkpoints, "AF4_blesz_end") != 1)
                throw new InvalidDataException(
                    "Le point AF4_blesz_end est absent ou ambigu.");

            string detector = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/AFRICA5/AF4_schumann_detector.scr",
                    ScriptArchives)));
            RequireCount(detector,
                @"CSC_RunCutscene\s*\(\s*20\s*\)", 1,
                "L'embuscade de Schumann n'est plus declenchee.");

            string sniper = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/AFRICA5/AF4_31.scr", ScriptArchives)));
            RequireCount(sniper,
                @"OnCutscene\s*\(\s*20\s*\)", 1,
                "Le tireur d'Africa 5 ne participe plus a la cinematique 20.");
            RequireCount(sniper,
                @"OnCutsceneDone\s*\(\s*20\s*\)", 1,
                "La sortie de cinematique du tireur d'Africa 5 est absente.");
        }

        private static int CountAscii(byte[] data, string value)
        {
            byte[] needle = Encoding.ASCII.GetBytes(value);
            int count = 0;
            for (int start = 0; start <= data.Length - needle.Length; start++)
            {
                int index = 0;
                while (index < needle.Length
                    && ToLowerAscii(data[start + index]) == ToLowerAscii(needle[index]))
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

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 5 trop court.");
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
                    "Registre de scripts Africa 5 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 5.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Africa 5.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
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
