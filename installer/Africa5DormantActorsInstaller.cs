using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa5DormantActorsInstaller
    {
        private const string GuardScriptPath =
            "Scripts/AFRICA5/AF4_43.scr";
        private const string FaceScriptPath =
            "Scripts/AFRICA5/AF4_faceassigner.scr";
        private const string StorageScriptPath =
            "Scripts/AFRICA5/AF4_sklad01.scr";
        private const string RegistryPath =
            "Missions/AFRICA5/scripts.dta";
        private const string ActorsPath =
            "Missions/AFRICA5/actors.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] guard = ReadSource(ResolveSource(
                gamePath, GuardScriptPath, ScriptArchives));
            byte[] patchedGuard = PatchGuard(guard);
            if (BytesEqual(guard, patchedGuard))
                throw new InvalidDataException(
                    "Les evenements du garde 43 d'Africa 5 semblent deja actifs.");
            ValidateGuard(patchedGuard);
            if (!BytesEqual(patchedGuard, PatchGuard(patchedGuard)))
                throw new InvalidDataException(
                    "La restauration du garde 43 d'Africa 5 n'est pas idempotente.");

            byte[] faces = ReadSource(ResolveSource(
                gamePath, FaceScriptPath, ScriptArchives));
            byte[] patchedFaces = PatchFaces(faces);
            if (BytesEqual(faces, patchedFaces))
                throw new InvalidDataException(
                    "Le visage d'AF4_10 semble deja restaure.");
            ValidateFaces(patchedFaces);
            if (!BytesEqual(patchedFaces, PatchFaces(patchedFaces)))
                throw new InvalidDataException(
                    "La restauration du visage d'AF4_10 n'est pas idempotente.");

            byte[] storage = ReadSource(ResolveSource(
                gamePath, StorageScriptPath, ScriptArchives));
            byte[] patchedStorage = PatchStorageVoice(storage);
            if (BytesEqual(storage, patchedStorage))
                throw new InvalidDataException(
                    "L'alerte vocale d'AF4_sklad01 semble deja restauree.");
            ValidateStorageVoice(patchedStorage);
            if (!BytesEqual(
                    patchedStorage, PatchStorageVoice(patchedStorage)))
                throw new InvalidDataException(
                    "La restauration vocale d'AF4_sklad01 n'est pas idempotente.");

            ValidateAssets(gamePath);
            return "Africa 5 verifiee : le garde cache 43 recoit de nouveau "
                + "les alertes, AF4_10 retrouve son visage officiel et le "
                + "garde du magasin son alerte vocale.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string guard = InstallerCore.SafeGameTarget(
                    gamePath, GuardScriptPath);
                string faces = InstallerCore.SafeGameTarget(
                    gamePath, FaceScriptPath);
                string storage = InstallerCore.SafeGameTarget(
                    gamePath, StorageScriptPath);
                if (!File.Exists(guard) || !File.Exists(faces)
                    || !File.Exists(storage)) return false;
                ValidateGuard(File.ReadAllBytes(guard));
                ValidateFaces(File.ReadAllBytes(faces));
                ValidateStorageVoice(File.ReadAllBytes(storage));
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
                "Restauration du garde cache et du visage dormant d'Africa 5...");
            ValidateAssets(gamePath);
            bool changed = InstallOne(
                gamePath, GuardScriptPath, PatchGuard, ValidateGuard,
                journal, prepared);
            changed |= InstallOne(
                gamePath, FaceScriptPath, PatchFaces, ValidateFaces,
                journal, prepared);
            changed |= InstallOne(
                gamePath, StorageScriptPath, PatchStorageVoice,
                ValidateStorageVoice, journal, prepared);
            if (!changed)
            {
                InstallerCore.Report(progress,
                    "Le garde 43, le visage d'AF4_10 et l'alerte du magasin "
                    + "sont deja restaures.");
                return;
            }

            InstallerCore.Log(
                "Africa 5 : evenements d'AF4_43, visage e_f0w1 d'AF4_10 "
                + "et alerte vocale d'AF4_sklad01 restaures.");
            InstallerCore.Report(progress,
                "Le garde cache 43 reagit de nouveau aux alertes et "
                + "AF4_10 retrouve son visage historique; le garde du "
                + "magasin emet aussi son alerte d'origine.");
        }

        private static bool InstallOne(
            string gamePath, string relative, Func<byte[], byte[]> patch,
            Action<byte[]> validate, StateJournal journal,
            HashSet<string> prepared)
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
                journal.RecordHash(
                    relative, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            return true;
        }

        private static byte[] PatchGuard(byte[] data)
        {
            return ActivateLine(data,
                @"HUMAN_SetEvents\s*\(\s*true\s*\)\s*;",
                "evenements du garde AF4_43");
        }

        private static byte[] PatchFaces(byte[] data)
        {
            return ActivateLine(data,
                @"FRM_FindFrame\s*\(\s*act\s*,\s*""AF4_10""\s*\)\s*;"
                + @"\s*FRM_SwitchFaceTexture\s*\(\s*act\s*,\s*""e_f0w1""\s*\)\s*;",
                "visage feminin d'AF4_10");
        }

        private static byte[] PatchStorageVoice(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = StorageVoiceRegex();
            if (active.Matches(text).Count == 1) return data;
            if (active.Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Alerte vocale ambigue dans AF4_sklad01.scr.");

            Regex marker = new Regex(
                @"(?m)^(?<indent>[ \t]*)if\s*\(\s*Atype\s*==\s*2\s*\)\s*\{",
                RegexOptions.IgnoreCase);
            if (marker.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Point de restauration de l'alerte AF4_sklad01 introuvable.");
            string eol = text.IndexOf("\r\n", StringComparison.Ordinal) >= 0
                ? "\r\n" : "\n";
            string block = "if(!played){" + eol
                + "  PlaySound(9, 36);" + eol
                + "  Delay(1000);" + eol
                + "  played = 1;" + eol
                + "}" + eol + eol;
            text = marker.Replace(text, block + "$&", 1);
            return ansi.GetBytes(text);
        }

        private static Regex StorageVoiceRegex()
        {
            return new Regex(
                @"if\s*\(\s*!played\s*\)\s*\{[\s\S]{0,100}?"
                + @"PlaySound\s*\(\s*9\s*,\s*36\s*\)\s*;"
                + @"[\s\S]{0,100}?Delay\s*\(\s*1000\s*\)\s*;"
                + @"[\s\S]{0,100}?played\s*=\s*1\s*;[\s\S]{0,40}?\}",
                RegexOptions.IgnoreCase);
        }

        private static byte[] ActivateLine(
            byte[] data, string expression, string description)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = new Regex(
                @"(?m)^[ \t]*" + expression
                + @"[ \t]*(?://[^\r\n]*)?\r?$",
                RegexOptions.IgnoreCase);
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>"
                + expression + @")(?<tail>[ \t]*(?://[^\r\n]*)?)\r?$",
                RegexOptions.IgnoreCase);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == 1 && dormantCount == 0) return data;
            if (activeCount != 0 || dormantCount != 1)
                throw new InvalidDataException(
                    "Instruction Africa 5 absente ou ambigue : "
                    + description + ".");
            text = dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value
                    + match.Groups["tail"].Value;
            }, 1);
            return ansi.GetBytes(text);
        }

        private static void ValidateGuard(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireOne(text,
                @"HUMAN_Suspend\s*\(\s*true\s*\)\s*;"
                + @"[\s\S]{0,100}?HUMAN_SetEvents\s*\(\s*true\s*\)\s*;"
                + @"[\s\S]{0,100}?goto\s+END\s*;",
                "La reception des alertes d'AF4_43 est incomplete.");
            RequireOne(text,
                @"Whenever\s+player\s*\(\s*_PlayerInRange\s*\(\s*15\s*\)",
                "Le reveil local d'AF4_43 a ete altere.");
        }

        private static void ValidateFaces(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            RequireOne(text,
                @"FRM_FindFrame\s*\(\s*act\s*,\s*""AF4_10""\s*\)\s*;"
                + @"\s*FRM_SwitchFaceTexture\s*\(\s*act\s*,\s*""e_f0w1""\s*\)\s*;",
                "Le visage e_f0w1 d'AF4_10 est absent ou duplique.");
            RequireOne(text,
                @"FRM_FindFrame\s*\(\s*act\s*,\s*""AF4_12""\s*\)\s*;"
                + @"\s*FRM_SwitchFaceTexture\s*\(\s*act\s*,\s*""e_f0w2""\s*\)\s*;",
                "Le visage feminin de reference AF4_12 a ete altere.");
        }

        private static void ValidateStorageVoice(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (StorageVoiceRegex().Matches(text).Count != 1)
                throw new InvalidDataException(
                    "L'alerte vocale d'AF4_sklad01 est incomplete.");
            RequireOne(text,
                @"INTEGER\s+played\s*=\s*0\s*;",
                "Le verrou de l'alerte vocale d'AF4_sklad01 est absent.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            foreach (string actor in new[] {
                "AF4_10", "AF4_43", "AF4_sklad01"
            })
                if (!HasBinding(registry, actor, actor + ".scr"))
                    throw new InvalidDataException(
                        "Liaison Africa 5 absente pour " + actor + ".");
            if (!HasBinding(registry,
                    "dummy_face_assigner", "AF4_faceassigner.scr"))
                throw new InvalidDataException(
                    "Le distributeur de visages Africa 5 n'est plus relie.");

            byte[] actors = ReadSource(ResolveSource(
                gamePath, ActorsPath, MissionArchives));
            foreach (string actor in new[] {
                "AF4_10", "AF4_43", "AF4_sklad01"
            })
                if (CountAscii(actors, actor) < 1)
                    throw new InvalidDataException(
                        "Acteur Africa 5 absent : " + actor + ".");

            if (!ArchiveContains(
                    Path.Combine(gamePath, "Maps.dta"), "MAPS/e_f0w1.bmp"))
                throw new InvalidDataException(
                    "La texture officielle e_f0w1.bmp est absente.");

            string reference = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath,
                    "Scripts/AFRICA5/AF4_sklad04.scr", ScriptArchives)));
            RequireOne(reference,
                @"PlaySound\s*\(\s*9\s*,\s*41\s*\)\s*;",
                "Le canal vocal de reference du magasin est absent.");
        }

        private static bool ArchiveContains(string archivePath, string relative)
        {
            if (!File.Exists(archivePath))
                throw new FileNotFoundException(
                    "Archive officielle manquante.", archivePath);
            using (DtaArchive archive = new DtaArchive(archivePath))
                foreach (DtaEntry entry in archive.Entries)
                    if (String.Equals(
                        entry.Name.Replace((char)92, '/'), relative,
                        StringComparison.OrdinalIgnoreCase))
                        return true;
            return false;
        }

        private static void RequireOne(
            string text, string pattern, string message)
        {
            if (Regex.Matches(
                    text, pattern, RegexOptions.IgnoreCase).Count != 1)
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 5 trop court.");
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
                    "Registre de scripts Africa 5 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            uint rawTotal = BitConverter.ToUInt32(data, offset + 2);
            if (marker != 1 || rawTotal < 7 || rawTotal > Int32.MaxValue)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 5.");
            int total = (int)rawTotal;
            if (offset > data.Length - total
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ tronque dans le registre Africa 5.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
        }

        private static int CountAscii(byte[] data, string wanted)
        {
            byte[] needle = Encoding.ASCII.GetBytes(wanted);
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
                    "Donnee officielle Africa 5 introuvable : " + relative);
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
