using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class OfficialEasterEggInstaller
    {
        private const string Africa1ActivatorPath = "Scripts/AFRICA1/AF1_ee.scr";
        private const string Africa1RegistryPath = "Missions/AFRICA1/scripts.dta";
        private const string Africa1ActorsPath = "Missions/AFRICA1/actors.bin";
        private const string Africa1ScenePath = "Missions/AFRICA1/scene2.bin";
        private const string Africa4ActivatorPath = "Scripts/AFRICA4/AF3b_ee_activator.scr";
        private const string Africa4EffectPath = "Scripts/AFRICA4/AF3b_ee.scr";
        private const string Africa4RegistryPath = "Missions/AFRICA4/Scripts.dta";
        private const string Africa4ScenePath = "Missions/AFRICA4/scene2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly Regex Africa1DisabledTrigger = new Regex(
            @"(Whenever\s+mrtvolaci\s*\(\s*!_ACTOR_GetState\s*\(\s*m01\s*\)\s*\)\s*\{[\s\S]*?mrtvi_panaci\s*=\s*)0\s*;",
            RegexOptions.IgnoreCase);

        private static readonly Regex Africa1ActiveTrigger = new Regex(
            @"Whenever\s+mrtvolaci\s*\(\s*!_ACTOR_GetState\s*\(\s*m01\s*\)\s*\)\s*\{[\s\S]*?mrtvi_panaci\s*=\s*1\s*;",
            RegexOptions.IgnoreCase);

        private static readonly Regex Africa4DisabledTrigger = new Regex(
            @"(Whenever\s+iir\s*\(\s*\(\s*_ItemInRange\s*\(\s*240\s*,\s*3\s*\)\s+AND\s+_ItemInRange\s*\(\s*241\s*,\s*3\s*\)\s*\)\s+AND\s+_ItemInRange\s*\(\s*242\s*,\s*3\s*\)\s*\)\s*\{\s*)goto\s+END\s*;",
            RegexOptions.IgnoreCase);

        private static readonly Regex Africa4ActiveTrigger = new Regex(
            @"Whenever\s+iir\s*\(\s*\(\s*_ItemInRange\s*\(\s*240\s*,\s*3\s*\)\s+AND\s+_ItemInRange\s*\(\s*241\s*,\s*3\s*\)\s*\)\s+AND\s*_ItemInRange\s*\(\s*242\s*,\s*3\s*\)\s*\)\s*\{\s*goto\s+ACTIVATED\s*;",
            RegexOptions.IgnoreCase);

        public static string ValidateOnly(string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);

            ValidateAfrica1SupportingData(gamePath);
            byte[] africa1Original = ReadSource(ResolveSource(
                gamePath, Africa1ActivatorPath, ScriptArchives));
            string africa1Text = Encoding.GetEncoding(1252).GetString(africa1Original);
            if (Africa1DisabledTrigger.Matches(africa1Text).Count != 1)
                throw new InvalidDataException(
                    "La neutralisation officielle de l'easter egg Africa 1 n'a pas la structure attendue.");
            ValidateAfrica1Patched(PatchAfrica1Script(africa1Original));

            ValidateAfrica4SupportingData(gamePath);
            byte[] africa4Original = ReadSource(ResolveSource(
                gamePath, Africa4ActivatorPath, ScriptArchives));
            string africa4Text = Encoding.GetEncoding(1252).GetString(africa4Original);
            if (Africa4DisabledTrigger.Matches(africa4Text).Count != 1)
                throw new InvalidDataException(
                    "La neutralisation officielle de l'easter egg Africa 4 n'a pas la structure attendue.");
            ValidateAfrica4Patched(PatchAfrica4Script(africa4Original));

            return "Easter eggs verifies : la mise a jour 1.12 neutralise explicitement "
                + "Africa 1 et Africa 4, tandis que leurs scenes et effets restent complets.";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallAfrica1(gamePath, journal, prepared, progress);
            InstallAfrica4(gamePath, journal, prepared, progress);
        }

        private static void InstallAfrica1(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Reactivation de l'easter egg cache d'Africa 1...");
            ValidateAfrica1SupportingData(gamePath);
            ObjectiveScriptSource source = ResolveSource(
                gamePath, Africa1ActivatorPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, Africa1ActivatorPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target)
                : ReadSource(source);
            byte[] patched = PatchAfrica1Script(original);
            ValidateAfrica1Patched(patched);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Easter egg Africa 1 deja actif; aucune modification.");
                return;
            }

            WriteOverride(gamePath, Africa1ActivatorPath, target, patched,
                journal, prepared);
            InstallerCore.Log("Africa 1 : easter egg du jeep reactive.");
            InstallerCore.Report(progress,
                "Africa 1 : la sequence cachee du jeep est de nouveau activable.");
        }

        private static void InstallAfrica4(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Reactivation de la tempete de meteores cachee d'Africa 4...");
            ValidateAfrica4SupportingData(gamePath);
            ObjectiveScriptSource source = ResolveSource(
                gamePath, Africa4ActivatorPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, Africa4ActivatorPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target)
                : ReadSource(source);
            byte[] patched = PatchAfrica4Script(original);
            ValidateAfrica4Patched(patched);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Tempete de meteores Africa 4 deja active; aucune modification.");
                return;
            }

            WriteOverride(gamePath, Africa4ActivatorPath, target, patched,
                journal, prepared);
            InstallerCore.Log("Africa 4 : easter egg des trois cles reactive.");
            InstallerCore.Report(progress,
                "Africa 4 : la reunion des cles A, B et C reactive la tempete cachee.");
        }

        private static byte[] PatchAfrica1Script(byte[] source)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(source);
            if (Africa1ActiveTrigger.Matches(text).Count == 1) return source;
            if (Africa1ActiveTrigger.IsMatch(text)
                || Africa1DisabledTrigger.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du declencheur Africa 1.");
            string patched = Africa1DisabledTrigger.Replace(text, "${1}1;", 1);
            return ansi.GetBytes(patched);
        }

        private static byte[] PatchAfrica4Script(byte[] source)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(source);
            if (Africa4ActiveTrigger.Matches(text).Count == 1) return source;
            if (Africa4ActiveTrigger.IsMatch(text)
                || Africa4DisabledTrigger.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du declencheur Africa 4.");
            string patched = Africa4DisabledTrigger.Replace(
                text, "$1goto ACTIVATED;", 1);
            return ansi.GetBytes(patched);
        }

        private static void ValidateAfrica1Patched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (Africa1ActiveTrigger.Matches(text).Count != 1
                || text.IndexOf("goto ACTIVATED", StringComparison.OrdinalIgnoreCase) < 0
                || text.IndexOf("la_RedArmor_01", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Le declencheur Africa 1 n'a pas ete reactive correctement.");
        }

        private static void ValidateAfrica4Patched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (Africa4ActiveTrigger.Matches(text).Count != 1
                || !Regex.IsMatch(text,
                    @"Label\s+ACTIVATED\s*:[\s\S]*SaveGameValue\s*\(\s*60\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le declencheur Africa 4 n'a pas ete reactive correctement.");
        }

        private static void ValidateAfrica1SupportingData(string gamePath)
        {
            string registry = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, Africa1RegistryPath, MissionArchives)));
            if (registry.IndexOf("AF1_ee.scr", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Le script cache Africa 1 n'est plus lie a la mission.");

            string actors = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, Africa1ActorsPath, MissionArchives)));
            foreach (string required in new[] {
                "AF1_21", "la_Jeepsas_01", "ee_01", "ee_02", "ee_03",
                "la_RedArmor_01" })
                if (actors.IndexOf(required, StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Element cache Africa 1 absent : " + required);

            string scene = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, Africa1ScenePath, MissionArchives)));
            if (scene.IndexOf("dummy_fire_portal", StringComparison.OrdinalIgnoreCase) < 0
                || scene.IndexOf("camera_ee", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "La scene cachee Africa 1 est incomplete.");
        }

        private static void ValidateAfrica4SupportingData(string gamePath)
        {
            byte[] effect = ReadSource(ResolveSource(
                gamePath, Africa4EffectPath, ScriptArchives));
            string effectText = Encoding.GetEncoding(1252).GetString(effect);
            if (effectText.IndexOf("FRM_FindFrame(meteor, \"meteor01\")",
                    StringComparison.OrdinalIgnoreCase) < 0
                || effectText.IndexOf("FRM_WatchTrack(meteor, \"t_meteor_01\")",
                    StringComparison.OrdinalIgnoreCase) < 0
                || !Regex.IsMatch(effectText,
                    @"_LoadGameValue\s*\(\s*60\s*\)\s*==\s*1",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le script de tempete Africa 4 est incomplet.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, Africa4RegistryPath, MissionArchives));
            string registryText = Encoding.GetEncoding(1252).GetString(registry);
            if (registryText.IndexOf("AF3b_ee.scr", StringComparison.OrdinalIgnoreCase) < 0
                || registryText.IndexOf("AF3b_ee_activator.scr",
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Les scripts caches Africa 4 ne sont plus lies a la mission.");

            byte[] scene = ReadSource(ResolveSource(
                gamePath, Africa4ScenePath, MissionArchives));
            if (Encoding.GetEncoding(1252).GetString(scene).IndexOf(
                    "meteor01", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Le modele de meteore Africa 4 est absent de la scene.");
        }

        private static void WriteOverride(
            string gamePath, string relativePath, string target, byte[] data,
            StateJournal journal, HashSet<string> prepared)
        {
            InstallerCore.PrepareTarget(
                gamePath, relativePath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, data);
                File.Copy(temporary, target, true);
                journal.RecordHash(relativePath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        private static ObjectiveScriptSource ResolveSource(
            string gamePath, string relative, string[] archiveNames)
        {
            ObjectiveScriptSource result = null;
            foreach (string archiveName in archiveNames)
            {
                string archivePath = Path.Combine(gamePath, archiveName);
                if (!File.Exists(archivePath))
                    throw new FileNotFoundException("Archive officielle manquante.", archivePath);
                using (DtaArchive archive = new DtaArchive(archivePath))
                {
                    foreach (DtaEntry entry in archive.Entries)
                    {
                        string normalized = entry.Name.Replace((char)92, '/');
                        if (String.Equals(normalized, relative,
                            StringComparison.OrdinalIgnoreCase))
                            result = new ObjectiveScriptSource {
                                ArchivePath = archivePath,
                                EntryIndex = entry.Index,
                                RelativePath = relative
                            };
                    }
                }
            }
            if (result == null)
                throw new InvalidDataException(
                    "Donnee officielle introuvable : " + relative);
            return result;
        }

        private static byte[] ReadSource(ObjectiveScriptSource source)
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