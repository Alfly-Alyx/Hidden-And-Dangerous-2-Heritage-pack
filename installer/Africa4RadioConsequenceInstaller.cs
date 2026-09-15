using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Africa4RadioConsequenceInstaller
    {
        private const string OrganizerPath =
            "Scripts/AFRICA4/AF3b_organizer.scr";
        private const string RadioOperatorPath =
            "Scripts/AFRICA3/AF3a_19.scr";
        private const string DiaryPath =
            "Scripts/AFRICA4/AF3b_dummy_diary.scr";
        private const string RegistryPath =
            "Missions/AFRICA4/Scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] StandardSoldiers = {
            "AF3b_11", "AF3b_14", "AF3b_17", "AF3b_20", "AF3b_23", "AF3b_31",
            "AF3b_12", "AF3b_15", "AF3b_18", "AF3b_21", "AF3b_24", "AF3b_32",
            "AF3b_13", "AF3b_16", "AF3b_19", "AF3b_22", "AF3b_25", "AF3b_33"
        };

        private static readonly Regex ForcedWarning = new Regex(
            @"(?m)^[ \t]*odvysilali[ \t]*=[ \t]*1[ \t]*;[ \t]*(?:\r?\n)?",
            RegexOptions.IgnoreCase);

        public static string ValidateOnly(string gamePath)
        {
            byte[] original = ReadSource(ResolveSource(
                gamePath, OrganizerPath, ScriptArchives));
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "La consequence du choix radio d'Africa 3 semble deja restauree dans les archives.");
            ValidatePatched(patched);
            if (!BytesEqual(patched, PatchScript(patched)))
                throw new InvalidDataException(
                    "La restauration du choix radio Africa 4 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Africa 4 verifie : l'attaque distingue de nouveau le cas ou "
                + "le radio-operateur d'Africa 3 a prevenu les renforts.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(
                    gamePath, OrganizerPath);
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
                "Restauration de la consequence du choix radio dans Africa 4...");
            DormantSource source = ResolveSource(
                gamePath, OrganizerPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(
                gamePath, OrganizerPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Consequence du choix radio Africa 3 deja active dans Africa 4.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, OrganizerPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    OrganizerPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Africa 4 : branche avertie/non avertie restauree depuis le choix radio d'Africa 3.");
            InstallerCore.Report(progress,
                "Le choix radio d'Africa 3 modifie de nouveau l'attaque d'Africa 4.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            int forced = ForcedWarning.Matches(text).Count;
            if (forced == 0)
            {
                ValidatePatched(data);
                return data;
            }
            if (forced != 1)
                throw new InvalidDataException(
                    "Structure inattendue de la branche radio dans Africa 4.");
            return ansi.GetBytes(ForcedWarning.Replace(text, String.Empty));
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!Regex.IsMatch(text,
                @"INTEGER\s+odvysilali\s*=\s*_LoadGameValue\s*\(\s*20\s*\)\s*;",
                RegexOptions.IgnoreCase)
                || ForcedWarning.IsMatch(text))
                throw new InvalidDataException(
                    "La valeur sauvegardee du choix radio n'est pas respectee.");

            Require(text, @"if\s*\(\s*odvysilali\s*\)[\s\S]{0,120}signal1\s*=\s*20\s*;[\s\S]{0,80}signal2\s*=\s*1\s*;",
                "Branche des renforts avertis incomplete.");
            Require(text, @"else\s*\{[\s\S]{0,120}signal1\s*=\s*21\s*;[\s\S]{0,80}signal2\s*=\s*2\s*;",
                "Branche des renforts non avertis incomplete.");
            Require(text, @"if\s*\(\s*odvysilali\s*\)[\s\S]{0,100}zpozdeni\s*=\s*30000\s*;[\s\S]{0,100}else[\s\S]{0,80}zpozdeni\s*=\s*20000\s*;",
                "Temporisations alternatives des renforts absentes.");
        }

        private static void ValidateAssets(string gamePath)
        {
            string radioOperator = ReadText(ResolveSource(
                gamePath, RadioOperatorPath, ScriptArchives));
            Require(radioOperator,
                @"SaveGameValue\s*\(\s*20\s*,\s*0\s*\)",
                "Initialisation du choix radio absente dans Africa 3.");
            Require(radioOperator,
                @"SaveGameValue\s*\(\s*20\s*,\s*1\s*\)",
                "Validation de l'alerte radio absente dans Africa 3.");

            string diary = ReadText(ResolveSource(
                gamePath, DiaryPath, ScriptArchives));
            Require(diary,
                @"_LoadGameValue\s*\(\s*20\s*\)",
                "Le journal Africa 4 ne conserve pas la consequence radio.");
            Require(diary,
                @"if\s*\(\s*odvisilali\s*\)[\s\S]{0,120}AddDiaryText\s*\(\s*4153\s*\)[\s\S]{0,120}else[\s\S]{0,120}AddDiaryText\s*\(\s*4154\s*\)",
                "Les deux textes de journal Africa 4 ne sont pas complets.");

            foreach (string driver in new[] { "AF3b_01", "AF3b_06" })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA4/" + driver + ".scr", ScriptArchives));
                RequireHandler(script, 20, driver);
                RequireHandler(script, 21, driver);
            }

            foreach (string soldier in StandardSoldiers)
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA4/" + soldier + ".scr", ScriptArchives));
                RequireHandler(script, 1, soldier);
                RequireHandler(script, 2, soldier);
            }

            foreach (string tanker in new[] {
                "AF3b_tankista01", "AF3b_tankista04"
            })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA4/" + tanker + ".scr", ScriptArchives));
                RequireHandler(script, 1, tanker);
                RequireHandler(script, 2, tanker);
            }

            foreach (string reserve in new[] {
                "AF3b_26", "AF3b_27", "AF3b_28", "AF3b_29", "AF3b_30"
            })
            {
                string script = ReadText(ResolveSource(gamePath,
                    "Scripts/AFRICA4/" + reserve + ".scr", ScriptArchives));
                Require(script,
                    @"_LoadGameValue\s*\(\s*20\s*\)[\s\S]{0,300}if\s*\(\s*!\s*odvysilali\s*\)",
                    reserve + " ne respecte plus la variante non avertie.");
                RequireHandler(script, 1, reserve);
            }

            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry,
                "dummy_organizer", "AF3b_organizer.scr"))
                throw new InvalidDataException(
                    "Liaison officielle de l'organisateur Africa 4 absente.");
        }

        private static void RequireHandler(
            string text, int signal, string actor)
        {
            Require(text,
                @"OnSignal\s*\(\s*" + signal + @"\s*\)",
                "Signal " + signal + " absent pour " + actor + ".");
        }

        private static void Require(
            string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 4 trop court.");
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
                    "Registre de scripts Africa 4 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 4.");
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

        private static string ReadText(DormantSource source)
        {
            return Encoding.GetEncoding(1252).GetString(ReadSource(source));
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