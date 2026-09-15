using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa3DormantSentryInstaller
    {
        private const string RegistryPath = "Missions/AFRICA3/scripts.dta";
        private const string ActorsPath = "Missions/AFRICA3/actors.bin";
        private const string CheckpointsPath = "Missions/AFRICA3/check2.bin";
        private const string ScenePath = "Missions/AFRICA3/scene2.bin";

        private static readonly string[] Actors = {
            "AF3a_06", "AF3a_16", "AF3a_25", "AF3a_28",
            "AF3a_29", "AF3a_31", "AF3a_32", "AF3a_33",
            "AF3a_34", "AF3a_35", "AF3a_36", "AF3a_37"
        };

        private static readonly string[] EventActors = {
            "AF3a_25", "AF3a_28", "AF3a_29", "AF3a_31", "AF3a_32"
        };

        private static readonly string[] AmbushLookFrames = {
            "oa_dv91", "oa_dv64", "oa_dv74", "oa_dv103", "oa_dv97"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (string actor in Actors)
            {
                string relative = ScriptPath(actor);
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(original, actor);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "Le poste dormant de " + actor + " semble deja actif.");
                ValidatePatched(patched, actor);
                if (!BytesEqual(patched, PatchScript(patched, actor)))
                    throw new InvalidDataException(
                        "La restauration de " + actor + " n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Africa 3 verifiee : douze sentinelles retrouvent leurs "
                + "reactions, evenements et postes de combat.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string actor in Actors)
                {
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, ScriptPath(actor));
                    if (!File.Exists(target)) return false;
                    ValidatePatched(File.ReadAllBytes(target), actor);
                }
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
                "Restauration des postes de combat dormants d'Africa 3...");
            ValidateAssets(gamePath);
            bool changed = false;
            foreach (string actor in Actors)
                changed |= InstallOne(
                    gamePath, actor, journal, prepared);
            if (!changed)
            {
                InstallerCore.Report(progress,
                    "Les postes de combat dormants d'Africa 3 sont deja actifs.");
                return;
            }

            InstallerCore.Log(
                "Africa 3 : reactions des gardes 06 et 16, evenements "
                + "des gardes 25, 28, 29, 31 et 32, et postes "
                + "des sentinelles 33 a 37 restaures.");
            InstallerCore.Report(progress,
                "Les douze sentinelles d'Africa 3 retrouvent leurs ordres de combat.");
        }

        private static bool InstallOne(
            string gamePath, string actor, StateJournal journal,
            HashSet<string> prepared)
        {
            string relative = ScriptPath(actor);
            DormantSource source = ResolveSource(
                gamePath, relative, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original, actor);
            ValidatePatched(patched, actor);
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

        private static string ScriptPath(string actor)
        {
            return "Scripts/AFRICA3/" + actor + ".scr";
        }

        private static byte[] PatchScript(byte[] data, string actor)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (String.Equals(actor, "AF3a_06",
                    StringComparison.OrdinalIgnoreCase))
            {
                text = ActivateInSection(
                    text, OnAlarmStart(), OnAlarmDoneStart(),
                    @"HUMAN_SETMODE_Crouch\s*\(\s*\)\s*;",
                    "posture accroupie du garde 06");
                text = ActivateInSection(
                    text, OnAlarmStart(), OnAlarmDoneStart(),
                    @"HUMAN_SetSniper\s*\(\s*true\s*,\s*5\s*\)\s*;",
                    "poste defensif du garde 06");
            }
            else if (String.Equals(actor, "AF3a_16",
                    StringComparison.OrdinalIgnoreCase))
            {
                text = ActivateInSection(
                    text, OnAlarmStart(), OnAlarmDoneStart(),
                    @"HUMAN_SetSniper\s*\(\s*true\s*,\s*5\s*\)\s*;",
                    "poste defensif du garde 16");
            }
            else if (Contains(EventActors, actor))
            {
                text = ActivateInSection(
                    text, @"Whenever\s+player\b",
                    @"Label\s+ACTIVATE\s*:",
                    @"HUMAN_SetEvents\s*\(\s*true\s*\)\s*;",
                    "evenements d'attente de " + actor);
            }
            else
            {
                text = ActivateInSection(
                    text, @"Whenever\s+player\b",
                    @"Label\s+ACTIVATE\s*:",
                    @"HUMAN_SetSniper\s*\(\s*true\s*,\s*1\s*\)\s*;",
                    "poste d'embuscade de " + actor);
            }
            return ansi.GetBytes(text);
        }

        private static string OnAlarmStart()
        {
            return @"OnAlarm\s*\(\s*\)\s*\{";
        }

        private static string OnAlarmDoneStart()
        {
            return @"OnAlarmDone\s*\(\s*\)\s*\{";
        }

        private static string ActivateInSection(
            string text, string start, string end,
            string expression, string description)
        {
            Regex section = new Regex(
                @"(?ms)(?<start>" + start + @")(?<body>.*?)(?<end>" + end + @")",
                RegexOptions.IgnoreCase);
            MatchCollection sections = section.Matches(text);
            if (sections.Count != 1)
                throw new InvalidDataException(
                    "Section Africa 3 absente ou ambigue : " + description + ".");
            Match match = sections[0];
            string body = match.Groups["body"].Value;
            string patched = ActivateLine(body, expression, description);
            if (String.Equals(body, patched, StringComparison.Ordinal))
                return text;
            return text.Substring(0, match.Groups["body"].Index)
                + patched
                + text.Substring(
                    match.Groups["body"].Index + match.Groups["body"].Length);
        }

        private static string ActivateLine(
            string text, string expression, string description)
        {
            Regex active = new Regex(
                @"(?m)^[ \t]*" + expression
                + @"[ \t]*(?://[^\r\n]*)?\r?$",
                RegexOptions.IgnoreCase);
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>"
                + expression + @")(?<tail>[ \t]*(?://[^\r\n]*)?)\r?$",
                RegexOptions.IgnoreCase);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == 1 && dormantCount == 0) return text;
            if (activeCount != 0 || dormantCount != 1)
                throw new InvalidDataException(
                    "Instruction Africa 3 absente ou ambigue : "
                    + description + ".");
            return dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value
                    + match.Groups["tail"].Value;
            }, 1);
        }

        private static void ValidatePatched(byte[] data, string actor)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (String.Equals(actor, "AF3a_06",
                    StringComparison.OrdinalIgnoreCase))
            {
                RequireSequence(text,
                    OnAlarmStart()
                    + @"[\s\S]{0,900}?SendSignal\s*\(\s*dummy_alarm\s*,\s*1\s*\)\s*;"
                    + @"[\s\S]{0,260}?HUMAN_SETMODE_Crouch\s*\(\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SetSniper\s*\(\s*true\s*,\s*5\s*\)\s*;"
                    + @"[\s\S]{0,100}?EndScript\s*\(\s*\)\s*;",
                    "Reaction de combat du garde 06 incomplete.");
            }
            else if (String.Equals(actor, "AF3a_16",
                    StringComparison.OrdinalIgnoreCase))
            {
                RequireSequence(text,
                    OnAlarmStart()
                    + @"[\s\S]{0,1200}?HUMAN_Move\s*\(\s*""AF3a_16_05""\s*\)\s*;"
                    + @"[\s\S]{0,300}?HUMAN_SETMODE_Crouch\s*\(\s*\)\s*;"
                    + @"[\s\S]{0,160}?HUMAN_SETAIMODE_Defensive\s*\(\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SetSniper\s*\(\s*true\s*,\s*5\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SetAlarm\s*\(\s*false\s*\)\s*;",
                    "Poste defensif du garde 16 incomplet.");
            }
            else if (Contains(EventActors, actor))
            {
                RequireSequence(text,
                    @"Whenever\s+player\b[\s\S]{0,500}?"
                    + @"HUMAN_Suspend\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SetEvents\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,100}?goto\s+(?:END2|END)\s*;",
                    "Evenements d'attente de " + actor + " incomplets.");
            }
            else
            {
                RequireSequence(text,
                    @"Whenever\s+player\b[\s\S]{0,500}?"
                    + @"HUMAN_TurnAt\s*\(\s*turn1\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SetSniper\s*\(\s*true\s*,\s*1\s*\)\s*;"
                    + @"[\s\S]{0,160}?HUMAN_SETAIMODE_(?:Aggressive|Defensive)\s*\(\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SetMODE_Crouch\s*\(\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_Suspend\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,100}?goto\s+(?:END2|END)\s*;",
                    "Poste d'embuscade de " + actor + " incomplet.");
            }
        }

        private static void RequireSequence(
            string text, string pattern, string message)
        {
            if (Regex.Matches(
                    text, pattern, RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(message);
        }

        private static bool Contains(string[] values, string wanted)
        {
            foreach (string value in values)
                if (String.Equals(
                        value, wanted, StringComparison.OrdinalIgnoreCase))
                    return true;
            return false;
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            foreach (string actor in Actors)
            {
                if (!HasBinding(registry, actor, actor + ".scr"))
                    throw new InvalidDataException(
                        "Liaison Africa 3 absente pour " + actor + ".");
                if (CountAscii(actors, actor) < 1)
                    throw new InvalidDataException(
                        "Acteur Africa 3 absent : " + actor + ".");
            }

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            if (CountAscii(checkpoints, "AF3a_16_05") != 1)
                throw new InvalidDataException(
                    "Poste du minaret AF3a_16_05 absent ou ambigu.");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            foreach (string look in AmbushLookFrames)
                if (CountAscii(scene, look) != 1)
                    throw new InvalidDataException(
                        "Direction d'embuscade Africa 3 absente ou ambigue : "
                        + look + ".");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 3 trop court.");
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
                    "Registre de scripts Africa 3 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 3.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Africa 3.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
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
                    "Donnee officielle Africa 3 introuvable : " + relative);
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
