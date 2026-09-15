using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Arctic4IceFallInstaller
    {
        private const string ScriptPath =
            "Scripts/ARCTIC4/R_Arc3_bouchni.scr";
        private const string RegistryPath = "Missions/ARCTIC4/Scripts.dta";
        private const string ScenePath = "Missions/ARCTIC4/scene2.bin";
        private const string ActorsPath = "Missions/ARCTIC4/actors.bin";

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
                    "L'impact de la chute de glace Arctic 4 semble deja actif.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration de la chute de glace Arctic 4 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Arctic 4 verifie : l'explosion exacte de la chute de glace "
                + "peut etre reactivee sans creer d'acteur ni de declencheur.";
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
                "Restauration de l'impact de la chute de glace dans Arctic 4...");
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
                    "L'impact de la chute de glace Arctic 4 est deja actif.");
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
                "Arctic 4 : explosion de la chute de glace reactivee.");
            InstallerCore.Report(progress,
                "La chute de glace Arctic 4 produit de nouveau son impact historique.");
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
                @"(?m)^(?<indent>[ \t]*)//[ \t]*MakeExplosion\s*"
                + @"\(\s*FRM\s*,\s*5000000\s*,\s*3500\s*\)\s*;"
                + @"[^\r\n]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Explosion dormante de la chute de glace Arctic 4 introuvable.");
            text = dormant.Replace(text, match =>
                match.Groups["indent"].Value
                + "MakeExplosion(FRM, 5000000, 3500);", 1);
            return ansi.GetBytes(text);
        }

        private static bool IsPatched(string text)
        {
            return Regex.IsMatch(text,
                @"OnSignal\s*\(\s*1\s*\)\s*\{[\s\S]{0,220}"
                + @"MakeExplosion\s*\(\s*FRM\s*,\s*5000000\s*,\s*3500\s*\)\s*;"
                + @"[\s\S]{0,140}SetActorState\s*\(\s*Ulomek\s*,\s*1\s*\)\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsPatched(text))
                throw new InvalidDataException(
                    "Sequence d'impact Arctic 4 incomplete.");
            if (Regex.Matches(text,
                    @"(?m)^[ \t]*MakeExplosion\s*\(\s*FRM\s*,\s*5000000\s*,\s*3500\s*\)\s*;",
                    RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(
                    "Nombre inattendu d'explosions actives pour la chute de glace Arctic 4.");
            Require(text,
                @"FRM_FindFrame\s*\(\s*Ulomek\s*,\s*""ulomek_4""\s*\)",
                "Le fragment officiel ulomek_4 n'est plus cible par le script.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry,
                    "dummy_bouchni", "R_Arc3_bouchni.scr"))
                throw new InvalidDataException(
                    "Liaison officielle de la chute de glace Arctic 4 absente.");
            ValidateAsset(gamePath, ScenePath, "dummy_bouchni");
            ValidateAsset(gamePath, ActorsPath, "ulomek_4");
        }

        private static void ValidateAsset(
            string gamePath, string relative, string marker)
        {
            string text = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, relative, MissionArchives)));
            if (text.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Element Arctic 4 absent de " + relative + " : " + marker + ".");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Arctic 4 trop court.");
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
                    "Registre de scripts Arctic 4 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Arctic 4.");
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
