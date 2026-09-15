using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa4DormantInfantryInstaller
    {
        private const string RegistryPath = "Missions/AFRICA4/scripts.dta";
        private const string ActorsPath = "Missions/AFRICA4/actors.bin";
        private const string CheckpointsPath = "Missions/AFRICA4/check2.bin";

        private static readonly string[] PassengerActors = {
            "AF3b_03", "AF3b_04", "AF3b_07", "AF3b_09", "AF3b_10"
        };

        private static readonly string[] ReserveActors = {
            "AF3b_27", "AF3b_28", "AF3b_29", "AF3b_30"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (string actor in AllActors())
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, ScriptPath(actor), ScriptArchives));
                byte[] patched = PatchScript(original, actor);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "Le comportement dormant de " + actor
                        + " semble deja actif.");
                ValidatePatched(patched, actor);
                if (!BytesEqual(patched, PatchScript(patched, actor)))
                    throw new InvalidDataException(
                        "La restauration de " + actor
                        + " n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Africa 4 verifiee : cinq passagers restent en place "
                + "jusqu'au debarquement et quatre reserves retrouvent "
                + "leur posture aleatoire.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string actor in AllActors())
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
                "Restauration des passagers et reserves dormants d'Africa 4...");
            ValidateAssets(gamePath);
            bool changed = false;
            foreach (string actor in AllActors())
                changed |= InstallOne(
                    gamePath, actor, journal, prepared);
            if (!changed)
            {
                InstallerCore.Report(progress,
                    "Les comportements d'infanterie Africa 4 sont deja actifs.");
                return;
            }

            InstallerCore.Log(
                "Africa 4 : attente des passagers 03, 04, 07, 09 et 10 "
                + "et postures des reserves 27 a 30 restaurees.");
            InstallerCore.Report(progress,
                "Les passagers d'Opel et quatre reserves d'Africa 4 "
                + "retrouvent leurs comportements.");
        }

        private static IEnumerable<string> AllActors()
        {
            foreach (string actor in PassengerActors) yield return actor;
            foreach (string actor in ReserveActors) yield return actor;
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
            return "Scripts/AFRICA4/" + actor + ".scr";
        }

        private static byte[] PatchScript(byte[] data, string actor)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (Contains(PassengerActors, actor))
            {
                text = ActivateLine(text,
                    @"HUMAN_Suspend\s*\(\s*true\s*\)\s*;",
                    "suspension du passager " + actor);
                text = ActivateLine(text,
                    @"HUMAN_SET?EVENTS\s*\(\s*true\s*\)\s*;",
                    "evenements du passager " + actor);
            }
            else
            {
                text = ActivateLine(text,
                    @"gosub\s+CHANGEPOS\s*;",
                    "posture aleatoire de " + actor);
            }
            return ansi.GetBytes(text);
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
                    "Instruction Africa 4 absente ou ambigue : "
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
            if (Contains(PassengerActors, actor))
            {
                RequireOne(text,
                    @"HUMAN_BoardVehicle\s*\(\s*""Opel0[12]""\s*,\s*1\s*,\s*[1-4]\s*\)\s*;"
                    + @"[\s\S]{0,120}?HUMAN_Suspend\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SET?EVENTS\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,100}?goto\s+END\s*;",
                    "Attente embarquee de " + actor + " incomplete.");
            }
            else
            {
                RequireOne(text,
                    @"Label\s+ACTIVITY\s*:"
                    + @"[\s\S]{0,100}?gosub\s+CHANGEPOS\s*;"
                    + @"[\s\S]{0,100}?HUMAN_Move\s*\(\s*"""
                    + Regex.Escape(actor) + @"_01""\s*\)\s*;"
                    + @"[\s\S]{0,220}?goto\s+CROUCH_END\s*;"
                    + @"[\s\S]{0,160}?Label\s+CHANGEPOS\s*:"
                    + @"[\s\S]{0,120}?rnd\s*=\s*_RandomInt\s*\(\s*2\s*\)\s*;"
                    + @"[\s\S]{0,220}?HUMAN_SetMODE_Stand\s*\(\s*\)"
                    + @"[\s\S]{0,220}?HUMAN_SetMODE_Crouch\s*\(\s*\)"
                    + @"[\s\S]{0,100}?return\s*;",
                    "Posture aleatoire de " + actor + " incomplete.");
            }
        }

        private static void RequireOne(
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
            foreach (string actor in AllActors())
            {
                if (!HasBinding(registry, actor, actor + ".scr"))
                    throw new InvalidDataException(
                        "Liaison Africa 4 absente pour " + actor + ".");
                if (CountAscii(actors, actor) < 1)
                    throw new InvalidDataException(
                        "Acteur Africa 4 absent : " + actor + ".");
            }
            foreach (string vehicle in new[] { "Opel01", "Opel02" })
                if (CountAscii(actors, vehicle) < 1)
                    throw new InvalidDataException(
                        "Vehicule Africa 4 absent : " + vehicle + ".");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            foreach (string actor in ReserveActors)
                if (CountAscii(checkpoints, actor + "_01") != 1)
                    throw new InvalidDataException(
                        "Point de reserve Africa 4 absent ou ambigu : "
                        + actor + "_01.");

            foreach (string referenceActor in new[] { "AF3b_02", "AF3b_08" })
            {
                string reference = Encoding.GetEncoding(1252).GetString(
                    ReadSource(ResolveSource(
                        gamePath, ScriptPath(referenceActor), ScriptArchives)));
                RequireOne(reference,
                    @"HUMAN_BoardVehicle\s*\([^\r\n]+\)\s*;"
                    + @"[\s\S]{0,120}?HUMAN_Suspend\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,100}?HUMAN_SET?EVENTS\s*\(\s*true\s*\)\s*;",
                    "Passager de reference Africa 4 altere : "
                    + referenceActor + ".");
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 4 trop court.");
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
                    "Registre de scripts Africa 4 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 4.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Africa 4.");
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
                    "Donnee officielle Africa 4 introuvable : " + relative);
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
