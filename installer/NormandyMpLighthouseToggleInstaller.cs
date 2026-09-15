using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class NormandyMpLighthouseToggleInstaller
    {
        private const string ScriptPath =
            "Scripts/NORMANDY_MP/mp_N1_majak.scr";
        private const string SwitchPath =
            "Scripts/NORMANDY_MP/mp_N1_switch.scr";
        private const string RegistryPath =
            "Missions/NORMANDY_MP/mpscripts.dta";
        private const string ScenePath =
            "Missions/NORMANDY_MP/scene2.bin";
        private const string ActorsPath =
            "Missions/NORMANDY_MP/actors.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] Effects = {
            "volumetrika", "flare1", "flare2"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, ScriptPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "L'extinction du phare Normandy MP semble deja corrigee.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La correction du phare Normandy MP n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Normandy MP verifie : le second usage arrete la rotation "
                + "et eteint les trois effets du phare.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(
                    gamePath, ScriptPath);
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
                "Correction de l'interrupteur du phare dans Normandy MP...");
            ValidateAssets(gamePath);
            DormantSource source = ResolveSource(
                gamePath, ScriptPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "L'extinction du phare Normandy MP est deja corrigee.");
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
                "Normandy MP : extinction des trois effets du phare corrigee.");
            InstallerCore.Report(progress,
                "Le phare Normandy MP peut maintenant etre allume puis eteint.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex branch = StopBranchRegex();
            MatchCollection matches = branch.Matches(text);
            if (matches.Count != 1)
                throw new InvalidDataException(
                    "Branche d'arret du phare Normandy MP absente ou ambigue.");
            Match match = matches[0];
            string body = match.Groups["body"].Value;
            int activeTrue = 0;
            int activeFalse = 0;
            foreach (string effect in Effects)
            {
                activeTrue += EffectRegex(effect, true).Matches(body).Count;
                activeFalse += EffectRegex(effect, false).Matches(body).Count;
            }
            if (activeTrue == 0 && activeFalse == Effects.Length)
                return data;
            if (activeTrue != Effects.Length || activeFalse != 0)
                throw new InvalidDataException(
                    "Etat inattendu des effets dans l'arret du phare Normandy MP.");
            foreach (string effect in Effects)
                body = EffectRegex(effect, true).Replace(
                    body, "FRM_SetOn(" + effect + ", false);", 1);
            string replacement = match.Groups["start"].Value
                + body + match.Groups["end"].Value;
            string patched = text.Substring(0, match.Index) + replacement
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(patched);
        }

        private static Regex StopBranchRegex()
        {
            return new Regex(
                @"(?<start>If\s*\(\s*zapnute\s*==\s*1\s*\)"
                + @"\s*\{\s*zapnute\s*=\s*0\s*;\s*Block\s*\{)"
                + @"(?<body>[\s\S]{0,320}?)"
                + @"(?<end>\}\s*GoTo\s+stop\s*;\s*\})",
                RegexOptions.IgnoreCase);
        }

        private static Regex StartBranchRegex()
        {
            return new Regex(
                @"(?<start>If\s*\(\s*zapnute\s*==\s*0\s*\)"
                + @"\s*\{\s*zapnute\s*=\s*1\s*;\s*Block\s*\{)"
                + @"(?<body>[\s\S]{0,320}?)"
                + @"(?<end>\}\s*GoTo\s+rotate\s*;\s*\})",
                RegexOptions.IgnoreCase);
        }

        private static Regex EffectRegex(string effect, bool state)
        {
            return new Regex(
                @"FRM_SetOn\s*\(\s*" + Regex.Escape(effect)
                + @"\s*,\s*" + (state ? "true" : "false")
                + @"\s*\)\s*;",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            MatchCollection stops = StopBranchRegex().Matches(text);
            MatchCollection starts = StartBranchRegex().Matches(text);
            if (stops.Count != 1 || starts.Count != 1)
                throw new InvalidDataException(
                    "Cycle du phare Normandy MP absent ou ambigu.");
            string stop = stops[0].Groups["body"].Value;
            string start = starts[0].Groups["body"].Value;
            foreach (string effect in Effects)
            {
                if (EffectRegex(effect, false).Matches(stop).Count != 1
                    || EffectRegex(effect, true).Matches(stop).Count != 0)
                    throw new InvalidDataException(
                        "Extinction incomplete du phare Normandy MP : "
                        + effect + ".");
                if (EffectRegex(effect, true).Matches(start).Count != 1
                    || EffectRegex(effect, false).Matches(start).Count != 0)
                    throw new InvalidDataException(
                        "Allumage du phare Normandy MP altere : "
                        + effect + ".");
            }
            Require(text,
                @"Label\s+rotate\s*:[\s\S]{0,180}"
                + @"FRM_RotateY\s*\(\s*svetlo\s*,\s*360\s*,\s*9\s*\)"
                + @"[\s\S]{0,180}Label\s+stop\s*:[\s\S]{0,100}"
                + @"FRM_RotateY\s*\(\s*svetlo\s*,\s*0\s*,\s*0\s*\)",
                "Rotation et arret du phare Normandy MP incomplets.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(
                    registry, "m_maj_svet01", "mp_N1_majak.scr")
                || !HasBinding(
                    registry, "m_n1_switch_", "mp_N1_switch.scr"))
                throw new InvalidDataException(
                    "Liaisons du phare Normandy MP absentes.");

            string switchScript = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(
                    gamePath, SwitchPath, ScriptArchives)));
            Require(switchScript,
                @"OnUse\s*\(\s*\)[\s\S]{0,120}"
                + @"SendSignal\s*\(\s*svetlo\s*,\s*1\s*\)",
                "Interrupteur du phare Normandy MP incomplet.");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            foreach (string name in new[] {
                "m_maj_svet01", "majak_volum01", "vol_majak01", "vol_majak02"
            })
                if (CountAscii(scene, name) < 1)
                    throw new InvalidDataException(
                        "Objet du phare Normandy MP absent : " + name + ".");
            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            if (CountAscii(actors, "m_n1_switch_") < 1)
                throw new InvalidDataException(
                    "Interrupteur du phare Normandy MP absent des acteurs.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre Normandy MP trop court.");
            int offset = 6;
            int found = 0;
            while (offset < data.Length)
            {
                string actor = ReadRegistryField(data, ref offset);
                string script = ReadRegistryField(data, ref offset);
                if (String.Equals(actor, wantedActor,
                        StringComparison.OrdinalIgnoreCase)
                    && String.Equals(script, wantedScript,
                        StringComparison.OrdinalIgnoreCase))
                    found++;
            }
            return found == 1;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException(
                    "Registre Normandy MP tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide du registre Normandy MP.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
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
