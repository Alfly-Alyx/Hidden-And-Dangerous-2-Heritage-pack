using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Burma2DormantScenesInstaller
    {
        private static readonly string[] ScriptPaths = {
            "Scripts/BURMA2/BU2_22.scr",
            "Scripts/BURMA2/BU2_Allied11.scr",
            "Scripts/BURMA2/BU2_xplo22.scr"
        };

        private const string RegistryPath = "Missions/BURMA2/scripts.dta";
        private const string ActorsPath = "Missions/BURMA2/actors.bin";
        private const string ScenePath = "Missions/BURMA2/scene2.bin";
        private const string ModelPath = "Missions/BURMA2/Scene.4ds";

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
                        "La sequence Burma 2 semble deja active dans " + relative + ".");
                ValidatePatched(relative, patched);
                if (!BytesEqual(patched, PatchScript(relative, patched)))
                    throw new InvalidDataException(
                        "La restauration Burma 2 n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Burma 2 verifie : tir du bunker, soldat panique et explosion 22 restaures.";
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
                "Restauration des sequences dormantes de Burma 2...");
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
                "Burma 2 : " + changed + " scripts de scene restaures.");
            InstallerCore.Report(progress,
                "Tir du bunker, soldat panique et explosion 22 restaures.");
        }

        private static byte[] PatchScript(string relative, byte[] data)
        {
            if (relative.EndsWith("BU2_22.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateSingleStatement(data,
                    @"HUMAN_Attack\s*\(\s*shoot01\s*,\s*2000\s*\)\s*;");
            if (relative.EndsWith("BU2_Allied11.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateAlliedWaiting(data);
            if (relative.EndsWith("BU2_xplo22.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateExplosion(data);
            throw new InvalidDataException(
                "Script Burma 2 non pris en charge : " + relative);
        }

        private static byte[] ActivateSingleStatement(
            byte[] data, string statementPattern)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex dormant = StatementRegex(statementPattern, true);
            Regex active = StatementRegex(statementPattern, false);
            if (dormant.Matches(text).Count == 0
                && active.Matches(text).Count == 1)
                return data;
            if (dormant.Matches(text).Count != 1
                || active.Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Instruction Burma 2 commentee absente ou ambigue.");
            return ansi.GetBytes(dormant.Replace(text, "$1$2$3", 1));
        }

        private static byte[] ActivateAlliedWaiting(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = new Regex(
                @"(?m)^[ \t]*HUMAN_Suspend\s*\(\s*true\s*\)\s*;[ \t]*\r?$"
                + @"\n^[ \t]*GoTo[ \t]+end\s*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
            if (active.Matches(text).Count == 1) return data;

            Regex dormant = new Regex(
                @"(?m)^(?<i>[ \t]*)//[ \t]*(?<a>HUMAN_Suspend\s*"
                + @"\(\s*true\s*\)\s*;)[ \t]*(?<r1>\r?)$\n"
                + @"^\k<i>//[ \t]*(?<b>GoTo[ \t]+end\s*;)[ \t]*(?<r2>\r?)$",
                RegexOptions.IgnoreCase);
            Match match = dormant.Match(text);
            if (!match.Success || dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Sequence d'attente du soldat panique absente ou ambigue.");
            string replacement = match.Groups["i"].Value
                + match.Groups["a"].Value + match.Groups["r1"].Value + "\n"
                + match.Groups["i"].Value + match.Groups["b"].Value
                + match.Groups["r2"].Value;
            text = text.Substring(0, match.Index) + replacement
                + text.Substring(match.Index + match.Length);
            return ansi.GetBytes(text);
        }

        private static byte[] ActivateExplosion(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = ActivateToCount(text,
                @"PlaySound\s*\(\s*6\s*,\s*8\s*\)\s*;", 1, 1);
            text = ActivateToCount(text,
                @"PlaySound\s*\(\s*6\s*,\s*2\s*\)\s*;", 2, 0);
            text = ActivateToCount(text,
                @"FRM_CreateParticle\s*\(\s*48\s*,\s*me\s*\)\s*;", 2, 0);
            text = ActivateToCount(text,
                @"MakeExplosion\s*\(\s*xplo22\s*,\s*50000\s*,\s*8000\s*\)\s*;",
                2, 0);
            text = ActivateToCount(text,
                @"MakeExplosion\s*\(\s*xplo22\s*,\s*1\s*,\s*15000\s*\)\s*;",
                1, 0);
            return ansi.GetBytes(text);
        }

        private static string ActivateToCount(
            string text, string statementPattern,
            int wantedActive, int wantedDormant)
        {
            Regex active = StatementRegex(statementPattern, false);
            Regex dormant = StatementRegex(statementPattern, true);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == wantedActive && dormantCount == wantedDormant)
                return text;
            int needed = wantedActive - activeCount;
            if (needed < 1 || dormantCount - needed != wantedDormant)
                throw new InvalidDataException(
                    "Branche d'explosion Burma 2 absente ou ambigue.");
            return dormant.Replace(text, "$1$2$3", needed);
        }

        private static Regex StatementRegex(string statementPattern, bool dormant)
        {
            string prefix = dormant
                ? @"([ \t]*)//[ \t]*(" : @"[ \t]*";
            string suffix = dormant ? @")([ \t]*\r?)" : @"[ \t]*\r?";
            return new Regex(
                @"(?m)^" + prefix + statementPattern + suffix + @"$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(string relative, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (relative.EndsWith("BU2_22.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                string attack =
                    @"HUMAN_Attack\s*\(\s*shoot01\s*,\s*2000\s*\)\s*;";
                RequireCounts(text, attack, 1, 0,
                    "Tir du garde du bunker Burma 2 incomplet.");
                Require(text,
                    @"Whenever[ \t]+shoot\s*\(\s*_SignalReceived\s*\(\s*2\s*\)"
                    + @"\s*\)[\s\S]{0,220}HUMAN_SETMODE_Stand\s*\(\s*\)"
                    + @"[\s\S]{0,100}" + attack
                    + @"[\s\S]{0,140}SetAlarmType\s*\(\s*35\s*,\s*true\s*\)",
                    "Reaction complete du garde du bunker Burma 2 absente.");
                return;
            }
            if (relative.EndsWith("BU2_Allied11.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                Require(text,
                    @"FRM_SwitchFaceTexture\s*\(\s*me\s*,\s*""e_f054""\s*\)"
                    + @"[\s\S]{0,100}HUMAN_Suspend\s*\(\s*true\s*\)"
                    + @"[\s\S]{0,70}GoTo[ \t]+end\s*;"
                    + @"[\s\S]{0,80}Label[ \t]+panika\s*:",
                    "Attente initiale du soldat panique Burma 2 incomplete.");
                RequireCounts(text,
                    @"HUMAN_Suspend\s*\(\s*true\s*\)\s*;", 1, 0,
                    "Suspension du soldat panique Burma 2 incomplete.");
                Require(text,
                    @"Whenever[ \t]+player\s*\(\s*_PlayerInRange\s*\(\s*40\s*\)"
                    + @"\s*\)[\s\S]{0,220}HUMAN_Suspend\s*\(\s*false\s*\)"
                    + @"[\s\S]{0,180}HUMAN_SetAnim\s*\(\s*""%%panika1""",
                    "Reveil du soldat panique Burma 2 absent.");
                return;
            }
            if (relative.EndsWith("BU2_xplo22.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                RequireCounts(text,
                    @"PlaySound\s*\(\s*6\s*,\s*8\s*\)\s*;", 1, 1,
                    "Son initial de l'explosion 22 incorrect.");
                RequireCounts(text,
                    @"PlaySound\s*\(\s*6\s*,\s*2\s*\)\s*;", 2, 0,
                    "Son principal de l'explosion 22 incomplet.");
                RequireCounts(text,
                    @"FRM_CreateParticle\s*\(\s*48\s*,\s*me\s*\)\s*;", 2, 0,
                    "Particules de l'explosion 22 incompletes.");
                RequireCounts(text,
                    @"MakeExplosion\s*\(\s*xplo22\s*,\s*50000\s*,\s*8000\s*\)\s*;",
                    2, 0, "Degats de l'explosion 22 incomplets.");
                RequireCounts(text,
                    @"MakeExplosion\s*\(\s*xplo22\s*,\s*1\s*,\s*15000\s*\)\s*;",
                    1, 0, "Souffle direct de l'explosion 22 incomplet.");
                Require(text,
                    @"Whenever[ \t]+player\s*\(\s*_PlayerInRange\s*\(\s*8\s*\)"
                    + @"\s*\)[\s\S]{0,700}?^[ \t]*PlaySound\s*\(\s*6\s*,\s*8\s*\)"
                    + @"[\s\S]{0,600}?MakeExplosion\s*\(\s*xplo22\s*,\s*1\s*,\s*15000\s*\)",
                    "Branche joueur de l'explosion 22 incomplete.");
                Require(text,
                    @"Label[ \t]+xplo\s*:[\s\S]{0,100}?^[ \t]*//[ \t]*"
                    + @"PlaySound\s*\(\s*6\s*,\s*8\s*\)\s*;"
                    + @"[\s\S]{0,500}?MakeExplosion\s*\(\s*xplo22\s*,\s*50000\s*,\s*8000\s*\)",
                    "Branche allies de l'explosion 22 incomplete.");
                return;
            }
            throw new InvalidDataException(
                "Script Burma 2 non pris en charge : " + relative);
        }

        private static void RequireCounts(
            string text, string statementPattern,
            int activeCount, int dormantCount, string message)
        {
            if (StatementRegex(statementPattern, false).Matches(text).Count
                    != activeCount
                || StatementRegex(statementPattern, true).Matches(text).Count
                    != dormantCount)
                throw new InvalidDataException(message);
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            foreach (string[] binding in new[] {
                new[] { "BU2_22", "BU2_22.scr" },
                new[] { "BU2_22_A2", "BU2_22_A2.scr" },
                new[] { "BU2_Allied11", "BU2_Allied11.scr" },
                new[] { "vybuch_22", "BU2_xplo22.scr" },
                new[] { "vybuch_23", "BU2_xplo23.scr" }
            })
                if (!HasBinding(registry, binding[0], binding[1]))
                    throw new InvalidDataException(
                        "Liaison Burma 2 absente : " + binding[0] + ".");

            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            foreach (string actor in new[] { "BU2_22", "BU2_Allied11" })
                if (CountTypedString(actors, actor) != 1)
                    throw new InvalidDataException(
                        "Acteur Burma 2 absent ou ambigu : " + actor + ".");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, ScenePath, MissionArchives));
            foreach (string frame in new[] { "BU2_22_A2", "BU2_22_shoot01" })
                if (CountAscii(scene, frame) != 1)
                    throw new InvalidDataException(
                        "Cadre Burma 2 absent ou ambigu : " + frame + ".");

            byte[] model = ReadSource(ResolveSource(
                gamePath, ModelPath, MissionArchives));
            foreach (string frame in new[] { "x_vybuch_22", "x_vybuch_23" })
                if (CountAscii(model, frame) != 1)
                    throw new InvalidDataException(
                        "Effet Burma 2 absent ou ambigu : " + frame + ".");

            string activator = ReadText(ResolveSource(gamePath,
                "Scripts/BURMA2/BU2_22_A2.scr", ScriptArchives));
            Require(activator,
                @"Whenever[ \t]+player\s*\(\s*_PlayerInRange\s*\(\s*2\s*\)"
                + @"\s*\)[\s\S]{0,160}SendSignal\s*\(\s*bu2_22\s*,\s*2\s*\)",
                "Declencheur du tir du bunker Burma 2 absent.");

            string attackReference = ReadText(ResolveSource(gamePath,
                "Scripts/BURMA2/BU2_Allied01.scr", ScriptArchives));
            Require(attackReference,
                @"HUMAN_Attack\s*\(\s*shoot01\s*,\s*2000\s*\)",
                "Commande de tir de reference Burma 2 absente.");

            string explosionReference = ReadText(ResolveSource(gamePath,
                "Scripts/BURMA2/BU2_xplo23.scr", ScriptArchives));
            Require(explosionReference,
                @"PlaySound\s*\(\s*6\s*,\s*8\s*\)"
                + @"[\s\S]{0,250}FRM_CreateParticle\s*\(\s*48\s*,\s*me\s*\)"
                + @"[\s\S]{0,220}MakeExplosion\s*\(\s*xplo23\s*,\s*50000\s*,\s*8000\s*\)"
                + @"[\s\S]{0,120}MakeExplosion\s*\(\s*xplo23\s*,\s*1\s*,\s*15000\s*\)",
                "Explosion jumelle 23 de reference absente.");
        }

        private static void Require(string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static string ReadText(DormantSource source)
        {
            return Encoding.GetEncoding(1252).GetString(ReadSource(source));
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

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Burma 2 trop court.");
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
                    "Registre de scripts Burma 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Burma 2.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Burma 2.");
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