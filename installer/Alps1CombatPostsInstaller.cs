using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Alps1CombatPostsInstaller
    {
        private static readonly string[] ScriptPaths = {
            "Scripts/ALPS1/ge_16.scr",
            "Scripts/ALPS1/ge_17.scr",
            "Scripts/ALPS1/ge_18.scr",
            "Scripts/ALPS1/ge_23.scr",
            "Scripts/ALPS1/ge_34.scr",
            "Scripts/ALPS1/ge_35.scr",
            "Scripts/ALPS1/ridiccasovac.scr"
        };

        private const string RegistryPath = "Missions/ALPS1/Scripts.dta";
        private const string ActorsPath = "Missions/ALPS1/actors.bin";
        private const string CheckpointsPath = "Missions/ALPS1/check2.bin";

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
                        "Le poste de combat Alps 1 semble deja actif dans "
                        + relative + ".");
                ValidatePatched(relative, patched);
                if (!BytesEqual(patched, PatchScript(relative, patched)))
                    throw new InvalidDataException(
                        "La restauration des postes Alps 1 n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Alps 1 verifie : postes, patrouille 18, tir du garde 34, "
                + "informateur 35 et consequence temporisee sont restaures.";
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
                "Restauration des postes de combat et consequences d'Alps 1...");
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
                "Alps 1 : " + changed + " scripts de combat et d'alarme restaures.");
            InstallerCore.Report(progress,
                "Postes, patrouille 18, tir 34, informateur et consequence restaures.");
        }

        private static byte[] PatchScript(string relative, byte[] data)
        {
            if (relative.EndsWith("ge_16.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantLines(data,
                    @"HUMAN_Move\s*\(\s*""ge16_sniper""\s*\)\s*;",
                    @"HUMAN_SetSniper\s*\(\s*1\s*,\s*1\s*\)\s*;");
            if (relative.EndsWith("ge_17.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantLines(data,
                    @"HUMAN_BoardVehicle\s*\(\s*""w_mg42Crouch_"""
                    + @"\s*,\s*1\s*,\s*0\s*\)\s*;");
            if (relative.EndsWith("ge_18.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantLines(data,
                    @"HUMAN_Move\s*\(\s*""ge18_01""\s*\)\s*;");
            if (relative.EndsWith("ge_23.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantLines(data,
                    @"HUMAN_BoardVehicle\s*\(\s*""w_mg42Crouch_3"""
                    + @"\s*,\s*1\s*,\s*0\s*\)\s*;");
            if (relative.EndsWith("ge_34.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantLines(data,
                    @"HUMAN_Attack\s*\(\s*atak\s*,\s*5000\s*\)\s*;");
            if (relative.EndsWith("ge_35.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantLines(data,
                    @"HUMAN_Suspend\s*\(\s*0\s*\)\s*;");
            if (relative.EndsWith("ridiccasovac.scr",
                StringComparison.OrdinalIgnoreCase))
                return ActivateDormantLines(data,
                    @"SendSignal\s*\(\s*obj\s*,\s*18\s*\)\s*;");
            throw new InvalidDataException(
                "Script Alps 1 non pris en charge : " + relative);
        }

        private static byte[] ActivateDormantLines(
            byte[] data, params string[] statementPatterns)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            foreach (string statementPattern in statementPatterns)
            {
                Regex dormant = StatementRegex(statementPattern, true);
                Regex active = StatementRegex(statementPattern, false);
                int dormantCount = dormant.Matches(text).Count;
                int activeCount = active.Matches(text).Count;
                if (dormantCount == 0 && activeCount == 1) continue;
                if (dormantCount != 1 || activeCount != 0)
                    throw new InvalidDataException(
                        "Poste de combat commente absent ou ambigu.");
                text = dormant.Replace(text, "$1$2$3", 1);
            }
            return ansi.GetBytes(text);
        }

        private static Regex StatementRegex(string statementPattern, bool dormant)
        {
            string prefix = dormant
                ? @"([ \t]*)//[ \t]*(" : @"[ \t]*";
            string suffix = dormant ? @")(\r?)" : @"\r?";
            return new Regex(
                @"(?m)^" + prefix + statementPattern + @"[ \t]*"
                + suffix + @"$", RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(string relative, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (relative.EndsWith("ge_16.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                RequireActive(text,
                    @"HUMAN_Move\s*\(\s*""ge16_sniper""\s*\)\s*;");
                RequireActive(text,
                    @"HUMAN_SetSniper\s*\(\s*1\s*,\s*1\s*\)\s*;");
                Require(text,
                    @"OnAlarm\s*\(\s*\)[\s\S]{0,1000}"
                    + @"HUMAN_Move\s*\(\s*""ge16_sniper""\s*\)"
                    + @"[\s\S]{0,80}HUMAN_SetSniper\s*\(\s*1\s*,\s*1\s*\)",
                    "Poste de precision du garde 16 incomplet.");
                return;
            }
            if (relative.EndsWith("ge_17.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                string board = @"HUMAN_BoardVehicle\s*\(\s*""w_mg42Crouch_"""
                    + @"\s*,\s*1\s*,\s*0\s*\)\s*;";
                RequireActive(text, board);
                Require(text,
                    @"OnAlarm\s*\(\s*\)[\s\S]{0,900}"
                    + @"HUMAN_Move\s*\(\s*""ge17_01""\s*\)"
                    + @"[\s\S]{0,80}" + board,
                    "Poste MG42 du garde 17 incomplet.");
                return;
            }
            if (relative.EndsWith("ge_18.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                string first = @"HUMAN_Move\s*\(\s*""ge18_01""\s*\)\s*;";
                RequireActive(text, first);
                Require(text,
                    @"label\s+chod\s*:[\s\S]{0,120}" + first
                    + @"[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge18_02""\s*\)"
                    + @"[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge18_03""\s*\)"
                    + @"[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge18_04""\s*\)"
                    + @"[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge18_05""\s*\)"
                    + @"[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge18_04""\s*\)"
                    + @"[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge18_03""\s*\)"
                    + @"[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge18_02""\s*\)"
                    + @"[\s\S]{0,80}goto\s+chod\s*;",
                    "Boucle de patrouille du garde 18 incomplete.");
                return;
            }
            if (relative.EndsWith("ge_23.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                string board = @"HUMAN_BoardVehicle\s*\(\s*""w_mg42Crouch_3"""
                    + @"\s*,\s*1\s*,\s*0\s*\)\s*;";
                RequireActive(text, board);
                Require(text,
                    @"OnAlarm\s*\(\s*\)[\s\S]{0,900}"
                    + @"HUMAN_Move\s*\(\s*""ge23_01""\s*\)"
                    + @"[\s\S]{0,80}" + board,
                    "Poste MG42 du garde 23 incomplet.");
                return;
            }
            if (relative.EndsWith("ge_34.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                string attack =
                    @"HUMAN_Attack\s*\(\s*atak\s*,\s*5000\s*\)\s*;";
                RequireActive(text, attack);
                Require(text,
                    @"if\s*\(\s*aievent\s*==\s*32\s*\)[\s\S]{0,300}"
                    + @"SendSignal\s*\(\s*ge33\s*,\s*3\s*\)"
                    + @"[\s\S]{0,160}HUMAN_WeaponOnArm\s*\(\s*1\s*\)"
                    + @"[\s\S]{0,160}HUMAN_TurnAtNearestPlayer\s*\(\s*\)"
                    + @"[\s\S]{0,100}" + attack
                    + @"[\s\S]{0,100}EndScript\s*\(",
                    "Reaction de tir du garde 34 incomplete.");
                return;
            }
            if (relative.EndsWith("ge_35.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                string wake = @"HUMAN_Suspend\s*\(\s*0\s*\)\s*;";
                RequireActive(text, wake);
                Require(text,
                    @"Whenever\s+bez\s*\(\s*_SignalReceived\s*\(\s*1\s*\)"
                    + @"\s*\)[\s\S]{0,160}" + wake
                    + @"[\s\S]{0,160}HUMAN_SETEVENTS\s*\(\s*1\s*\)",
                    "Reveil de l'informateur 35 incomplet.");
                Require(text,
                    @"OnAlarm\s*\(\s*\)[\s\S]{0,1800}CSC_RunCutscene\s*\(",
                    "Consequence d'alarme de l'informateur 35 absente.");
                return;
            }
            if (relative.EndsWith("ridiccasovac.scr",
                StringComparison.OrdinalIgnoreCase))
            {
                string consequence =
                    @"SendSignal\s*\(\s*obj\s*,\s*18\s*\)\s*;";
                RequireActive(text, consequence);
                Require(text,
                    @"if\s*\(\s*a\s*==\s*2\s*\)[\s\S]{0,500}"
                    + @"delay\s*\(\s*60000\s*\)[\s\S]{0,160}"
                    + @"SendSignal\s*\(\s*ge38\s*,\s*1\s*\)"
                    + @"[\s\S]{0,100}SendSignal\s*\(\s*ge39\s*,\s*1\s*\)"
                    + @"[\s\S]{0,100}delay\s*\(\s*30000\s*\)"
                    + @"[\s\S]{0,100}" + consequence,
                    "Chaine temporisee des renforts Alps 1 incomplete.");
                return;
            }
            throw new InvalidDataException(
                "Script Alps 1 non pris en charge : " + relative);
        }

        private static void RequireActive(string text, string statementPattern)
        {
            if (StatementRegex(statementPattern, false).Matches(text).Count != 1
                || StatementRegex(statementPattern, true).Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Ligne de poste de combat restauree incomplete.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            foreach (string[] binding in new[] {
                new[] { "ge_16", "ge_16.scr" },
                new[] { "ge_17", "ge_17.scr" },
                new[] { "ge_18", "ge_18.scr" },
                new[] { "ge_23", "ge_23.scr" },
                new[] { "ge_34", "ge_34.scr" },
                new[] { "ge_35", "ge_35.scr" },
                new[] { "ridiccasovac", "ridiccasovac.scr" },
                new[] { "setobjectyves", "setobjectives.scr" }
            })
                if (!HasBinding(registry, binding[0], binding[1]))
                    throw new InvalidDataException(
                        "Liaison Alps 1 absente : " + binding[0] + ".");

            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            foreach (string actor in new[] {
                "ge_16", "ge_17", "ge_18", "ge_23", "ge_34", "ge34attack",
                "ge_35", "ge_38", "ge_39",
                "w_mg42Crouch_", "w_mg42Crouch_3"
            })
                if (CountTypedString(actors, actor) < 1)
                    throw new InvalidDataException(
                        "Acteur ou MG42 Alps 1 absent : " + actor + ".");

            byte[] checkpoints = ReadSource(ResolveSource(
                gamePath, CheckpointsPath, MissionArchives));
            foreach (string checkpoint in new[] {
                "ge16_sniper", "ge17_01",
                "ge18_01", "ge18_02", "ge18_03", "ge18_04", "ge18_05",
                "ge23_01", "ge38_01", "ge38_02", "ge39_01", "ge39_02"
            })
                if (CountAscii(checkpoints, checkpoint) != 1)
                    throw new InvalidDataException(
                        "Point Alps 1 absent ou ambigu : " + checkpoint + ".");

            string sniperReference = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/ge_28.scr", ScriptArchives));
            Require(sniperReference,
                @"HUMAN_SetSniper\s*\(\s*1\s*,\s*1\s*\)",
                "Commande de precision de reference Alps 1 absente.");

            string mgReference = ReadText(ResolveSource(gamePath,
                "Scripts/AFRICA2/AF2_15.scr", ScriptArchives));
            Require(mgReference,
                @"HUMAN_BoardVehicle\s*\(\s*""w_mg42Crouch_01"""
                + @"\s*,\s*true\s*,\s*0\s*\)",
                "Commande MG42 de reference commerciale absente.");

            string attackReference = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS2/AL2_10.scr", ScriptArchives));
            Require(attackReference,
                @"HUMAN_Attack\s*\(\s*target\s*,\s*4000\s*\)",
                "Commande d'attaque de reference Alps 2 absente.");

            string forgeDetector = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/detector_forge30.scr", ScriptArchives));
            Require(forgeDetector,
                @"SendSignal\s*\(\s*ge35\s*,\s*1\s*\)",
                "Signal d'activation de l'informateur 35 absent.");

            string selector = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/setobjectives.scr", ScriptArchives));
            Require(selector,
                @"ScriptAssign\s*\(\s*obj\s*,\s*""objectyves\.scr""\s*\)",
                "Affectation du controleur d'objectifs Alps 1 absente.");

            string objectives = ReadText(ResolveSource(gamePath,
                "Scripts/ALPS1/objectyves.scr", ScriptArchives));
            Require(objectives,
                @"Whenever\s+dlouho\s*\(\s*_SignalReceived\s*\(\s*18\s*\)"
                + @"\s*\)[\s\S]{0,300}SUBTITLES_SetText\s*\(\s*14992813\s*\)"
                + @"[\s\S]{0,180}SetObjectiveStatus\s*\(\s*1\s*,\s*3\s*\)",
                "Consequence du signal 18 Alps 1 absente.");

            foreach (string reinforcement in new[] { "ge_38", "ge_39" })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/ALPS1/" + reinforcement + ".scr", ScriptArchives));
                Require(script,
                    @"Whenever\s+bez\s*\(\s*_SignalReceived\s*\(\s*1\s*\)"
                    + @"\s*\)[\s\S]{0,180}HUMAN_Suspend\s*\(\s*0\s*\)",
                    "Activation du renfort Alps 1 absente : " + reinforcement);
            }
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
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
                    "Registre de scripts Alps 1 trop court.");
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
                    "Registre de scripts Alps 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Alps 1.");
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