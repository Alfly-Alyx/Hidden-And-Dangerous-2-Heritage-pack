using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace HD2CommunityInstaller
{
    internal static class BrestRouteInstaller
    {
        private const string SecondDetector = "detectorzone3aktiv2";
        private const string WrongScript = "detectorzone3aktiv1.scr";
        private const string RestoredScript = "detectorzone3aktiv2.scr";

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private sealed class RegistrySpec
        {
            public string Mission;
            public string RelativePath;
        }

        private static readonly RegistrySpec[] Registries = {
            new RegistrySpec {
                Mission = "Brest",
                RelativePath = "Missions/Brest/Scripts.dta"
            },
            new RegistrySpec {
                Mission = "Co_brest",
                RelativePath = "Missions/Co_brest/Scripts.dta"
            },
            new RegistrySpec {
                Mission = "Co_brest",
                RelativePath = "Missions/Co_brest/mpscripts.dta"
            }
        };

        private sealed class Binding
        {
            public string Actor;
            public string Script;
            public int ScriptOffset;
            public int ScriptLength;
        }

        public static string ValidateOnly(string gamePath)
        {
            foreach (RegistrySpec registry in Registries)
            {
                DormantSource source = ResolveSource(
                    gamePath, registry.RelativePath, MissionArchives);
                byte[] original = ReadSource(source);
                byte[] patched = PatchRegistry(original);
                ValidateBinding(patched);
                if (!BytesEqual(patched, PatchRegistry(patched)))
                    throw new InvalidDataException(
                        "La restauration de la route de Brest n'est pas idempotente : "
                        + registry.RelativePath + ".");
            }
            ValidateAssets(gamePath, "Brest");
            ValidateAssets(gamePath, "Co_brest");
            return "Routes Brest verifiees : le second passage possede son detecteur, "
                + "son script et son comportement alternatif complets en solo et en cooperation.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (RegistrySpec registry in Registries)
                {
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, registry.RelativePath);
                    if (!File.Exists(target) || !HasRestoredBinding(
                        File.ReadAllBytes(target)))
                        return false;
                }
                return true;
            }
            catch { return false; }
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Reactivation de la seconde route de Brest en solo et en cooperation...");
            ValidateAssets(gamePath, "Brest");
            ValidateAssets(gamePath, "Co_brest");
            int changed = 0;
            foreach (RegistrySpec registry in Registries)
                if (InstallRegistry(
                    gamePath, registry, journal, prepared))
                    changed++;

            if (changed == 0)
            {
                InstallerCore.Report(progress,
                    "Seconde route de Brest deja active en solo et en cooperation; aucune modification.");
                return;
            }
            InstallerCore.Log(
                "Brest : second detecteur relie a son script alternatif original "
                + "dans " + changed + " registre(s) solo/cooperation.");
            InstallerCore.Report(progress,
                "La seconde route de Brest a ete reactivee en solo et en cooperation.");
        }

        private static bool InstallRegistry(
            string gamePath, RegistrySpec registry, StateJournal journal,
            HashSet<string> prepared)
        {
            DormantSource source = ResolveSource(
                gamePath, registry.RelativePath, MissionArchives);
            string target = InstallerCore.SafeGameTarget(
                gamePath, registry.RelativePath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchRegistry(original);
            ValidateBinding(patched);
            if (BytesEqual(original, patched)) return false;

            InstallerCore.PrepareTarget(
                gamePath, registry.RelativePath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    registry.RelativePath,
                    CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            return true;
        }

        private static byte[] PatchRegistry(byte[] data)
        {
            byte[] result = null;
            int found = 0;
            foreach (Binding binding in ReadBindings(data))
            {
                if (!String.Equals(
                    binding.Actor, SecondDetector,
                    StringComparison.OrdinalIgnoreCase))
                    continue;
                found++;
                if (String.Equals(
                    binding.Script, RestoredScript,
                    StringComparison.OrdinalIgnoreCase))
                    continue;
                if (!String.Equals(
                    binding.Script, WrongScript,
                    StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "Le second detecteur de Brest possede un script inattendu : "
                        + binding.Script + ".");
                byte[] replacement = Encoding.GetEncoding(1252)
                    .GetBytes(RestoredScript);
                if (replacement.Length != binding.ScriptLength)
                    throw new InvalidDataException(
                        "La correction de Brest changerait la structure du registre.");
                if (result == null) result = (byte[])data.Clone();
                Buffer.BlockCopy(replacement, 0, result,
                    binding.ScriptOffset, replacement.Length);
            }
            if (found != 1)
                throw new InvalidDataException(
                    "Le second detecteur de Brest est absent ou duplique.");
            return result ?? data;
        }

        private static List<Binding> ReadBindings(byte[] data)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Brest trop court.");
            Encoding ansi = Encoding.GetEncoding(1252);
            List<Binding> result = new List<Binding>();
            int offset = 6;
            while (offset < data.Length)
            {
                int ignoredOffset;
                int ignoredLength;
                string actor = ReadField(data, ref offset, ansi,
                    out ignoredOffset, out ignoredLength);
                int scriptOffset;
                int scriptLength;
                string script = ReadField(data, ref offset, ansi,
                    out scriptOffset, out scriptLength);
                result.Add(new Binding {
                    Actor = actor,
                    Script = script,
                    ScriptOffset = scriptOffset,
                    ScriptLength = scriptLength
                });
            }
            return result;
        }

        private static string ReadField(
            byte[] data, ref int offset, Encoding encoding,
            out int valueOffset, out int valueLength)
        {
            if (offset < 0 || offset > data.Length - 6
                || BitConverter.ToUInt16(data, offset) != 1)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Brest.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Brest.");
            valueOffset = offset + 6;
            valueLength = (int)rawLength - 7;
            string value = encoding.GetString(
                data, valueOffset, valueLength);
            offset += (int)rawLength;
            return value;
        }

        private static bool HasRestoredBinding(byte[] data)
        {
            int found = 0;
            foreach (Binding binding in ReadBindings(data))
                if (String.Equals(
                    binding.Actor, SecondDetector,
                    StringComparison.OrdinalIgnoreCase)
                    && String.Equals(
                    binding.Script, RestoredScript,
                    StringComparison.OrdinalIgnoreCase))
                    found++;
            return found == 1;
        }

        private static void ValidateBinding(byte[] data)
        {
            if (!HasRestoredBinding(data))
                throw new InvalidDataException(
                    "La seconde route de Brest n'est pas reliee de facon unique.");
        }

        private static void ValidateAssets(string gamePath, string mission)
        {
            ValidateAsset(gamePath, "Missions/" + mission + "/actors.bin",
                MissionArchives,
                new[] { "detectorzone3aktiv1", "detectorzone3aktiv2" });
            ValidateAsset(gamePath,
                "Scripts/" + mission + "/detectorzone3aktiv1.scr",
                ScriptArchives,
                new[] { "FRM_FindFrame(z3_ven4", "sendsignal (z3_ven4,1)" });
            ValidateAsset(gamePath,
                "Scripts/" + mission + "/detectorzone3aktiv2.scr",
                ScriptArchives,
                new[] { "FRM_FindFrame(z3_ven4", "sendsignal (z3_ven4,2)" });
            ValidateAsset(gamePath, "Scripts/" + mission + "/z3_ven4.scr",
                ScriptArchives,
                new[] {
                    "_SignalReceived(1)", "_SignalReceived(2)",
                    "HUMAN_Move(\"z3ven4_01\")",
                    "HUMAN_Move(\"z3ven4_02\")"
                });
        }

        private static void ValidateAsset(
            string gamePath, string relative, string[] archives,
            string[] markers)
        {
            DormantSource source = ResolveSource(gamePath, relative, archives);
            string text = Encoding.GetEncoding(1252).GetString(ReadSource(source));
            foreach (string marker in markers)
                if (text.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Element Brest manquant dans " + relative + " : "
                        + marker + ".");
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