using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class CoLibye3DormantDetailsInstaller
    {
        private const string ObjectiveScript =
            "Scripts/Co_Libye3/Objective1.scr";
        private const string RoofScript =
            "Scripts/Co_Libye3/Village_Roof_7.scr";
        private const string RoofReferenceScript =
            "Scripts/Co_Libye3/Village_Roof_2.scr";

        private static readonly string[] RegistryPaths = {
            "Missions/Co_Libye3/MpScripts.dta",
            "Missions/Co_Libye3/Scripts.dta"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] FlagPatterns = {
            @"Frame[ \t]+ger_flag[ \t]*;[ \t]*FRM_FindFrame[ \t]*"
                + @"\([ \t]*ger_flag[ \t]*,[ \t]*""d_gerflag_""[ \t]*\)[ \t]*;",
            @"Frame[ \t]+gb_flag[ \t]*;[ \t]*FRM_FindFrame[ \t]*"
                + @"\([ \t]*gb_flag[ \t]*,[ \t]*""d_gbflag_""[ \t]*\)[ \t]*;",
            @"FRM_SetOn[ \t]*\([ \t]*ger_flag[ \t]*,[ \t]*false[ \t]*\)[ \t]*;",
            @"FRM_SetOn[ \t]*\([ \t]*gb_flag[ \t]*,[ \t]*true[ \t]*\)[ \t]*;",
            @"FRM_SetOn[ \t]*\([ \t]*ger_flag[ \t]*,[ \t]*true[ \t]*\)[ \t]*;",
            @"FRM_SetOn[ \t]*\([ \t]*gb_flag[ \t]*,[ \t]*false[ \t]*\)[ \t]*;"
        };

        private const string RoofBoardPattern =
            @"HUMAN_BoardVehicle[ \t]*\([ \t]*""Kulas2""[ \t]*,"
            + @"[ \t]*1[ \t]*,[ \t]*0[ \t]*\)[ \t]*;";

        private sealed class ScriptChange
        {
            public string Relative;
            public string Target;
            public byte[] Original;
            public byte[] Patched;
        }

        public static string ValidateOnly(string gamePath)
        {
            byte[] objectiveOriginal = ReadSource(ResolveSource(
                gamePath, ObjectiveScript, ScriptArchives));
            byte[] objectivePatched = PatchObjective(objectiveOriginal);
            if (BytesEqual(objectiveOriginal, objectivePatched))
                throw new InvalidDataException(
                    "Les drapeaux de Co_Libye3 semblent deja reactives dans l'archive.");
            ValidateObjective(objectivePatched);
            if (!BytesEqual(
                    objectivePatched, PatchObjective(objectivePatched)))
                throw new InvalidDataException(
                    "La restauration des drapeaux de Co_Libye3 n'est pas idempotente.");

            byte[] roofOriginal = ReadSource(ResolveSource(
                gamePath, RoofScript, ScriptArchives));
            byte[] roofPatched = PatchRoof(roofOriginal);
            if (BytesEqual(roofOriginal, roofPatched))
                throw new InvalidDataException(
                    "Le mitrailleur de toit Co_Libye3 semble deja reactive dans l'archive.");
            ValidateRoof(roofPatched);
            if (!BytesEqual(roofPatched, PatchRoof(roofPatched)))
                throw new InvalidDataException(
                    "La restauration du mitrailleur Co_Libye3 n'est pas idempotente.");

            ValidateAssets(gamePath);
            return "Co_Libye3 verifiee : l'echange des drapeaux du poste "
                + "et le mitrailleur de toit possedent leurs chaines officielles completes.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string objective = InstallerCore.SafeGameTarget(
                    gamePath, ObjectiveScript);
                string roof = InstallerCore.SafeGameTarget(
                    gamePath, RoofScript);
                if (!File.Exists(objective) || !File.Exists(roof))
                    return false;
                ValidateObjective(File.ReadAllBytes(objective));
                ValidateRoof(File.ReadAllBytes(roof));
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
                "Restauration des drapeaux et du mitrailleur de Co_Libye3...");
            ValidateAssets(gamePath);
            List<ScriptChange> changes = new List<ScriptChange>();
            changes.Add(BuildChange(
                gamePath, ObjectiveScript, PatchObjective, ValidateObjective));
            changes.Add(BuildChange(
                gamePath, RoofScript, PatchRoof, ValidateRoof));

            int written = 0;
            foreach (ScriptChange change in changes)
            {
                if (BytesEqual(change.Original, change.Patched)) continue;
                InstallerCore.PrepareTarget(
                    gamePath, change.Relative, change.Target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(change.Target));
                string temporary = change.Target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, change.Patched);
                    File.Copy(temporary, change.Target, true);
                    journal.RecordHash(
                        change.Relative, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                written++;
            }

            InstallerCore.Log("Co_Libye3 : " + written
                + " scripts de details historiques restaures.");
            InstallerCore.Report(progress,
                "Co_Libye3 retrouve l'echange des drapeaux et le mitrailleur de toit.");
        }

        private static ScriptChange BuildChange(
            string gamePath, string relative, Func<byte[], byte[]> patch,
            Action<byte[]> validate)
        {
            DormantSource source = ResolveSource(
                gamePath, relative, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = patch(original);
            validate(patched);
            return new ScriptChange {
                Relative = relative,
                Target = target,
                Original = original,
                Patched = patched
            };
        }

        private static byte[] PatchObjective(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            foreach (string pattern in FlagPatterns)
                text = UncommentUnique(
                    text, pattern, "instruction de drapeau Co_Libye3");
            return ansi.GetBytes(text);
        }

        private static byte[] PatchRoof(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = UncommentUnique(
                text, RoofBoardPattern, "embarquement Kulas2 Co_Libye3");
            return ansi.GetBytes(text);
        }

        private static string UncommentUnique(
            string text, string statementPattern, string description)
        {
            Regex active = ActiveLineRegex(statementPattern);
            Regex dormant = DormantLineRegex(statementPattern);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == 1 && dormantCount == 0) return text;
            if (activeCount != 0 || dormantCount != 1)
                throw new InvalidDataException(
                    "Etat absent ou ambigu : " + description + ".");
            return dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            }, 1);
        }

        private static Regex ActiveLineRegex(string statementPattern)
        {
            return new Regex(
                @"(?m)^[ \t]*" + statementPattern + @"[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static Regex DormantLineRegex(string statementPattern)
        {
            return new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>"
                + statementPattern + @")[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidateObjective(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            foreach (string pattern in FlagPatterns)
                if (ActiveLineRegex(pattern).Matches(text).Count != 1
                    || DormantLineRegex(pattern).Matches(text).Count != 0)
                    throw new InvalidDataException(
                        "Sequence de drapeaux Co_Libye3 incomplete.");
            Require(text,
                @"Whenever[ \t]+""Objective1""[\s\S]{0,300}"
                + @"SendSignal[ \t]*\([ \t]*objectives[ \t]*,[ \t]*25",
                "Le declencheur de capture du poste Co_Libye3 a ete altere.");
            Require(text,
                @"OnSignal[ \t]*\([ \t]*20[ \t]*\)[\s\S]{0,250}"
                + @"current_objective[ \t]*=[ \t]*1",
                "L'initialisation du poste Co_Libye3 a ete alteree.");
        }

        private static void ValidateRoof(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveLineRegex(RoofBoardPattern).Matches(text).Count != 1
                || DormantLineRegex(RoofBoardPattern).Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Embarquement Kulas2 Co_Libye3 incomplet.");
            Require(text,
                @"Label[ \t]+Action[ \t]*:[\s\S]{0,300}"
                + RoofBoardPattern,
                "L'embarquement Kulas2 n'est plus dans l'activite du garde.");
        }

        private static void ValidateAssets(string gamePath)
        {
            foreach (string registryPath in RegistryPaths)
            {
                byte[] registry = ReadSource(ResolveSource(
                    gamePath, registryPath, MissionArchives));
                if (!HasBinding(
                        registry, "D_ZONE2_FLAG", "Objective1.scr")
                    || !HasBinding(
                        registry, "VILLAGE_ROOF_7", "Village_Roof_7.scr"))
                    throw new InvalidDataException(
                        "Liaisons Co_Libye3 absentes dans " + registryPath + ".");
            }

            byte[] actors = ReadSource(ResolveSource(
                gamePath, "Missions/Co_Libye3/actors.bin",
                MissionArchives));
            foreach (string actor in new[] {
                "d_gerflag_", "d_gbflag_", "Kulas2", "Kulas3",
                "VILLAGE_ROOF_7", "VILLAGE_ROOF_2"
            })
                if (!ContainsNullTerminated(actors, actor))
                    throw new InvalidDataException(
                        "Acteur Co_Libye3 manquant : " + actor + ".");

            byte[] reference = ReadSource(ResolveSource(
                gamePath, RoofReferenceScript, ScriptArchives));
            string referenceText =
                Encoding.GetEncoding(1252).GetString(reference);
            string referencePattern =
                @"HUMAN_BoardVehicle[ \t]*\([ \t]*""Kulas3""[ \t]*,"
                + @"[ \t]*1[ \t]*,[ \t]*0[ \t]*\)[ \t]*;";
            if (ActiveLineRegex(referencePattern)
                    .Matches(referenceText).Count != 1)
                throw new InvalidDataException(
                    "Le mitrailleur de reference Kulas3 est absent.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Co_Libye3 trop court.");
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
            if (offset < 0 || offset > data.Length - 6
                || BitConverter.ToUInt16(data, offset) != 1)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Co_Libye3.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Co_Libye3.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, (int)rawLength - 7);
            offset += (int)rawLength;
            return value;
        }

        private static bool ContainsNullTerminated(byte[] data, string value)
        {
            byte[] needle = Encoding.GetEncoding(1252).GetBytes(value + "\0");
            for (int start = 0; start <= data.Length - needle.Length; start++)
            {
                int index = 0;
                while (index < needle.Length
                    && ToLowerAscii(data[start + index])
                        == ToLowerAscii(needle[index]))
                    index++;
                if (index == needle.Length) return true;
            }
            return false;
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
