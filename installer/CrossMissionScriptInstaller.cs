using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace HD2CommunityInstaller
{
    internal sealed class CrossMissionScriptSpec
    {
        public string SourcePath;
        public string TargetPath;
        public string RegistryPath;
        public string Actor;
        public string Script;
        public string AssetPath;
        public string[] SourceMarkers;
    }

    internal static class CrossMissionScriptInstaller
    {
        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly CrossMissionScriptSpec[] Scripts = {
            new CrossMissionScriptSpec {
                SourcePath = "Scripts/Burgundy1/bu1_diary.scr",
                TargetPath = "Scripts/Co_Burgundy1/bu1_diary.scr",
                RegistryPath = "Missions/Co_Burgundy1/mpscripts.dta",
                Actor = "dummy_diary",
                Script = "bu1_diary.scr",
                AssetPath = "Missions/Co_Burgundy1/scene2.bin",
                SourceMarkers = new[] {
                    "AddDiaryText(16016)", "AddDiaryText(17660)",
                    "AddDiaryText(17665)"
                }
            },
        };

        public static string ValidateOnly(string gamePath)
        {
            ValidateSourcesAndTargets(gamePath);
            return "Script officiel Burgundy 1 coop verifie : journal restaurable.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                ValidateSourcesAndTargets(gamePath);
                foreach (CrossMissionScriptSpec spec in Scripts)
                {
                    string target = InstallerCore.SafeGameTarget(gamePath, spec.TargetPath);
                    if (!File.Exists(target)) return false;
                    byte[] expected = ReadSource(ResolveSource(
                        gamePath, spec.SourcePath, ScriptArchives));
                    if (!BytesEqual(expected, File.ReadAllBytes(target))) return false;
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
                "Restauration des scripts officiels de Burgundy 1 cooperatif...");
            ValidateSourcesAndTargets(gamePath);
            int changed = 0;
            foreach (CrossMissionScriptSpec spec in Scripts)
            {
                byte[] official = ReadSource(ResolveSource(
                    gamePath, spec.SourcePath, ScriptArchives));
                string target = InstallerCore.SafeGameTarget(gamePath, spec.TargetPath);
                if (File.Exists(target)
                    && BytesEqual(official, File.ReadAllBytes(target)))
                    continue;

                InstallerCore.PrepareTarget(
                    gamePath, spec.TargetPath, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, official);
                    File.Copy(temporary, target, true);
                    journal.RecordHash(
                        spec.TargetPath, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                changed++;
            }
            InstallerCore.Log("Burgundy 1 coop : " + changed
                + " script officiel restaure.");
            InstallerCore.Report(progress,
                "Burgundy 1 cooperatif : journal officiel restaure.");
        }

        private static void ValidateSourcesAndTargets(string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);
            foreach (CrossMissionScriptSpec spec in Scripts)
            {
                byte[] source = ReadSource(ResolveSource(
                    gamePath, spec.SourcePath, ScriptArchives));
                string text = Encoding.GetEncoding(1252).GetString(source);
                foreach (string marker in spec.SourceMarkers)
                    if (text.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                        throw new InvalidDataException(
                            "Donnee officielle manquante dans " + spec.SourcePath
                            + " : " + marker + ".");

                byte[] registry = ReadSource(ResolveSource(
                    gamePath, spec.RegistryPath, MissionArchives));
                if (!HasBinding(registry, spec.Actor, spec.Script))
                    throw new InvalidDataException(
                        "Liaison officielle absente : " + spec.Actor
                        + " -> " + spec.Script + ".");

                byte[] asset = ReadSource(ResolveSource(
                    gamePath, spec.AssetPath, MissionArchives));
                string assetText = Encoding.GetEncoding(1252).GetString(asset);
                if (assetText.IndexOf(spec.Actor,
                    StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Acteur officiel absent de la carte : " + spec.Actor + ".");
            }
        }

        private static bool HasBinding(byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException("Registre de scripts trop court.");
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
                throw new InvalidDataException("Registre de scripts tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre de scripts.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
        }

        private static ObjectiveScriptSource ResolveSource(
            string gamePath, string relative, string[] archiveNames)
        {
            ObjectiveScriptSource result = null;
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
                            result = new ObjectiveScriptSource {
                                ArchivePath = archivePath,
                                EntryIndex = entry.Index,
                                RelativePath = relative
                            };
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