using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal sealed class DormantSource
    {
        public string ArchivePath;
        public int EntryIndex;
    }

    internal static class DormantContentInstaller
    {
        private const string ScriptPath = "Scripts/ARCTIC1/R_Arc1A_rebel.scr";
        private const string DialogueScriptPath =
            "Scripts/AFRICA3/AF3a_rozhovor_05.scr";
        private const string Africa3RegistryPath =
            "Missions/AFRICA3/Scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            DormantSource source = ResolveSource(gamePath, ScriptPath, ScriptArchives);
            byte[] original = ReadSource(source);
            byte[] patched = PatchScript(original);
            if (BytesEqual(original, patched))
                throw new InvalidDataException(
                    "Les sequences Arctic 1 semblent deja reactives dans les archives.");
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            byte[] dialogueOriginal = ReadSource(ResolveSource(
                gamePath, DialogueScriptPath, ScriptArchives));
            byte[] dialoguePatched = PatchDialogue(dialogueOriginal);
            if (BytesEqual(dialogueOriginal, dialoguePatched))
                throw new InvalidDataException(
                    "Les deux repliques Africa 3 semblent deja corrigees.");
            ValidateDialoguePatched(dialoguePatched);
            if (!BytesEqual(dialoguePatched, PatchDialogue(dialoguePatched)))
                throw new InvalidDataException(
                    "Le correctif des repliques Africa 3 n'est pas idempotent.");
            ValidateDialogueAssets(gamePath, dialogueOriginal);
            return "Vestiges narratifs verifies : 2 sequences de guidage Arctic 1 "
                + "et 2 identifiants de voix Africa 3 reparables.";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Reactivation des sequences de guidage Arctic 1...");
            DormantSource source = ResolveSource(gamePath, ScriptPath, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, ScriptPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = PatchScript(original);
            ValidatePatched(patched);
            ValidateAssets(gamePath);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Sequences Arctic 1 deja actives; aucune modification.");
            }
            else
            {
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
                    "Vestiges narratifs : 2 sequences Arctic 1 reactives.");
                InstallerCore.Report(progress,
                    "Deux sequences de guidage Arctic 1 ont ete reactives.");
            }
            InstallDialogue(gamePath, journal, prepared, progress);
        }

        private static void InstallDialogue(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Correction de deux identifiants de voix dans Africa 3...");
            DormantSource source = ResolveSource(
                gamePath, DialogueScriptPath, ScriptArchives);
            byte[] archived = ReadSource(source);
            string target = InstallerCore.SafeGameTarget(
                gamePath, DialogueScriptPath);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : archived;
            byte[] patched = PatchDialogue(original);
            ValidateDialoguePatched(patched);
            if (!BytesEqual(patched, PatchDialogue(patched)))
                throw new InvalidDataException(
                    "Le correctif des repliques Africa 3 n'est pas idempotent.");
            ValidateDialogueAssets(gamePath, archived);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress,
                    "Identifiants de voix Africa 3 deja corriges; aucune modification.");
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, DialogueScriptPath, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(
                    DialogueScriptPath, CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Log(
                "Africa 3 : identifiants de voix 07991601 et 07991604 corriges.");
            InstallerCore.Report(progress,
                "Deux identifiants de voix errones ont ete corriges dans Africa 3.");
        }

        private static byte[] PatchDialogue(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = PatchDialogueId(text, "079915601", "07991601");
            text = PatchDialogueId(text, "079915604", "07991604");
            return ansi.GetBytes(text);
        }

        private static string PatchDialogueId(
            string text, string wrongId, string correctId)
        {
            Regex wrong = DialogueCallRegex(wrongId);
            Regex correct = DialogueCallRegex(correctId);
            int wrongCount = wrong.Matches(text).Count;
            int correctCount = correct.Matches(text).Count;
            if (wrongCount == 0 && correctCount == 1) return text;
            if (wrongCount != 1 || correctCount != 0)
                throw new InvalidDataException(
                    "Structure inattendue de la replique Africa 3 : "
                    + wrongId + " -> " + correctId + ".");
            return wrong.Replace(text, "${1}" + correctId + "${2}", 1);
        }

        private static Regex DialogueCallRegex(string voiceId)
        {
            return new Regex(
                @"(?m)^(\s*FRM_MorphSpeechDelayed\s*\(\s*af02\s*,\s*)"
                + Regex.Escape(voiceId)
                + @"(\s*,\s*8\s*,\s*20\s*\)\s*;\s*)$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidateDialoguePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            foreach (string correctId in new[] { "07991601", "07991604" })
                if (DialogueCallRegex(correctId).Matches(text).Count != 1)
                    throw new InvalidDataException(
                        "Identifiant de voix Africa 3 non corrige : "
                        + correctId + ".");
            foreach (string wrongId in new[] { "079915601", "079915604" })
                if (DialogueCallRegex(wrongId).Matches(text).Count != 0)
                    throw new InvalidDataException(
                        "Ancien identifiant de voix Africa 3 encore present : "
                        + wrongId + ".");
            if (Regex.Matches(text, @"FRM_MorphSpeechDelayed\s*\(",
                    RegexOptions.IgnoreCase).Count != 16)
                throw new InvalidDataException(
                    "Nombre inattendu de repliques dans le dialogue Africa 3.");
        }

        private static void ValidateDialogueAssets(
            string gamePath, byte[] archivedDialogue)
        {
            string text = Encoding.GetEncoding(1252).GetString(archivedDialogue);
            foreach (string correctId in new[] { "07991601", "07991604" })
                if (!Regex.IsMatch(text,
                    @"(?m)^\s*//\s*AF3a_02\s+" + Regex.Escape(correctId)
                    + @"\s+NOSUB\b", RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Commentaire officiel de voix Africa 3 absent : "
                        + correctId + ".");
            if (DialogueCallRegex("079915601").Matches(text).Count != 1
                || DialogueCallRegex("079915604").Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Les deux erreurs commerciales de voix Africa 3 ne sont pas confirmees.");

            byte[] registry = ReadSource(ResolveSource(
                gamePath, Africa3RegistryPath, MissionArchives));
            if (!HasRegistryBinding(registry,
                "dummy_rozhovor_05", "AF3a_rozhovor_05.scr"))
                throw new InvalidDataException(
                    "Liaison officielle du dialogue Africa 3 absente.");
        }

        private static bool HasRegistryBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Africa 3 trop court.");
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
            if (offset < 0 || offset > data.Length - 6
                || BitConverter.ToUInt16(data, offset) != 1)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Africa 3.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Africa 3.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, (int)rawLength - 7);
            offset += (int)rawLength;
            return value;
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = PatchFlag(text, "SKIP_CSC3");
            text = PatchFlag(text, "SKIP_CSC4");
            return ansi.GetBytes(text);
        }

        private static string PatchFlag(string text, string name)
        {
            Regex active = new Regex(
                @"(?m)^(\s*integer\s+" + Regex.Escape(name)
                + @"\s*;\s*" + Regex.Escape(name) + @"\s*=\s*)0(\s*;[^\r\n]*)$",
                RegexOptions.IgnoreCase);
            if (active.Matches(text).Count == 1)
                return text;

            Regex disabled = new Regex(
                @"(?m)^(\s*integer\s+" + Regex.Escape(name)
                + @"\s*;\s*" + Regex.Escape(name) + @"\s*=\s*)99(\s*;[^\r\n]*)$",
                RegexOptions.IgnoreCase);
            MatchCollection matches = disabled.Matches(text);
            if (matches.Count != 1)
                throw new InvalidDataException(
                    "Structure inattendue du vestige Arctic 1 : " + name + ".");
            return disabled.Replace(text, "${1}0${2}", 1);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            foreach (string name in new[] { "SKIP_CSC3", "SKIP_CSC4" })
                if (!Regex.IsMatch(text,
                    @"integer\s+" + Regex.Escape(name) + @"\s*;\s*"
                    + Regex.Escape(name) + @"\s*=\s*0\s*;",
                    RegexOptions.IgnoreCase))
                    throw new InvalidDataException(
                        "Sequence Arctic 1 non reactivee : " + name + ".");

            string[] required = {
                "FRM_WatchTrack(K3, \"kamera 3\")",
                "FRM_WatchTrack(K4, \"kamera 4\")",
                "FRM_SetCameraFrame(Kanisternik)",
                "SendSignal(Roof, 1)",
                "SendSignal(kanisternik, 5)"
            };
            foreach (string marker in required)
                if (text.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Donnee de sequence Arctic 1 manquante : " + marker + ".");
        }

        private static void ValidateAssets(string gamePath)
        {
            ValidateAsset(gamePath, "MISSIONS/ARCTIC1/scene2.bin",
                new[] { "K3", "K3a", "K4", "K4a", "K4b",
                    "dummy_kanisternik_sit" });
            ValidateAsset(gamePath, "MISSIONS/ARCTIC1/tracks.dat",
                new[] { "kamera 3", "kamera 4", "kamera 4b" });
            ValidateAsset(gamePath, "MISSIONS/ARCTIC1/actors.bin",
                new[] { "Roof_walker", "Auti_BAD", "Kanisternik" });
        }

        private static void ValidateAsset(
            string gamePath, string relative, string[] markers)
        {
            DormantSource source = ResolveSource(
                gamePath, relative, MissionArchives);
            string text = Encoding.GetEncoding(1252).GetString(ReadSource(source));
            foreach (string marker in markers)
                if (text.IndexOf(marker, StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Element Arctic 1 manquant dans " + relative + " : "
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
