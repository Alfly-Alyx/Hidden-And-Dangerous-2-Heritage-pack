using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa2GuardSignalInstaller
    {
        private static readonly string[] ScriptPaths = {
            "Scripts/AFRICA2/AF2_activator.scr",
            "Scripts/AFRICA2/AF2_01_cardet.scr",
            "Scripts/AFRICA2/AF2_15.scr",
            "Scripts/AFRICA2/AF2_dummy_alert01.scr"
        };

        private const string RegistryPath = "Missions/AFRICA2/Scripts.dta";
        private const string ActorsPath = "Missions/AFRICA2/actors.bin";
        private const string CheckpointsPath = "Missions/AFRICA2/check2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (string relative in ScriptPaths)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(relative, original);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "Le reveil des gardes Africa 2 semble deja corrige dans "
                        + relative + ".");
                ValidatePatched(relative, patched);
                if (!BytesEqual(patched, PatchScript(relative, patched)))
                    throw new InvalidDataException(
                        "Le correctif des gardes Africa 2 n'est pas idempotent.");
            }
            ValidateAssets(gamePath);
            return "Africa 2 verifie : AF2_02 et AF2_05 retrouvent leurs bons signaux, "
                + "et AF2_03 ses trois raccordements officiels ; la coordination 14-15 est reactivee.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string relative in ScriptPaths)
                {
                    string target = InstallerCore.SafeGameTarget(gamePath, relative);
                    if (!File.Exists(target)) return false;
                    ValidatePatched(relative, File.ReadAllBytes(target));
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
                "Restauration des alertes et de la coordination rapprochee oubliees dans Africa 2...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (string relative in ScriptPaths)
            {
                DormantSource source = ResolveSource(
                    gamePath, relative, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(relative, original);
                ValidatePatched(relative, patched);
                if (BytesEqual(original, patched)) continue;

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
                changed++;
            }
            InstallerCore.Log(
                "Africa 2 : " + changed + " emetteurs d'alerte corriges.");
            InstallerCore.Report(progress,
                "AF2_02 et AF2_05 retrouvent leurs bons signaux, AF2_03 ses trois declencheurs et les gardes 14-15 leur sequence rapprochee.");
        }

        private static byte[] PatchScript(string relative, byte[] data)
        {
            if (relative.EndsWith("AF2_activator.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                data = ReplaceSignal(data, "af2_02", 5, 20);
                return PatchGuard03Connections(data, "af2_03", 1, 5);
            }
            if (relative.EndsWith("AF2_01_cardet.scr",
                StringComparison.OrdinalIgnoreCase))
                return PatchGuard03Connections(data, "af2_03", 1);
            if (relative.EndsWith("AF2_15.scr",
                StringComparison.OrdinalIgnoreCase))
                return PatchShortRangeCoordination(data);
            if (relative.EndsWith("AF2_dummy_alert01.scr",
                StringComparison.OrdinalIgnoreCase))
                return PatchGlobalAlert(data);
            throw new InvalidDataException(
                "Script Africa 2 non pris en charge : " + relative);
        }

        private static byte[] PatchShortRangeCoordination(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex dormantBlock = ShortRangeBlockRegex(true);
            Regex activeBlock = ShortRangeBlockRegex(false);
            Regex dormantAlarm = ShortRangeAlarmRegex(true);
            Regex activeAlarm = ShortRangeAlarmRegex(false);
            int dormantBlockCount = dormantBlock.Matches(text).Count;
            int activeBlockCount = activeBlock.Matches(text).Count;
            int dormantAlarmCount = dormantAlarm.Matches(text).Count;
            int activeAlarmCount = activeAlarm.Matches(text).Count;
            if (dormantBlockCount == 0 && activeBlockCount == 1
                && dormantAlarmCount == 0 && activeAlarmCount == 1)
                return data;
            if (dormantBlockCount != 1 || activeBlockCount != 0
                || dormantAlarmCount != 1 || activeAlarmCount != 0)
                throw new InvalidDataException(
                    "Structure inattendue de la coordination AF2_14/AF2_15.");
            text = dormantBlock.Replace(text, UncommentLines, 1);
            text = dormantAlarm.Replace(text, UncommentLines, 1);
            return ansi.GetBytes(text);
        }

        private static string UncommentLines(Match match)
        {
            return Regex.Replace(
                match.Value, @"(?m)^([ \t]*)//", "$1");
        }

        private static Regex ShortRangeBlockRegex(bool dormant)
        {
            string prefix = dormant ? @"[ \t]*//[ \t]*" : @"[ \t]*";
            return new Regex(
                @"(?m)^" + prefix
                + @"Whenever[ \t]+inshortrange\s*\(\s*_PlayerInRange"
                + @"\s*\(\s*130\s*\)\s*\)\s*\{"
                + @"\r?\n" + prefix
                + @"SendSignal\s*\(\s*af14\s*,\s*10\s*\)\s*;"
                + @"[ \t]*\r?\n" + prefix
                + @"goto[ \t]+ACTIVITYEND\s*;[ \t]*"
                + @"\r?\n" + prefix + @"\}[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static Regex ShortRangeAlarmRegex(bool dormant)
        {
            string prefix = dormant ? @"[ \t]*//[ \t]*" : @"[ \t]*";
            return new Regex(
                @"(?m)^" + prefix + @"SetWhenever\s*\("
                + @"\s*inshortrange\s*,\s*false\s*\)\s*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static byte[] PatchGlobalAlert(byte[] data)
        {
            data = ReplaceSignal(data, "en05", 20, 5);
            return PatchGuard03Connections(data, "en03", 20);
        }

        private static byte[] PatchGuard03Connections(
            byte[] data, string handle, params int[] signals)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = ActivateLine(text,
                Guard03DeclarationRegex(handle, true),
                Guard03DeclarationRegex(handle, false),
                "declaration " + handle);
            foreach (int signal in signals)
                text = ActivateLine(text,
                    Guard03SignalRegex(handle, signal, true),
                    Guard03SignalRegex(handle, signal, false),
                    "signal " + signal + " vers " + handle);
            return ansi.GetBytes(text);
        }

        private static Regex Guard03DeclarationRegex(
            string handle, bool dormant)
        {
            string actor = Regex.Escape(handle);
            string pattern = dormant
                ? @"(?m)^([ \t]*)//([ \t]*)(FRAME[ \t]+" + actor
                    + @"[ \t]*;[ \t]*FRM_FindFrame[ \t]*\([ \t]*"
                    + actor + @"[ \t]*,[ \t]*""AF2_03""[ \t]*\)"
                    + @"[ \t]*;[^\r\n]*)(\r?)$"
                : @"(?m)^[ \t]*FRAME[ \t]+" + actor
                    + @"[ \t]*;[ \t]*FRM_FindFrame[ \t]*\([ \t]*"
                    + actor + @"[ \t]*,[ \t]*""AF2_03""[ \t]*\)"
                    + @"[ \t]*;[^\r\n]*\r?$";
            return new Regex(pattern, RegexOptions.IgnoreCase);
        }

        private static Regex Guard03SignalRegex(
            string handle, int signal, bool dormant)
        {
            string actor = Regex.Escape(handle);
            string pattern = dormant
                ? @"(?m)^([ \t]*)//([ \t]*)(SendSignal\s*\(\s*"
                    + actor + @"\s*,\s*" + signal
                    + @"\s*\)\s*;[ \t]*)(\r?)$"
                : @"(?m)^[ \t]*SendSignal\s*\(\s*" + actor
                    + @"\s*,\s*" + signal + @"\s*\)\s*;[ \t]*\r?$";
            return new Regex(pattern, RegexOptions.IgnoreCase);
        }

        private static string ActivateLine(
            string text, Regex dormant, Regex active,
            string label)
        {
            int dormantCount = dormant.Matches(text).Count;
            int activeCount = active.Matches(text).Count;
            if (dormantCount == 0 && activeCount == 1) return text;
            if (dormantCount != 1 || activeCount != 0)
                throw new InvalidDataException(
                    "Structure inattendue de " + label + ".");
            return dormant.Replace(text, "$1$2$3$4", 1);
        }

        private static byte[] ReplaceSignal(
            byte[] data, string actor, int wrong, int correct)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = SignalRegex(actor, correct);
            Regex obsolete = SignalRegex(actor, wrong);
            if (active.Matches(text).Count == 1
                && obsolete.Matches(text).Count == 0)
                return data;
            if (active.Matches(text).Count != 0
                || obsolete.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du signal vers " + actor + ".");
            return ansi.GetBytes(obsolete.Replace(
                text, "${1}" + correct + "${2}", 1));
        }

        private static Regex SignalRegex(string actor, int signal)
        {
            return new Regex(
                @"(?m)^(\s*SendSignal\s*\(\s*" + Regex.Escape(actor)
                + @"\s*,\s*)" + signal + @"(\s*\)\s*;\s*)$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(string relative, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (relative.EndsWith("AF2_activator.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                RequireOnlySignal(text, "af2_02", 20, 5);
                RequireGuard03Connections(text, "af2_03", 1, 5);
            }
            else if (relative.EndsWith("AF2_01_cardet.scr",
                StringComparison.OrdinalIgnoreCase))
                RequireGuard03Connections(text, "af2_03", 1);
            else if (relative.EndsWith("AF2_15.scr",
                StringComparison.OrdinalIgnoreCase))
                ValidateShortRangeCoordination(text);
            else if (relative.EndsWith("AF2_dummy_alert01.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                RequireOnlySignal(text, "en05", 5, 20);
                RequireGuard03Connections(text, "en03", 20);
            }
            else
                throw new InvalidDataException(
                    "Script Africa 2 non pris en charge : " + relative);
        }

        private static void ValidateShortRangeCoordination(string text)
        {
            if (ShortRangeBlockRegex(false).Matches(text).Count != 1
                || ShortRangeBlockRegex(true).Matches(text).Count != 0
                || ShortRangeAlarmRegex(false).Matches(text).Count != 1
                || ShortRangeAlarmRegex(true).Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Coordination rapprochee AF2_14/AF2_15 incomplete.");
            Require(text,
                @"OnAlarm\s*\(\s*\)[\s\S]{0,500}"
                + @"SetWhenever\s*\(\s*inlongrange\s*,\s*false\s*\)"
                + @"[\s\S]{0,100}SetWhenever\s*\("
                + @"\s*inshortrange\s*,\s*false\s*\)",
                "Arret du detecteur rapproche absent pendant l'alarme.");
            Require(text,
                @"Label\s+ACTIVITYEND\s*:[\s\S]{0,300}"
                + @"HUMAN_Move\s*\(\s*""AF2_14_01""\s*\)"
                + @"[\s\S]{0,100}HUMAN_Move\s*\(\s*""AF2_14_02""\s*\)"
                + @"[\s\S]{0,100}HUMAN_Move\s*\(\s*""AF2_14_03""\s*\)",
                "Trajet rapproche officiel AF2_15 incomplet.");
        }

        private static void RequireGuard03Connections(
            string text, string handle, params int[] signals)
        {
            if (Guard03DeclarationRegex(handle, false).Matches(text).Count != 1
                || Guard03DeclarationRegex(handle, true).Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Declaration invalide pour " + handle + ".");
            foreach (int signal in signals)
                if (Guard03SignalRegex(handle, signal, false)
                        .Matches(text).Count != 1
                    || Guard03SignalRegex(handle, signal, true)
                        .Matches(text).Count != 0)
                    throw new InvalidDataException(
                        "Raccordement invalide du signal " + signal
                        + " vers " + handle + ".");
        }

        private static void RequireOnlySignal(
            string text, string actor, int expected, int forbidden)
        {
            if (SignalRegex(actor, expected).Matches(text).Count != 1
                || SignalRegex(actor, forbidden).Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Signal d'alerte invalide vers " + actor + ".");
        }

        private static void ValidateAssets(string gamePath)
        {
            string actor02 = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_02.scr", ScriptArchives));
            RequireHandler(actor02, 20, "AF2_02");
            ForbidHandler(actor02, 5, "AF2_02");
            Require(actor02,
                @"OnSignal\s*\(\s*20\s*\)[\s\S]{0,60}goto\s+ALERT[\s\S]{0,3000}Label\s+ALERT\s*:[\s\S]{0,300}HUMAN_Move\s*\(\s*""AF2_02_alert""\s*\)",
                "Route d'alerte officielle AF2_02 incomplete.");

            string actor03 = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_03.scr", ScriptArchives));
            RequireHandler(actor03, 1, "AF2_03");
            RequireHandler(actor03, 5, "AF2_03");
            RequireHandler(actor03, 20, "AF2_03");
            Require(actor03,
                @"OnSignal\s*\(\s*1\s*\)[\s\S]{0,60}goto\s+ACTIVATE[\s\S]{0,3000}Label\s+ACTIVATE\s*:[\s\S]{0,300}HUMAN_Move\s*\(\s*""AF2_03_01""\s*\)",
                "Route d'activation officielle AF2_03 incomplete.");
            Require(actor03,
                @"OnSignal\s*\(\s*5\s*\)[\s\S]{0,300}HUMAN_Move\s*\(\s*""AF2_03_alert""\s*\)",
                "Reaction directe officielle AF2_03 incomplete.");
            Require(actor03,
                @"OnSignal\s*\(\s*20\s*\)[\s\S]{0,60}goto\s+ALERT[\s\S]{0,3000}Label\s+ALERT\s*:[\s\S]{0,300}HUMAN_Move\s*\(\s*""AF2_03_alert""\s*\)",
                "Route d'alerte officielle AF2_03 incomplete.");

            string actor14 = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_14.scr", ScriptArchives));
            Require(actor14,
                @"OnSignal\s*\(\s*10\s*\)[\s\S]{0,80}goto\s+ACTIVITY"
                + @"[\s\S]{0,2500}Label\s+ACTIVITY\s*:"
                + @"[\s\S]{0,120}HUMAN_SetAnim\s*\(\s*""%%sedimL""",
                "Reaction officielle AF2_14 au signal 10 incomplete.");

            string actor15 = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_15.scr", ScriptArchives));
            Require(actor15,
                @"Label\s+ACTIVITYEND\s*:[\s\S]{0,300}"
                + @"HUMAN_Move\s*\(\s*""AF2_14_01""\s*\)"
                + @"[\s\S]{0,100}HUMAN_Move\s*\(\s*""AF2_14_02""\s*\)"
                + @"[\s\S]{0,100}HUMAN_Move\s*\(\s*""AF2_14_03""\s*\)",
                "Trajet officiel AF2_15 incomplet.");

            string actor05 = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_05.scr", ScriptArchives));
            RequireHandler(actor05, 5, "AF2_05");
            ForbidHandler(actor05, 20, "AF2_05");
            Require(actor05,
                @"OnSignal\s*\(\s*5\s*\)[\s\S]{0,300}HUMAN_Move\s*\(\s*""AF2_05_alert""\s*\)",
                "Route d'alerte officielle AF2_05 incomplete.");

            string activator = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_activator.scr", ScriptArchives));
            foreach (string actor in new[] {
                "af2_01", "af2_04", "af2_05", "af2_06"
            })
                if (SignalRegex(actor, 5).Matches(activator).Count != 1)
                    throw new InvalidDataException(
                        "Signal 5 de reference absent vers " + actor + ".");

            string global = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_dummy_alert01.scr", ScriptArchives));
            foreach (string actor in new[] {
                "en01", "en02", "en04", "en06"
            })
                if (SignalRegex(actor, 20).Matches(global).Count != 1)
                    throw new InvalidDataException(
                        "Signal 20 de reference absent vers " + actor + ".");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "af2_activator", "AF2_activator.scr")
                || !HasBinding(registry,
                    "AF2_01_cardet", "AF2_01_cardet.scr")
                || !HasBinding(registry,
                    "dummy_alert01", "AF2_dummy_alert01.scr")
                || !HasBinding(registry, "AF2_02", "AF2_02.scr")
                || !HasBinding(registry, "AF2_03", "AF2_03.scr")
                || !HasBinding(registry, "AF2_05", "AF2_05.scr")
                || !HasBinding(registry, "AF2_14", "AF2_14.scr")
                || !HasBinding(registry, "AF2_15", "AF2_15.scr"))
                throw new InvalidDataException(
                    "Liaisons officielles du groupe de gardes Africa 2 incompletes.");

            ValidateCoordinationAssets(gamePath);
        }

        private static void ValidateCoordinationAssets(string gamePath)
        {
            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            foreach (string actor in new[] { "AF2_14", "AF2_15" })
                if (CountTypedString(actors, actor) != 1)
                    throw new InvalidDataException(
                        "Acteur officiel " + actor + " absent ou ambigu.");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            foreach (string checkpoint in new[] {
                "AF2_14_01", "AF2_14_02", "AF2_14_03"
            })
                if (CountAscii(checkpoints, checkpoint) != 1)
                    throw new InvalidDataException(
                        "Point officiel " + checkpoint + " absent ou ambigu.");
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

        private static void RequireHandler(
            string text, int signal, string actor)
        {
            Require(text, @"OnSignal\s*\(\s*" + signal + @"\s*\)",
                "Signal " + signal + " absent pour " + actor + ".");
        }

        private static void ForbidHandler(
            string text, int signal, string actor)
        {
            if (Regex.IsMatch(text,
                @"OnSignal\s*\(\s*" + signal + @"\s*\)",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le signal obsolete " + signal + " existe deja pour " + actor + ".");
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 2 trop court.");
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
                    "Registre de scripts Africa 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 2.");
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

        private static string ReadText(DormantSource source)
        {
            return Encoding.GetEncoding(1252).GetString(ReadSource(source));
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