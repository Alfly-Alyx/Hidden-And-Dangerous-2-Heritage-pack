using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class BrestDormantGuardActionsInstaller
    {
        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private sealed class ScriptSpec
        {
            public string Relative;
            public int DormantCount;
            public int ActiveBefore;

            public int ActiveAfter
            {
                get { return DormantCount + ActiveBefore; }
            }
        }

        private static ScriptSpec Spec(
            string mission, string file, int dormant, int activeBefore)
        {
            return new ScriptSpec {
                Relative = "Scripts/" + mission + "/" + file,
                DormantCount = dormant,
                ActiveBefore = activeBefore
            };
        }

        private static readonly ScriptSpec[] Scripts = {
            Spec("Brest", "ven_klicnik.scr", 1, 0),
            Spec("Brest", "venek1.scr", 3, 1),
            Spec("Brest", "venek2.scr", 1, 0),
            Spec("Brest", "venek3.scr", 4, 1),
            Spec("Brest", "venek4.scr", 1, 0),
            Spec("Brest", "z2_domek2.scr", 1, 1),
            Spec("Brest", "z2_flak1.scr", 2, 0),
            Spec("Brest", "z2_ven1.scr", 2, 2),
            Spec("Brest", "z2_ven3.scr", 2, 2),
            Spec("Brest", "z2_ven4.scr", 2, 0),
            Spec("Brest", "z2_ven5.scr", 1, 0),
            Spec("Brest", "z3_ven1.scr", 2, 2),
            Spec("Brest", "z3_ven3.scr", 2, 0),
            Spec("Brest", "z3_ven4.scr", 1, 0),
            Spec("Brest", "z4_ven1.scr", 2, 2),
            Spec("Brest", "z4_ven2.scr", 2, 1),
            Spec("Co_brest", "ven_klicnik.scr", 1, 0),
            Spec("Co_brest", "venek1.scr", 3, 1),
            Spec("Co_brest", "venek2.scr", 1, 0),
            Spec("Co_brest", "venek3.scr", 4, 1),
            Spec("Co_brest", "venek4.scr", 1, 0),
            Spec("Co_brest", "z2_domek2.scr", 1, 1),
            Spec("Co_brest", "z2_flak1.scr", 2, 0),
            Spec("Co_brest", "z2_ven1.scr", 2, 2),
            Spec("Co_brest", "z2_ven3.scr", 2, 2),
            Spec("Co_brest", "z2_ven4.scr", 2, 0),
            Spec("Co_brest", "z2_ven5.scr", 1, 0),
            Spec("Co_brest", "z3_ven1.scr", 2, 2),
            Spec("Co_brest", "z3_ven3.scr", 2, 0),
            Spec("Co_brest", "z3_ven4.scr", 1, 0),
            Spec("Co_brest", "z4_ven1.scr", 2, 2),
            Spec("Co_brest", "z4_ven2.scr", 2, 1),
            Spec("Co_brest", "z4_venkur.scr", 1, 0)
        };

        private static readonly Regex DormantAction = new Regex(
            @"(?m)^([ \t]*)//[ \t]*((?:HUMAN_SetAnim\s*\(\s*""%%(?:koukadrep|kouka)""\s*,\s*300\s*,\s*300\s*,\s*0\s*\)|HUMAN_Attack\s*\(\s*puf\s*,\s*3000\s*\))\s*;)[ \t]*\r?$",
            RegexOptions.IgnoreCase);

        private static readonly Regex ActiveAction = new Regex(
            @"(?m)^[ \t]*(?:HUMAN_SetAnim\s*\(\s*""%%(?:koukadrep|kouka)""\s*,\s*300\s*,\s*300\s*,\s*0\s*\)|HUMAN_Attack\s*\(\s*puf\s*,\s*3000\s*\))\s*;[ \t]*\r?$",
            RegexOptions.IgnoreCase);

        public static string ValidateOnly(string gamePath)
        {
            int restored = 0;
            foreach (ScriptSpec spec in Scripts)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, spec.Relative, ScriptArchives));
                byte[] patched = PatchScript(original, spec);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "Les actions de garde de Brest semblent deja actives dans l'archive source : "
                        + spec.Relative + ".");
                ValidatePatched(patched, spec);
                if (!BytesEqual(patched, PatchScript(patched, spec)))
                    throw new InvalidDataException(
                        "La restauration des gardes de Brest n'est pas idempotente : "
                        + spec.Relative + ".");
                restored += spec.DormantCount;
            }
            if (restored != 59)
                throw new InvalidDataException(
                    "Le total des actions dormantes de Brest est inattendu.");
            ValidateAssets(gamePath);
            return "Brest verifiee : 49 animations d'observation et 10 reactions "
                + "a un cadavre peuvent etre restaurees en solo et en cooperation.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (ScriptSpec spec in Scripts)
                {
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, spec.Relative);
                    if (!File.Exists(target)) return false;
                    ValidatePatched(File.ReadAllBytes(target), spec);
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
                "Restauration des observations et reactions des gardes de Brest...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (ScriptSpec spec in Scripts)
                if (InstallScript(gamePath, spec, journal, prepared))
                    changed++;

            if (changed == 0)
            {
                InstallerCore.Report(progress,
                    "Les actions dormantes des gardes de Brest sont deja actives.");
                return;
            }
            InstallerCore.Log(
                "Brest : 59 actions de garde restaurees dans " + changed
                + " script(s) solo/cooperation.");
            InstallerCore.Report(progress,
                "Les sentinelles de Brest observent et reagissent de nouveau comme prevu.");
        }

        private static bool InstallScript(
            string gamePath, ScriptSpec spec, StateJournal journal,
            HashSet<string> prepared)
        {
            DormantSource source = ResolveSource(
                gamePath, spec.Relative, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(
                gamePath, spec.Relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original, spec);
            ValidatePatched(patched, spec);
            if (BytesEqual(original, patched)) return false;

            InstallerCore.PrepareTarget(
                gamePath, spec.Relative, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    spec.Relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            return true;
        }

        private static byte[] PatchScript(byte[] data, ScriptSpec spec)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            int dormant = DormantAction.Matches(text).Count;
            int active = ActiveAction.Matches(text).Count;
            if (dormant == 0 && active == spec.ActiveAfter)
                return data;
            if (dormant != spec.DormantCount
                || active != spec.ActiveBefore)
                throw new InvalidDataException(
                    "Actions dormantes de Brest absentes ou partielles : "
                    + spec.Relative + ".");
            return ansi.GetBytes(DormantAction.Replace(text, "$1$2"));
        }

        private static void ValidatePatched(byte[] data, ScriptSpec spec)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (DormantAction.Matches(text).Count != 0
                || ActiveAction.Matches(text).Count != spec.ActiveAfter)
                throw new InvalidDataException(
                    "Actions de garde Brest incompletes : "
                    + spec.Relative + ".");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] soloRegistry = ReadSource(ResolveSource(
                gamePath, "Missions/Brest/Scripts.dta", MissionArchives));
            byte[] coopRegistry = ReadSource(ResolveSource(
                gamePath, "Missions/Co_brest/Scripts.dta", MissionArchives));
            byte[] coopMpRegistry = ReadSource(ResolveSource(
                gamePath, "Missions/Co_brest/mpscripts.dta", MissionArchives));

            foreach (ScriptSpec spec in Scripts)
            {
                string script = Path.GetFileName(spec.Relative);
                if (spec.Relative.StartsWith(
                    "Scripts/Brest/", StringComparison.OrdinalIgnoreCase))
                {
                    if (!HasScriptBinding(soloRegistry, script))
                        throw new InvalidDataException(
                            "Script de garde Brest non relie : " + script + ".");
                }
                else if (!HasScriptBinding(coopRegistry, script)
                    || !HasScriptBinding(coopMpRegistry, script))
                    throw new InvalidDataException(
                        "Script de garde Co_brest incomplet dans les registres : "
                        + script + ".");
            }

            foreach (string relative in new[] {
                "Missions/Brest/actors.bin",
                "Missions/Co_brest/actors.bin"
            })
            {
                byte[] actors = ReadSource(ResolveSource(
                    gamePath, relative, MissionArchives));
                if (CountAscii(actors, "venek1puf") < 1)
                    throw new InvalidDataException(
                        "Cible d'alerte venek1puf absente : " + relative + ".");
            }
        }

        private static bool HasScriptBinding(byte[] data, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Brest trop court.");
            int offset = 6;
            while (offset < data.Length)
            {
                ReadRegistryField(data, ref offset);
                string script = ReadRegistryField(data, ref offset);
                if (String.Equals(script, wantedScript,
                        StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException(
                    "Registre de scripts Brest tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Brest.");
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
                    && ToLowerAscii(data[start + index]) == ToLowerAscii(needle[index]))
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
                    "Donnee officielle Brest introuvable : " + relative);
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
