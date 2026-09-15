using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Czech2CutsceneSmokeInstaller
    {
        private const string ScriptPath =
            "Scripts/CZECH2/CUTgeneral_cz2.scr";
        private const string RegistryPath = "Missions/CZECH2/Scripts.dta";
        private const string ScenePath = "Missions/CZECH2/scene2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, ScriptPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "La fumee de la cinematique Czech 2 semble deja nettoyee.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "Le nettoyage de fumee Czech 2 n'est pas idempotent.");
            ValidateAssets(gamePath);
            return "Czech 2 verifie : la fumee de cigare creee par la "
                + "cinematique peut etre detruite par son instruction officielle.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
                if (!File.Exists(target)) return false;
                ValidatePatched(File.ReadAllBytes(target));
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
                "Nettoyage de la fumee de cigare de la cinematique Czech 2...");
            DormantSource source = ResolveSource(
                gamePath, ScriptPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Le nettoyage de la fumee Czech 2 est deja actif.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, ScriptPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    ScriptPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Czech 2 : nettoyage officiel de la fumee de cinematique reactive.");
            InstallerCore.Report(progress,
                "La fumee de cigare Czech 2 ne persiste plus apres la cinematique.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsPatched(text))
            {
                ValidatePatched(data);
                return data;
            }

            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*FRM_DestroyIndexedParticle\s*"
                + @"\(\s*cigdym\s*\)\s*;[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Nettoyage dormant de la fumee Czech 2 introuvable.");
            text = dormant.Replace(text, match =>
                match.Groups["indent"].Value
                + "FRM_DestroyIndexedParticle(cigdym);", 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"OnCutsceneDone\s*\(\s*1\s*\)\s*\{[\s\S]{0,420}"
                + @"FRM_SetOn\s*\(\s*MyFrame\s*,\s*false\s*\)\s*;"
                + @"[\s\S]{0,160}FRM_DestroyIndexedParticle\s*"
                + @"\(\s*cigdym\s*\)\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsPatched(text))
                throw new InvalidDataException(
                    "Sequence de nettoyage de fumee Czech 2 incomplete.");
            if (Regex.Matches(text,
                    @"(?m)^[ \t]*FRM_DestroyIndexedParticle\s*"
                    + @"\(\s*cigdym\s*\)\s*;",
                    RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(
                    "Nombre inattendu de nettoyages de fumee Czech 2.");
            Require(text,
                @"FRM_CreateIndexedParticle\s*\(\s*10\s*,\s*dym_cig\s*,\s*cigdym\s*\)",
                "Creation officielle de la fumee Czech 2 absente.");
            Require(text,
                @"FRM_FindFrame\s*\(\s*dym_cig\s*,\s*""CUTcigaro\.particle""\s*\)",
                "Ancre officielle de la fumee Czech 2 absente.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "Ge05b_", "CUTgeneral_cz2.scr"))
                throw new InvalidDataException(
                    "Liaison de la cinematique generale Czech 2 absente.");
            string scene = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, ScenePath, MissionArchives)));
            if (scene.IndexOf("CUTcigaro.particle",
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Ancre de fumee CUTcigaro.particle absente de Czech 2.");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Czech 2 trop court.");
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
                    "Registre de scripts Czech 2 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Czech 2.");
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