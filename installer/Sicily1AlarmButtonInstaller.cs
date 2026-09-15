using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Sicily1AlarmButtonInstaller
    {
        private sealed class AlarmSpec
        {
            public string Actor;
            public string Script;
            public string Cylinder;
        }

        private sealed class MissionSpec
        {
            public string Folder;
            public string RegistryPath;
            public string CheckpointsPath;
        }

        private static readonly AlarmSpec[] Alarms = {
            new AlarmSpec {
                Actor = "M_ALAR_", Script = "Sic1_alarm_buton1.scr",
                Cylinder = "M_ALAR_.Cylinder01"
            },
            new AlarmSpec {
                Actor = "M_ALAR_2", Script = "Sic1_alarm_buton2.scr",
                Cylinder = "M_ALAR_2.Cylinder01"
            },
            new AlarmSpec {
                Actor = "M_ALAR_3", Script = "Sic1_alarm_buton3.scr",
                Cylinder = "M_ALAR_3.Cylinder01"
            },
            new AlarmSpec {
                Actor = "M_ALAR_4", Script = "Sic1_alarm_buton4.scr",
                Cylinder = "M_ALAR_4.Cylinder01"
            },
            new AlarmSpec {
                Actor = "M_ALAR_6", Script = "Sic1_alarm_buton5.scr",
                Cylinder = "M_ALAR_6.Cylinder01"
            },
            new AlarmSpec {
                Actor = "M_ALAR_5", Script = "Sic1_alarm_buton6.scr",
                Cylinder = "M_ALAR_5.Cylinder01"
            }
        };

        private static readonly MissionSpec[] Missions = {
            new MissionSpec {
                Folder = "Sicily1",
                RegistryPath = "Missions/Sicily1/Scripts.dta",
                CheckpointsPath = "Missions/Sicily1/check2.bin"
            },
            new MissionSpec {
                Folder = "Co_Sicily1",
                RegistryPath = "Missions/Co_Sicily1/MpScripts.dta",
                CheckpointsPath = "Missions/Co_Sicily1/check2.bin"
            }
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] ModelArchives = {
            "models.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            int changed = 0;
            foreach (MissionSpec mission in Missions)
                foreach (AlarmSpec alarm in Alarms)
                {
                    string relative = ScriptPath(mission, alarm);
                    byte[] original = ReadSource(ResolveSource(
                        gamePath, relative, ScriptArchives));
                    byte[] patched = PatchScript(alarm, original);
                    if (!BytesEqual(original, patched)) changed++;
                    ValidatePatched(mission, alarm, patched);
                    if (!BytesEqual(patched, PatchScript(alarm, patched)))
                        throw new InvalidDataException(
                            "La restauration des boutons Sicily 1 n'est pas idempotente.");
                }
            if (changed != Missions.Length * Alarms.Length)
                throw new InvalidDataException(
                    "Les douze scripts Sicily 1 ne presentent pas tous le vestige attendu.");
            ValidateAssets(gamePath);
            return "Sicily 1 verifie : les six boutons d'alarme retrouvent "
                + "leur animation officielle en solo et en cooperation.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (MissionSpec mission in Missions)
                    foreach (AlarmSpec alarm in Alarms)
                    {
                        string relative = ScriptPath(mission, alarm);
                        string target = InstallerCore.SafeGameTarget(
                            gamePath, relative);
                        if (!File.Exists(target)) return false;
                        ValidatePatched(
                            mission, alarm, File.ReadAllBytes(target));
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
                "Restauration des boutons d'alarme de Sicily 1...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (MissionSpec mission in Missions)
                foreach (AlarmSpec alarm in Alarms)
                {
                    string relative = ScriptPath(mission, alarm);
                    DormantSource source = ResolveSource(
                        gamePath, relative, ScriptArchives);
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, relative);
                    byte[] original = File.Exists(target)
                        ? File.ReadAllBytes(target) : ReadSource(source);
                    byte[] patched = PatchScript(alarm, original);
                    ValidatePatched(mission, alarm, patched);
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

            InstallerCore.Log("Sicily 1 : animation visuelle restauree dans "
                + changed + " scripts d'alarme.");
            InstallerCore.Report(progress,
                "Les six boutons d'alarme de Sicily 1 sont de nouveau animes "
                + "en solo et en cooperation.");
        }

        private static byte[] PatchScript(AlarmSpec alarm, byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (HasCompleteActiveSequence(text, alarm.Cylinder))
            {
                ValidateActiveCounts(text, alarm);
                return data;
            }

            Regex declaration = DormantDeclarationRegex(alarm.Cylinder);
            Regex toggle = DormantToggleRegex();
            if (declaration.Matches(text).Count != 1
                || toggle.Matches(text).Count != 4)
                throw new InvalidDataException(
                    "Animation commentee absente ou ambigue dans " + alarm.Script + ".");

            text = declaration.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            });
            text = toggle.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            });
            return ansi.GetBytes(text);
        }

        private static Regex DormantDeclarationRegex(string cylinder)
        {
            return new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>Frame[ \t]+hide;"
                + @"[ \t]*FRM_FindFrame\s*\(\s*hide\s*,\s*"""
                + Regex.Escape(cylinder)
                + @"""\s*\);)[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static Regex DormantToggleRegex()
        {
            return new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>FRM_SetOn\s*"
                + @"\(\s*hide\s*,\s*(?:True|False)\s*\);)[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static bool HasCompleteActiveSequence(
            string text, string cylinder)
        {
            return ActiveDeclarationRegex(cylinder).Matches(text).Count == 1
                && ActiveToggleRegex(true).Matches(text).Count == 2
                && ActiveToggleRegex(false).Matches(text).Count == 2;
        }

        private static Regex ActiveDeclarationRegex(string cylinder)
        {
            return new Regex(
                @"(?m)^[ \t]*Frame[ \t]+hide;[ \t]*FRM_FindFrame\s*"
                + @"\(\s*hide\s*,\s*""" + Regex.Escape(cylinder)
                + @"""\s*\);[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static Regex ActiveToggleRegex(bool state)
        {
            return new Regex(
                @"(?m)^[ \t]*FRM_SetOn\s*\(\s*hide\s*,\s*"
                + (state ? "True" : "False")
                + @"\s*\);[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(
            MissionSpec mission, AlarmSpec alarm, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            ValidateActiveCounts(text, alarm);
            if (DormantDeclarationRegex(alarm.Cylinder).Matches(text).Count != 0
                || DormantToggleRegex().Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Des lignes visuelles Sicily 1 sont encore desactivees dans "
                    + alarm.Script + ".");
            if (!Regex.IsMatch(text,
                    @"OnUse\s*\(\s*\)", RegexOptions.IgnoreCase)
                || !Regex.IsMatch(text,
                    @"OnSignal\s*\(\s*1\s*\)", RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "La logique d'alarme a ete alteree dans " + alarm.Script + ".");

            int savedAlarm = Regex.Matches(text,
                @"SaveGameValue\s*\(\s*61\s*,\s*1\s*\)",
                RegexOptions.IgnoreCase).Count;
            int expected = String.Equals(
                mission.Folder, "Sicily1",
                StringComparison.OrdinalIgnoreCase) ? 1 : 0;
            if (savedAlarm != expected)
                throw new InvalidDataException(
                    "L'etat global de l'alarme a ete altere dans " + alarm.Script + ".");
        }

        private static void ValidateActiveCounts(
            string text, AlarmSpec alarm)
        {
            if (!HasCompleteActiveSequence(text, alarm.Cylinder))
                throw new InvalidDataException(
                    "Animation restauree incomplete dans " + alarm.Script + ".");
            if (Regex.Matches(text, @"(?m)^[ \t]*hidden\s*=",
                    RegexOptions.IgnoreCase).Count != 3
                || Regex.Matches(text,
                    @"integer[ \t]+hidden\s*=\s*0\s*;",
                    RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(
                    "Etat du bouton altere dans " + alarm.Script + ".");
        }

        private static void ValidateAssets(string gamePath)
        {
            foreach (MissionSpec mission in Missions)
            {
                byte[] registry = ReadSource(ResolveSource(
                    gamePath, mission.RegistryPath, MissionArchives));
                byte[] checkpoints = ReadSource(ResolveSource(
                    gamePath, mission.CheckpointsPath, MissionArchives));
                foreach (AlarmSpec alarm in Alarms)
                {
                    if (!HasBinding(registry, alarm.Actor, alarm.Script))
                        throw new InvalidDataException(
                            "Liaison Sicily 1 absente : " + alarm.Actor
                            + " -> " + alarm.Script + ".");
                    if (CountNullTerminated(checkpoints, alarm.Actor) != 1)
                        throw new InvalidDataException(
                            "Bouton Sicily 1 absent ou ambigu : "
                            + alarm.Actor + ".");
                }
            }

            byte[] model = ReadSource(ResolveSource(
                gamePath, "Models/M_ALAR01.4ds", ModelArchives));
            if (CountNullTerminated(model, "Cylinder01") != 1)
                throw new InvalidDataException(
                    "Le bouton Cylinder01 est absent du modele M_ALAR01.");

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/ARCTIC2/R_Arc1B_AlarmButon.scr",
                    ScriptArchives)));
            if (ActiveDeclarationRegex(
                    "m_alarm_.Cylinder01").Matches(reference).Count != 1
                || ActiveToggleRegex(true).Matches(reference).Count != 2
                || ActiveToggleRegex(false).Matches(reference).Count != 2)
                throw new InvalidDataException(
                    "Le mecanisme officiel de reference des boutons est absent.");
        }

        private static string ScriptPath(
            MissionSpec mission, AlarmSpec alarm)
        {
            return "Scripts/" + mission.Folder + "/" + alarm.Script;
        }

        private static int CountNullTerminated(byte[] data, string value)
        {
            byte[] needle = Encoding.GetEncoding(1252).GetBytes(value + "\0");
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
                    "Registre de scripts Sicily 1 trop court.");
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
                    "Registre de scripts Sicily 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Sicily 1.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Sicily 1.");
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
