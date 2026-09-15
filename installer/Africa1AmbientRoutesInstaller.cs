using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa1AmbientRoutesInstaller
    {
        private const string MechanicPath = "Scripts/AFRICA1/AF1_16.scr";
        private const string PatrolPath = "Scripts/AFRICA1/AF1_19.scr";
        private const string RegistryPath = "Missions/AFRICA1/Scripts.dta";
        private const string CheckpointsPath = "Missions/AFRICA1/check2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] mechanic = ReadSource(ResolveSource(
                gamePath, MechanicPath, ScriptArchives));
            byte[] patrol = ReadSource(ResolveSource(
                gamePath, PatrolPath, ScriptArchives));
            byte[] patchedMechanic = PatchMechanic(mechanic);
            byte[] patchedPatrol = PatchPatrol(patrol);
            if (BytesEqual(mechanic, patchedMechanic)
                || BytesEqual(patrol, patchedPatrol))
                throw new InvalidDataException(
                    "Une sequence ambiante d'Africa 1 semble deja restauree.");
            ValidateMechanic(patchedMechanic);
            ValidatePatrol(patchedPatrol);
            if (!BytesEqual(patchedMechanic, PatchMechanic(patchedMechanic))
                || !BytesEqual(patchedPatrol, PatchPatrol(patchedPatrol)))
                throw new InvalidDataException(
                    "La restauration des trajets Africa 1 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 1 verifie : le mecanicien 16 rejoint son avion et le garde 19 retrouve sa ronde complete apres alerte.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string mechanic = InstallerCore.SafeGameTarget(
                    gamePath, MechanicPath);
                string patrol = InstallerCore.SafeGameTarget(
                    gamePath, PatrolPath);
                if (!File.Exists(mechanic) || !File.Exists(patrol)) return false;
                ValidateMechanic(File.ReadAllBytes(mechanic));
                ValidatePatrol(File.ReadAllBytes(patrol));
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
                "Restauration de deux trajets ambiants dans Africa 1...");
            ValidateAssets(gamePath);
            bool changed = false;
            changed |= InstallOne(gamePath, MechanicPath, journal, prepared,
                PatchMechanic, ValidateMechanic);
            changed |= InstallOne(gamePath, PatrolPath, journal, prepared,
                PatchPatrol, ValidatePatrol);
            if (!changed)
            {
                InstallerCore.Report(progress,
                    "Les deux trajets ambiants d'Africa 1 sont deja actifs.");
                return;
            }
            InstallerCore.Log(
                "Africa 1 : trajet du mecanicien 16 et ronde du garde 19 restaures.");
            InstallerCore.Report(progress,
                "Le mecanicien 16 et le garde 19 retrouvent leurs trajets officiels.");
        }

        private static bool InstallOne(
            string gamePath, string relative, StateJournal journal,
            HashSet<string> prepared, Func<byte[], byte[]> patch,
            Action<byte[]> validate)
        {
            DormantSource source = ResolveSource(
                gamePath, relative, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = patch(original);
            validate(patched);
            if (BytesEqual(original, patched)) return false;

            InstallerCore.PrepareTarget(
                gamePath, relative, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            return true;
        }

        private static byte[] PatchMechanic(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsMechanicPatched(text))
            {
                ValidateMechanic(data);
                return data;
            }
            Regex dormant = new Regex(
                @"(?m)^(?<one>[ \t]*)//[ \t]*HUMAN_Move\s*\(\s*""af1_16_06""\s*\)\s*;[ \t]*\r?\n"
                + @"(?<two>[ \t]*)//[ \t]*HUMAN_TurnAt\s*\(\s*airplane\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Mise en place dormante d'AF1_16 introuvable.");
            text = dormant.Replace(text, match =>
                match.Groups["one"].Value + "HUMAN_Move(\"af1_16_06\");"
                + Environment.NewLine + match.Groups["two"].Value
                + "HUMAN_TurnAt(airplane);", 1);
            return ansi.GetBytes(text);
        }

        private static byte[] PatchPatrol(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatrolPatched(text))
            {
                ValidatePatrol(data);
                return data;
            }
            string[] patterns = {
                @"(?m)^(?<i>[ \t]*)//[ \t]*Label[ \t]+LOOP[ \t]*:[ \t]*(?=\r?$)",
                @"(?m)^(?<i>[ \t]*)//[ \t]*HUMAN_Move\s*\(\s*""AF1_18_02""\s*\)\s*;[ \t]*(?=\r?$)",
                @"(?m)^(?<i>[ \t]*)//[ \t]*HUMAN_Move\s*\(\s*""AF1_19_01""\s*\)\s*;[ \t]*(?=\r?$)",
                @"(?m)^(?<i>[ \t]*)//[ \t]*HUMAN_Move\s*\(\s*""AF1_19_02""\s*\)\s*;[ \t]*(?=\r?$)",
                @"(?m)^(?<i>[ \t]*)//[ \t]*HUMAN_Move\s*\(\s*""AF1_18_03""\s*\)\s*;[ \t]*(?=\r?$)",
                @"(?m)^(?<i>[ \t]*)//[ \t]*goto[ \t]+LOOP\s*;[ \t]*(?=\r?$)"
            };
            string[] replacements = {
                "Label LOOP:",
                "HUMAN_Move(\"AF1_18_02\");",
                "HUMAN_Move(\"AF1_19_01\");",
                "HUMAN_Move(\"AF1_19_02\");",
                "HUMAN_Move(\"AF1_18_03\");",
                "goto LOOP;"
            };
            for (int index = 0; index < patterns.Length; index++)
            {
                Regex dormant = new Regex(patterns[index], RegexOptions.IgnoreCase);
                if (dormant.Matches(text).Count != 1)
                    throw new InvalidDataException(
                        "Etape dormante " + (index + 1)
                        + " de la ronde AF1_19 introuvable.");
                string replacement = replacements[index];
                text = dormant.Replace(text, match =>
                    match.Groups["i"].Value + replacement, 1);
            }
            return ansi.GetBytes(text);
        }

        private static bool IsMechanicPatched(string text)
        {
            return Regex.IsMatch(text,
                @"(?m)^[ \t]*HUMAN_Move\s*\(\s*""af1_16_06""\s*\)\s*;[ \t]*\r?\n"
                + @"[ \t]*HUMAN_TurnAt\s*\(\s*airplane\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase);
        }

        private static bool IsPatrolPatched(string text)
        {
            return Regex.IsMatch(text,
                @"OnAlarmDone\s*\(\s*\)\s*\{[\s\S]{0,500}"
                + @"Label[ \t]+LOOP\s*:[\s\S]{0,100}"
                + @"HUMAN_Move\s*\(\s*""AF1_18_02""\s*\)\s*;[\s\S]{0,100}"
                + @"HUMAN_Move\s*\(\s*""AF1_19_01""\s*\)\s*;[\s\S]{0,100}"
                + @"HUMAN_Move\s*\(\s*""AF1_19_02""\s*\)\s*;[\s\S]{0,100}"
                + @"HUMAN_Move\s*\(\s*""AF1_18_03""\s*\)\s*;[\s\S]{0,100}"
                + @"goto[ \t]+LOOP\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidateMechanic(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Require(text,
                @"HUMAN_SETMODE_Guard\s*\(\s*\)\s*;[\s\S]{0,180}"
                + @"HUMAN_Move\s*\(\s*""af1_16_06""\s*\)\s*;[\s\S]{0,80}"
                + @"HUMAN_TurnAt\s*\(\s*airplane\s*\)\s*;[\s\S]{0,120}"
                + @"Label[ \t]+BEFORE\s*:",
                "La mise en place du mecanicien AF1_16 est incomplete.");
        }

        private static void ValidatePatrol(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsPatrolPatched(text))
                throw new InvalidDataException(
                    "La ronde restauree d'AF1_19 est incomplete.");
            Require(text,
                @"OnAlarmDone\s*\(\s*\)\s*\{[\s\S]{0,220}"
                + @"HUMAN_SETMODE_Walk\s*\(\s*\)\s*;",
                "Le retour d'alarme officiel d'AF1_19 a ete altere.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "AF1_16", "AF1_16.scr")
                || !HasBinding(registry, "AF1_19", "AF1_19.scr"))
                throw new InvalidDataException(
                    "Liaisons officielles AF1_16/AF1_19 absentes.");

            string checkpoints = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(
                    gamePath, CheckpointsPath, MissionArchives)));
            foreach (string checkpoint in new[] {
                "af1_16_06", "AF1_18_02", "AF1_19_01",
                "AF1_19_02", "AF1_18_03"
            })
                if (checkpoints.IndexOf(
                    checkpoint, StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Checkpoint Africa 1 absent : " + checkpoint + ".");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 1 trop court.");
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
                    "Registre de scripts Africa 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 1.");
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