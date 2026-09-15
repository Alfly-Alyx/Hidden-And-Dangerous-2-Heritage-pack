using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class CoLibye1SmokingInstaller
    {
        private const string RegistryPath = "Missions/Co_Libye1/mpscripts.dta";
        private static readonly string[] Scripts = {
            "AF1_33", "AF1_50", "AF1_52", "AF1_53"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (string actor in Scripts)
            {
                string relative = ScriptPath(actor);
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(original, actor);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "L'animation de cigarette de " + actor
                        + " semble deja restauree.");
                ValidatePatched(patched, actor);
                if (!BytesEqual(patched, PatchScript(patched, actor)))
                    throw new InvalidDataException(
                        "La restauration de " + actor + " n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Libye 1 cooperative verifiee : quatre gardes retrouvent "
                + "leurs animations de cigarette et les interrompent a l'alarme.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string actor in Scripts)
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
                "Restauration des animations de cigarette de Libye 1 cooperative...");
            ValidateAssets(gamePath);
            List<ScriptChange> changes = new List<ScriptChange>();
            foreach (string actor in Scripts)
            {
                string relative = ScriptPath(actor);
                DormantSource source = ResolveSource(
                    gamePath, relative, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(original, actor);
                ValidatePatched(patched, actor);
                changes.Add(new ScriptChange {
                    Actor = actor,
                    Relative = relative,
                    Target = target,
                    Original = original,
                    Patched = patched
                });
            }

            int written = 0;
            foreach (ScriptChange change in changes)
            {
                if (BytesEqual(change.Original, change.Patched)) continue;
                InstallerCore.PrepareTarget(
                    gamePath, change.Relative, change.Target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(change.Target));
                string temporary = change.Target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, change.Patched);
                    File.Copy(temporary, change.Target, true);
                    journal.RecordHash(
                        change.Relative, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                written++;
            }

            if (written == 0)
            {
                InstallerCore.Report(progress,
                    "Les animations de cigarette de Libye 1 cooperative sont deja restaurees.");
                return;
            }
            InstallerCore.Log(
                "Libye 1 cooperative : animations de cigarette restaurees pour "
                + written + " gardes.");
            InstallerCore.Report(progress,
                "Quatre gardes de Libye 1 cooperative retrouvent leur activite d'origine.");
        }

        private static string ScriptPath(string actor)
        {
            return "Scripts/Co_Libye1/" + actor + ".scr";
        }

        private static byte[] PatchScript(byte[] data, string actor)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*HUMAN_ACTIVITY_Smoke\s*"
                + @"\(\s*(?<state>true|false|1|0)\s*\)\s*;[^\r\n]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            int active = ActiveCount(text);
            int dormantCount = dormant.Matches(text).Count;
            if (active == 2 && dormantCount == 0)
            {
                ValidatePatched(data, actor);
                return data;
            }
            if (active != 0 || dormantCount != 2)
                throw new InvalidDataException(
                    "Etat inattendu des animations de cigarette dans "
                    + actor + ".scr.");

            text = dormant.Replace(text, match =>
                match.Groups["indent"].Value + "HUMAN_ACTIVITY_Smoke("
                + match.Groups["state"].Value.ToLowerInvariant() + ");");
            return ansi.GetBytes(text);
        }

        private static int ActiveCount(string text)
        {
            return Regex.Matches(text,
                @"(?m)^[ \t]*HUMAN_ACTIVITY_Smoke\s*\(\s*"
                + @"(?:true|false|1|0)\s*\)\s*;",
                RegexOptions.IgnoreCase).Count;
        }

        private static void ValidatePatched(byte[] data, string actor)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveCount(text) != 2)
                throw new InvalidDataException(
                    "Les deux commandes de cigarette de " + actor
                    + " ne sont pas actives.");
            if (String.Equals(actor, "AF1_33", StringComparison.OrdinalIgnoreCase))
            {
                Require(text,
                    @"Label\s+activity\s*:[\s\S]{0,1000}"
                    + @"HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,120}Delay\s*\(\s*120000\s*\)\s*;"
                    + @"[\s\S]{0,120}HUMAN_ACTIVITY_Smoke\s*\(\s*false\s*\)\s*;",
                    "La sequence longue de cigarette d'AF1_33 est incomplete.");
            }
            else
            {
                Require(text,
                    @"OnAlarm\s*\(\s*\)\s*\{[\s\S]{0,180}"
                    + @"HUMAN_ACTIVITY_Smoke\s*\(\s*false\s*\)\s*;",
                    "L'arret de la cigarette a l'alarme manque dans "
                    + actor + ".scr.");
                Require(text,
                    @"Label\s+DeAlarm\s*:[\s\S]{0,180}"
                    + @"HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)\s*;"
                    + @"[\s\S]{0,100}Label\s+end\s*:",
                    "La reprise de cigarette de " + actor + " est incomplete.");
            }
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            foreach (string actor in Scripts)
                if (!HasBinding(registry, actor, actor + ".scr"))
                    throw new InvalidDataException(
                        "La liaison cooperative de " + actor + " est absente.");

            foreach (string reference in new[] {
                "Scripts/Libye1/AF1_33.scr",
                "Scripts/Libye3/Li3_German_14.scr"
            })
            {
                string script = Encoding.GetEncoding(1252).GetString(
                    ReadSource(ResolveSource(gamePath, reference, ScriptArchives)));
                Require(script,
                    @"(?m)^[ \t]*HUMAN_ACTIVITY_Smoke\s*\(\s*true\s*\)\s*;",
                    "Le demarrage officiel de l'animation de cigarette manque dans "
                    + reference + ".");
                Require(script,
                    @"(?m)^[ \t]*HUMAN_ACTIVITY_Smoke\s*\(\s*false\s*\)\s*;",
                    "L'arret officiel de l'animation de cigarette manque dans "
                    + reference + ".");
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Libye 1 cooperative trop court.");
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
                    "Registre Libye 1 cooperative tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Libye 1 cooperative.");
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

        private sealed class ScriptChange
        {
            public string Actor;
            public string Relative;
            public string Target;
            public byte[] Original;
            public byte[] Patched;
        }
    }
}