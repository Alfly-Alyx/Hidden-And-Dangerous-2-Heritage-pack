using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Burgundy2DormantBehaviorInstaller
    {
        private enum BehaviorKind
        {
            PathResume,
            Murmur
        }

        private sealed class ScriptSpec
        {
            public string ScriptPath;
            public string RegistryPath;
            public string Actor;
            public string Script;
            public BehaviorKind Kind;
        }

        private static readonly ScriptSpec[] Scripts = {
            new ScriptSpec {
                ScriptPath = "Scripts/BURGUNDY2/ge_cesticka.scr",
                RegistryPath = "Missions/Burgundy2/Scripts.dta",
                Actor = "ge_cesticka", Script = "ge_cesticka.scr",
                Kind = BehaviorKind.PathResume
            },
            new ScriptSpec {
                ScriptPath = "Scripts/Co_Burgundy2/ge_cesticka.scr",
                RegistryPath = "Missions/Co_Burgundy2/mpscripts.dta",
                Actor = "ge_cesticka", Script = "ge_cesticka.scr",
                Kind = BehaviorKind.PathResume
            },
            new ScriptSpec {
                ScriptPath = "Scripts/BURGUNDY2/gumak.scr",
                RegistryPath = "Missions/Burgundy2/Scripts.dta",
                Actor = "gumak", Script = "gumak.scr",
                Kind = BehaviorKind.Murmur
            },
            new ScriptSpec {
                ScriptPath = "Scripts/Co_Burgundy2/gumak.scr",
                RegistryPath = "Missions/Co_Burgundy2/mpscripts.dta",
                Actor = "gumak", Script = "gumak.scr",
                Kind = BehaviorKind.Murmur
            }
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (ScriptSpec spec in Scripts)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, spec.ScriptPath, ScriptArchives));
                byte[] patched = PatchScript(original, spec.Kind);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "Le vestige Burgundy 2 semble deja actif dans "
                        + spec.ScriptPath + ".");
                ValidatePatched(patched, spec.Kind);
                if (!BytesEqual(patched, PatchScript(patched, spec.Kind)))
                    throw new InvalidDataException(
                        "La restauration Burgundy 2 n'est pas idempotente dans "
                        + spec.ScriptPath + ".");
            }
            ValidateAssets(gamePath);
            return "Burgundy 2 verifiee : le garde de la petite route peut "
                + "reprendre son cinquieme segment et la boucle de marmonnement "
                + "retrouve sa replique temporisee en solo et en cooperation.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (ScriptSpec spec in Scripts)
                {
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, spec.ScriptPath);
                    if (!File.Exists(target)) return false;
                    ValidatePatched(File.ReadAllBytes(target), spec.Kind);
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
                "Restauration de deux comportements dormants de Burgundy 2...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (ScriptSpec spec in Scripts)
            {
                DormantSource source = ResolveSource(
                    gamePath, spec.ScriptPath, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(
                    gamePath, spec.ScriptPath);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(original, spec.Kind);
                ValidatePatched(patched, spec.Kind);
                if (BytesEqual(original, patched)) continue;

                InstallerCore.PrepareTarget(
                    gamePath, spec.ScriptPath, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, patched);
                    File.Copy(temporary, target, true);
                    journal.RecordHash(
                        spec.ScriptPath, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                changed++;
            }

            InstallerCore.Log(
                "Burgundy 2 : reprise de ronde et marmonnement restaures dans "
                + changed + " scripts.");
            InstallerCore.Report(progress,
                "Burgundy 2 retrouve la reprise du cinquieme segment et le marmonnement continu.");
        }

        private static byte[] PatchScript(byte[] data, BehaviorKind kind)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatched(text, kind)) return data;

            Regex dormant;
            string replacement;
            if (kind == BehaviorKind.PathResume)
            {
                dormant = new Regex(
                    @"(?m)^([ \t]*)//[ \t]*(if\s*\(\s*a\s*==\s*5\s*\)\s*\{\s*goto\s+5\s*;\s*\})[ \t]*\r?$",
                    RegexOptions.IgnoreCase);
                replacement = "${1}${2}";
            }
            else
            {
                dormant = new Regex(
                    @"(?m)^([ \t]*)//[ \t]*(FRM_MorphSpeechDelayed\s*\(\s*kolab\s*,\s*58990053\s*,\s*[15]\s*,\s*10\s*\)\s*;)[ \t]*\r?$",
                    RegexOptions.IgnoreCase);
                replacement = "${1}${2}";
            }

            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Ligne dormante Burgundy 2 introuvable ou ambigue.");
            return ansi.GetBytes(dormant.Replace(text, replacement, 1));
        }

        private static bool IsPatched(string text, BehaviorKind kind)
        {
            string pattern = kind == BehaviorKind.PathResume
                ? @"(?m)^[ \t]*if\s*\(\s*a\s*==\s*5\s*\)\s*\{\s*goto\s+5\s*;\s*\}[ \t]*\r?$"
                : @"label\s+mumlani\s*:[ \t]*\r?\n[ \t]*FRM_MorphSpeechDelayed\s*\(\s*kolab\s*,\s*58990053\s*,\s*[15]\s*,\s*10\s*\)\s*;";
            return Regex.IsMatch(text, pattern, RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(byte[] data, BehaviorKind kind)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsPatched(text, kind))
                throw new InvalidDataException(
                    "Le comportement dormant Burgundy 2 reste inactif.");

            if (kind == BehaviorKind.PathResume)
            {
                Require(text,
                    @"HUMAN_Move\s*\(\s*""ge_cesticka4""\s*\)\s*;[\s\S]{0,80}a\s*=\s*5\s*;",
                    "L'etat 5 de ge_cesticka n'est plus produit.");
                Require(text,
                    @"label\s+5\s*:[\s\S]{0,80}HUMAN_Move\s*\(\s*""ge_cesticka2""\s*\)",
                    "Le cinquieme segment de ge_cesticka est absent.");
                Require(text,
                    @"label\s+rozdel\s*:[\s\S]{0,260}if\s*\(\s*a\s*==\s*5\s*\)\s*\{\s*goto\s+5\s*;",
                    "La reprise de ge_cesticka n'est pas dans son repartiteur d'alarme.");
            }
            else
            {
                Require(text,
                    @"label\s+mumlani\s*:[\s\S]{0,100}FRM_MorphSpeechDelayed\s*\(\s*kolab\s*,\s*58990053\s*,\s*[15]\s*,\s*10\s*\)\s*;[\s\S]{0,80}goto\s+mumlani\s*;",
                    "La replique n'est pas dans la boucle de marmonnement Burgundy 2.");
            }
        }

        private static void ValidateAssets(string gamePath)
        {
            foreach (ScriptSpec spec in Scripts)
            {
                byte[] registry = ReadSource(ResolveSource(
                    gamePath, spec.RegistryPath, MissionArchives));
                if (!HasBinding(registry, spec.Actor, spec.Script))
                    throw new InvalidDataException(
                        "Liaison Burgundy 2 absente : " + spec.Actor
                        + " -> " + spec.Script + ".");
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Burgundy 2 trop court.");
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
                    "Registre de scripts Burgundy 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Burgundy 2.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
        }

        private static void Require(string text, string pattern, string message)
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
