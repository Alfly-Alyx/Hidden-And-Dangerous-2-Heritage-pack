using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class PairedSignalTargetInstaller
    {
        private const string ArcticPath = "Scripts/ARCTIC3/R_Ar3_Wood_1.scr";
        private const string CzechPath = "Scripts/CZECH3/ovladacblockeru.scr";
        private const string AlpsForge16Path = "Scripts/ALPS1/detector_forge16.scr";
        private const string AlpsForge20Path = "Scripts/ALPS1/detector_forge20.scr";
        private const string AlpsForge30Path = "Scripts/ALPS1/detector_forge30.scr";
        private const string AlpsDogCarnagePath = "Scripts/ALPS1/ge_08_car.scr";
        private const string AlpsRegistryPath = "Missions/ALPS1/Scripts.dta";
        private const string AlpsActorsPath = "Missions/ALPS1/actors.bin";
        private const string AlpsCheckpointsPath = "Missions/ALPS1/check2.bin";

        private static readonly string[] ScriptPaths = {
            ArcticPath, CzechPath, AlpsForge16Path, AlpsForge20Path, AlpsForge30Path,
            AlpsDogCarnagePath
        };

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
                        "La seconde cible semble deja corrigee dans " + relative + ".");
                ValidatePatched(relative, patched);
                if (!BytesEqual(patched, PatchScript(relative, patched)))
                    throw new InvalidDataException(
                        "La correction de cible n'est pas idempotente dans "
                        + relative + ".");
            }
            ValidateAssets(gamePath);
            return "Arctic 3, Czech 3 et Alps 1 verifies : les ordres oublies et la route Carnage du maitre-chien sont reactives.";
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
                "Restauration des destinataires oublies et de la route Carnage dans Arctic 3, Czech 3 et Alps 1...");
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
                "Arctic 3 / Czech 3 / Alps 1 : " + changed
                + " doubles destinataires corriges.");
            InstallerCore.Report(progress,
                "Les groupes Arctic 3 et Czech 3, les gardes de forge et le maitre-chien Carnage d'Alps 1 reagissent de nouveau.");
        }

        private static byte[] PatchScript(string relative, byte[] data)
        {
            if (String.Equals(relative, ArcticPath,
                StringComparison.OrdinalIgnoreCase))
                return ReplaceSecondTarget(data, "W2", "W3", 5);
            if (String.Equals(relative, CzechPath,
                StringComparison.OrdinalIgnoreCase))
                return ReplaceSecondTarget(data, "detect", "detect1", 1);
            if (String.Equals(relative, AlpsForge16Path,
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantSignal(data, "ge11", 1);
            if (String.Equals(relative, AlpsForge20Path,
                StringComparison.OrdinalIgnoreCase))
            {
                data = ActivateDormantSignal(data, "ge10", 1);
                return ActivateDormantSignal(data, "ge11", 1);
            }
            if (String.Equals(relative, AlpsForge30Path,
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantSignal(data, "ge43", 2);
            if (String.Equals(relative, AlpsDogCarnagePath,
                StringComparison.OrdinalIgnoreCase))
                return PatchAlpsDogCarnage(data);
            throw new InvalidDataException(
                "Script de cible appariee non pris en charge : " + relative);
        }

        private static byte[] PatchAlpsDogCarnage(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex activeMove = DogCarnageMoveRegex(false);
            Regex dormantMove = DogCarnageMoveRegex(true);
            int activeCount = activeMove.Matches(text).Count;
            int dormantCount = dormantMove.Matches(text).Count;
            if (activeCount == 0 && dormantCount == 1)
                data = ansi.GetBytes(dormantMove.Replace(
                    text, "$1$2$3$4", 1));
            else if (activeCount != 1 || dormantCount != 0)
                throw new InvalidDataException(
                    "Route Carnage ge08_02 absente ou ambigue.");
            return ActivateDormantSignal(data, "pes", 2);
        }

        private static Regex DogCarnageMoveRegex(bool dormant)
        {
            string prefix = dormant
                ? @"([ \t]*)//([ \t]*)(" : @"[ \t]*";
            string suffix = dormant ? @")(\r?)" : @"\r?";
            return new Regex(
                @"(?m)^" + prefix + @"HUMAN_Move\s*\("
                + @"\s*""ge08_02""\s*\)\s*;[ \t]*"
                + suffix + @"$", RegexOptions.IgnoreCase);
        }

        private static byte[] ActivateDormantSignal(
            byte[] data, string actor, int signal)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = SignalRegex(actor, signal);
            Regex dormant = DormantSignalRegex(actor, signal);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == 1 && dormantCount == 0) return data;
            if (activeCount != 0 || dormantCount != 1)
                throw new InvalidDataException(
                    "Signal dormant absent ou ambigu vers " + actor + ".");
            return ansi.GetBytes(dormant.Replace(
                text, "$1$2$3$4", 1));
        }

        private static Regex DormantSignalRegex(string actor, int signal)
        {
            return new Regex(
                @"(?m)^([ \t]*)//([ \t]*)(SendSignal\s*\(\s*"
                + Regex.Escape(actor) + @"\s*,\s*" + signal
                + @"\s*\)\s*;[ \t]*)(\r?)$",
                RegexOptions.IgnoreCase);
        }

        private static byte[] ReplaceSecondTarget(
            byte[] data, string duplicate, string second, int signal)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex firstRegex = SignalRegex(duplicate, signal);
            Regex secondRegex = SignalRegex(second, signal);
            int firstCount = firstRegex.Matches(text).Count;
            int secondCount = secondRegex.Matches(text).Count;
            if (firstCount == 1 && secondCount == 1)
                return data;
            if (firstCount != 2 || secondCount != 0)
                throw new InvalidDataException(
                    "Structure inattendue de l'ordre vers " + duplicate + ".");

            int seen = 0;
            string patched = firstRegex.Replace(text, delegate(Match match) {
                seen++;
                if (seen != 2) return match.Value;
                return match.Groups[1].Value + second + match.Groups[2].Value;
            });
            return ansi.GetBytes(patched);
        }

        private static Regex SignalRegex(string variable, int signal)
        {
            return new Regex(
                @"(?m)^(\s*SendSignal\s*\(\s*)" + Regex.Escape(variable)
                + @"(\s*,\s*" + signal + @"\s*\)\s*;\s*)$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(string relative, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (String.Equals(relative, ArcticPath,
                StringComparison.OrdinalIgnoreCase))
            {
                RequirePair(text, "W2", "W3", 5, "Arctic 3");
                Require(text, @"FRM_FindFrame\s*\(\s*W3\s*,\s*""Wood_3""\s*\)",
                    "Declaration de Wood_3 absente du chef de groupe Arctic 3.");
                return;
            }
            if (String.Equals(relative, CzechPath,
                StringComparison.OrdinalIgnoreCase))
            {
                RequirePair(text, "detect", "detect1", 1, "Czech 3");
                Require(text,
                    @"FRM_FindFrame\s*\(\s*detect1\s*,\s*""detector_blockerz1""\s*\)",
                    "Declaration du second detecteur Czech 3 absente.");
                return;
            }
            if (String.Equals(relative, AlpsForge16Path,
                StringComparison.OrdinalIgnoreCase))
            {
                RequireActivatedSignal(text, "ge11", 1);
                return;
            }
            if (String.Equals(relative, AlpsForge20Path,
                StringComparison.OrdinalIgnoreCase))
            {
                RequireActivatedSignal(text, "ge10", 1);
                RequireActivatedSignal(text, "ge11", 1);
                return;
            }
            if (String.Equals(relative, AlpsForge30Path,
                StringComparison.OrdinalIgnoreCase))
            {
                RequireActivatedSignal(text, "ge43", 2);
                return;
            }
            if (String.Equals(relative, AlpsDogCarnagePath,
                StringComparison.OrdinalIgnoreCase))
            {
                if (DogCarnageMoveRegex(false).Matches(text).Count != 1
                    || DogCarnageMoveRegex(true).Matches(text).Count != 0)
                    throw new InvalidDataException(
                        "Route Carnage ge08_02 incomplete.");
                RequireActivatedSignal(text, "pes", 2);
                Require(text,
                    @"_SignalReceived\s*\(\s*10\s*\)[\s\S]{0,220}"
                    + @"FORMATION_DelMember[\s\S]{0,120}"
                    + @"HUMAN_Move\s*\(\s*""ge08_02""\s*\)"
                    + @"[\s\S]{0,80}SendSignal\s*\(\s*pes\s*,\s*2\s*\)",
                    "Branche Carnage du maitre-chien incomplete.");
                return;
            }
            throw new InvalidDataException(
                "Script de cible appariee non pris en charge : " + relative);
        }

        private static void RequireActivatedSignal(
            string text, string actor, int signal)
        {
            if (SignalRegex(actor, signal).Matches(text).Count != 1
                || DormantSignalRegex(actor, signal).Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Signal restaure incomplet vers " + actor + ".");
        }

        private static void RequirePair(
            string text, string first, string second, int signal, string mission)
        {
            if (SignalRegex(first, signal).Matches(text).Count != 1
                || SignalRegex(second, signal).Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Les deux destinataires de " + mission
                    + " ne recoivent pas chacun leur ordre.");
        }

        private static void ValidateAssets(string gamePath)
        {
            foreach (string actor in new[] { "2", "3" })
            {
                string wood = ReadText(ResolveSource(gamePath,
                    "Scripts/ARCTIC3/R_Ar3_Wood_" + actor + ".scr",
                    ScriptArchives));
                Require(wood,
                    @"OnSignal\s*\(\s*5\s*\)[\s\S]{0,80}Goto\s+Dealarm",
                    "Reaction 5 officielle absente pour Wood_" + actor + ".");
            }

            string detector = ReadText(ResolveSource(gamePath,
                "Scripts/CZECH3/detector_blockerz.scr", ScriptArchives));
            Require(detector,
                @"_SignalReceived\s*\(\s*1\s*\)[\s\S]{0,100}SetWhenever\s*\(\s*player\s*,\s*1\s*\)",
                "Activation officielle des detecteurs Czech 3 absente.");

            byte[] arcticRegistry = ReadSource(ResolveSource(gamePath,
                "Missions/ARCTIC3/Scripts.dta", MissionArchives));
            if (!HasBinding(arcticRegistry,
                    "Wood_1", "R_Ar3_Wood_1.scr", "Arctic 3")
                || !HasBinding(arcticRegistry,
                    "Wood_2", "R_Ar3_Wood_2.scr", "Arctic 3")
                || !HasBinding(arcticRegistry,
                    "Wood_3", "R_Ar3_Wood_3.scr", "Arctic 3"))
                throw new InvalidDataException(
                    "Liaisons officielles du groupe Wood Arctic 3 incompletes.");

            byte[] czechRegistry = ReadSource(ResolveSource(gamePath,
                "Missions/CZECH3/Scripts.dta", MissionArchives));
            if (!HasBinding(czechRegistry,
                    "ovladacblockeru", "ovladacblockeru.scr", "Czech 3")
                || !HasBinding(czechRegistry,
                    "detector_blockerz", "detector_blockerz.scr", "Czech 3")
                || !HasBinding(czechRegistry,
                    "detector_blockerz1", "detector_blockerz.scr", "Czech 3"))
                throw new InvalidDataException(
                    "Liaisons officielles des detecteurs Czech 3 incompletes.");

            ValidateAlpsAssets(gamePath);
        }

        private static void ValidateAlpsAssets(string gamePath)
        {
            string ge10 = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/ge_10.scr", ScriptArchives));
            Require(ge10,
                @"_SignalReceived\s*\(\s*1\s*\)[\s\S]{0,250}"
                + @"HUMAN_Suspend\s*\(\s*0\s*\)[\s\S]{0,200}"
                + @"goto\s+flakejse",
                "Activation officielle ge_10 incomplete.");

            string ge11 = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/ge_11.scr", ScriptArchives));
            Require(ge11,
                @"_SignalReceived\s*\(\s*1\s*\)[\s\S]{0,250}"
                + @"HUMAN_Suspend\s*\(\s*0\s*\)[\s\S]{0,250}"
                + @"goto\s+flakejse",
                "Activation officielle ge_11 incomplete.");

            string ge43 = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/ge_43.scr", ScriptArchives));
            Require(ge43,
                @"_SignalReceived\s*\(\s*2\s*\)[\s\S]{0,180}"
                + @"HUMAN_Move\s*\(\s*""ge43_01""\s*\)"
                + @"[\s\S]{0,80}goto\s+loop",
                "Activation officielle ge_43 incomplete.");

            string dogCarnage = ReadText(ResolveSource(gamePath,
                AlpsDogCarnagePath, ScriptArchives));
            Require(dogCarnage,
                @"_SignalReceived\s*\(\s*10\s*\)[\s\S]{0,100}"
                + @"FORMATION_DelMember",
                "Declencheur 10 Carnage du maitre-chien absent.");

            string dogNormal = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/ge_08.scr", ScriptArchives));
            Require(dogNormal,
                @"_SignalReceived\s*\(\s*10\s*\)[\s\S]{0,220}"
                + @"HUMAN_Move\s*\(\s*""ge08_01""\s*\)"
                + @"[\s\S]{0,80}SendSignal\s*\(\s*pes\s*,\s*2\s*\)",
                "Route normale de reference du maitre-chien absente.");

            string dog = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/pes.scr", ScriptArchives));
            Require(dog,
                @"_SignalReceived\s*\(\s*2\s*\)[\s\S]{0,100}"
                + @"DOG_Suspend\s*\(\s*1\s*\)",
                "Reaction 2 officielle du chien absente.");

            string modeSelector = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/setobjectives.scr", ScriptArchives));
            Require(modeSelector,
                @"_SPGetGameType\s*\(\s*\)[\s\S]{0,180}"
                + @"mrd\s*==\s*3[\s\S]{0,80}mrd\s*==\s*7"
                + @"[\s\S]{0,900}ScriptAssign\s*\(\s*ge_08\s*,"
                + @"\s*""ge_08_car\.scr""\s*\)",
                "Selection officielle de ge_08_car en Carnage absente.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, AlpsRegistryPath, MissionArchives));
            foreach (string[] binding in new[] {
                new[] { "detector_forge16_1", "detector_forge16.scr" },
                new[] { "detector_forge20_1", "detector_forge20.scr" },
                new[] { "detector_forge30", "detector_forge30.scr" },
                new[] { "ge_10", "ge_10.scr" },
                new[] { "ge_11", "ge_11.scr" },
                new[] { "ge_43", "ge_43.scr" },
                new[] { "ge_08", "ge_08.scr" },
                new[] { "pes", "pes.scr" },
                new[] { "setobjectyves", "setobjectives.scr" }
            })
                if (!HasBinding(registry, binding[0], binding[1], "Alps 1"))
                    throw new InvalidDataException(
                        "Liaison Alps 1 absente : " + binding[0] + ".");

            byte[] actors = ReadSource(ResolveSource(
                gamePath, AlpsActorsPath, MissionArchives));
            foreach (string actor in new[] { "ge_10", "ge_11", "ge_43", "ge_08" })
                if (CountTypedString(actors, actor) != 1)
                    throw new InvalidDataException(
                        "Acteur Alps 1 absent ou ambigu : " + actor + ".");

            if (CountTypedString(actors, "pes") < 1)
                throw new InvalidDataException(
                    "Acteur officiel du chien Alps 1 absent.");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, AlpsCheckpointsPath, MissionArchives));
            foreach (string checkpoint in new[] {
                "ge10_01", "ge10_02", "ge10_03", "ge10_04",
                "ge10_05", "ge10_06", "ge10_07", "ge10_08",
                "ge11_01", "ge11_02", "ge11_03", "ge11_04",
                "ge43_01", "ge43_02", "ge43_03",
                "ge08_01", "ge08_02"
            })
                if (CountAscii(checkpoints, checkpoint) != 1)
                    throw new InvalidDataException(
                        "Point Alps 1 absent ou ambigu : " + checkpoint + ".");
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

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript, string mission)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts " + mission + " trop court.");
            int offset = 6;
            while (offset < data.Length)
            {
                string actor = ReadRegistryField(data, ref offset, mission);
                string script = ReadRegistryField(data, ref offset, mission);
                if (String.Equals(actor, wantedActor,
                        StringComparison.OrdinalIgnoreCase)
                    && String.Equals(script, wantedScript,
                        StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static string ReadRegistryField(
            byte[] data, ref int offset, string mission)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException(
                    "Registre de scripts " + mission + " tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre " + mission + ".");
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