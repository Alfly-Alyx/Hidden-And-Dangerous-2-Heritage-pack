using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class CoLibye1DormantDialoguesInstaller
    {
        private sealed class VoiceSpec
        {
            public string Actor;
            public int Id;
        }

        private sealed class DialogueSpec
        {
            public string ActorA;
            public string ActorB;
            public string VariableA;
            public string VariableB;
            public string Controller;
            public int EndSignal;
            public VoiceSpec[] Voices;
        }

        private sealed class ScriptChange
        {
            public string Relative;
            public string Target;
            public byte[] Original;
            public byte[] Patched;
        }

        private static readonly DialogueSpec[] Dialogues = {
            new DialogueSpec {
                ActorA = "AF1_08",
                ActorB = "AF1_12",
                VariableA = "af08",
                VariableB = "af12",
                Controller = "AF1_08_AF1_12_speech",
                EndSignal = 3,
                Voices = new[] {
                    Voice("af12", 52990001),
                    Voice("af08", 52990002),
                    Voice("af08", 52990003),
                    Voice("af08", 52990004),
                    Voice("af12", 52990005),
                    Voice("af12", 52990006),
                    Voice("af12", 52990007),
                    Voice("af12", 52990008),
                    Voice("af12", 52990009),
                    Voice("af08", 52990010),
                    Voice("af12", 52990011)
                }
            },
            new DialogueSpec {
                ActorA = "AF1_33",
                ActorB = "AF1_34",
                VariableA = "af33",
                VariableB = "af34",
                Controller = "AF1_33_AF1_34_speech",
                EndSignal = 2,
                Voices = new[] {
                    Voice("af33", 52990024),
                    Voice("af34", 52990025),
                    Voice("af33", 52990026),
                    Voice("af34", 52990027),
                    Voice("af33", 52990028),
                    Voice("af33", 52990029),
                    Voice("af34", 52990030),
                    Voice("af34", 52990031),
                    Voice("af33", 52990032)
                }
            }
        };

        private static readonly string[] RegistryPaths = {
            "Missions/Co_Libye1/MpScripts.dta",
            "Missions/Co_Libye1/Scripts.dta"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (DialogueSpec dialogue in Dialogues)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, CooperativePath(dialogue), ScriptArchives));
                byte[] patched = PatchScript(dialogue, original);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "Le dialogue " + dialogue.Controller
                        + " semble deja actif dans l'archive officielle.");
                ValidatePatched(dialogue, patched);
                if (!BytesEqual(patched, PatchScript(dialogue, patched)))
                    throw new InvalidDataException(
                        "La restauration du dialogue " + dialogue.Controller
                        + " n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Libye 1 cooperative verifiee : deux conversations officielles "
                + "completes, soit vingt repliques, peuvent etre restaurees.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (DialogueSpec dialogue in Dialogues)
                {
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, CooperativePath(dialogue));
                    if (!File.Exists(target)) return false;
                    ValidatePatched(dialogue, File.ReadAllBytes(target));
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
                "Restauration de deux conversations dans Libye 1 cooperative...");
            ValidateAssets(gamePath);
            List<ScriptChange> changes = new List<ScriptChange>();
            foreach (DialogueSpec dialogue in Dialogues)
            {
                string relative = CooperativePath(dialogue);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target)
                    : ReadSource(ResolveSource(gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(dialogue, original);
                ValidatePatched(dialogue, patched);
                changes.Add(new ScriptChange {
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

            InstallerCore.Log("Libye 1 cooperative : " + written
                + " controleurs de dialogue restaures, vingt repliques disponibles.");
            InstallerCore.Report(progress,
                "Deux conversations completes de Libye 1 cooperative sont restaurees.");
        }

        private static VoiceSpec Voice(string actor, int id)
        {
            return new VoiceSpec { Actor = actor, Id = id };
        }

        private static string CooperativePath(DialogueSpec dialogue)
        {
            return "Scripts/Co_Libye1/" + dialogue.Controller + ".scr";
        }

        private static string SoloPath(DialogueSpec dialogue)
        {
            return "Scripts/Libye1/" + dialogue.Controller + ".scr";
        }

        private static byte[] PatchScript(DialogueSpec dialogue, byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            text = UncommentExpected(
                text, GuardPattern(dialogue), dialogue.Voices.Length,
                "conditions du dialogue " + dialogue.Controller);
            foreach (VoiceSpec voice in dialogue.Voices)
                text = UncommentExpected(
                    text, SpeechPattern(voice), 1,
                    "replique " + voice.Id);
            return ansi.GetBytes(text);
        }

        private static string UncommentExpected(
            string text, string statementPattern, int expected,
            string description)
        {
            Regex active = ActiveLineRegex(statementPattern);
            Regex dormant = DormantLineRegex(statementPattern);
            int activeCount = active.Matches(text).Count;
            int dormantCount = dormant.Matches(text).Count;
            if (activeCount == expected && dormantCount == 0) return text;
            if (activeCount + dormantCount != expected)
                throw new InvalidDataException(
                    "Etat absent ou ambigu : " + description + ".");
            return dormant.Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            });
        }

        private static string GuardPattern(DialogueSpec dialogue)
        {
            return @"If[ \t]*\([ \t]*\(_ACTOR_GetState[ \t]*"
                + @"\([ \t]*" + Regex.Escape(dialogue.VariableA)
                + @"[ \t]*\)[ \t]*"
                + @"AND[ \t]+_ACTOR_GetState[ \t]*\([ \t]*"
                + Regex.Escape(dialogue.VariableB)
                + @"[ \t]*\)[ \t]*\)[ \t]*"
                + @"==[ \t]*1[ \t]*\)";
        }

        private static string SpeechPattern(VoiceSpec voice)
        {
            return @"\{[ \t]*FRM_MorphSpeechDelayed[ \t]*\([ \t]*"
                + Regex.Escape(voice.Actor) + @"[ \t]*,[ \t]*"
                + voice.Id + @"[ \t]*,[ \t]*2[ \t]*,[ \t]*60"
                + @"[ \t]*\)[ \t]*;[ \t]*Delay[ \t]*\([ \t]*10"
                + @"[ \t]*\)[ \t]*;[ \t]*\}";
        }

        private static Regex ActiveLineRegex(string statementPattern)
        {
            return new Regex(
                @"(?m)^[ \t]*" + statementPattern + @"[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static Regex DormantLineRegex(string statementPattern)
        {
            return new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>"
                + statementPattern + @")[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(
            DialogueSpec dialogue, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveLineRegex(GuardPattern(dialogue))
                    .Matches(text).Count != dialogue.Voices.Length
                || DormantLineRegex(GuardPattern(dialogue))
                    .Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Conditions de dialogue incompletes dans "
                    + dialogue.Controller + ".");

            Match start = Regex.Match(
                text, @"(?im)^[ \t]*Label[ \t]+start[ \t]*:");
            if (!start.Success)
                throw new InvalidDataException(
                    "Debut du dialogue absent : " + dialogue.Controller + ".");
            int cursor = start.Index + start.Length;
            foreach (VoiceSpec voice in dialogue.Voices)
            {
                Regex active = ActiveLineRegex(SpeechPattern(voice));
                if (active.Matches(text).Count != 1
                    || DormantLineRegex(SpeechPattern(voice))
                        .Matches(text).Count != 0)
                    throw new InvalidDataException(
                        "Replique incomplete : " + voice.Id + ".");
                Match ordered = active.Match(text, cursor);
                if (!ordered.Success)
                    throw new InvalidDataException(
                        "Ordre des repliques altere dans "
                        + dialogue.Controller + ".");
                cursor = ordered.Index + ordered.Length;
            }

            Require(text,
                @"OnSignal[ \t]*\([ \t]*1[ \t]*\)[\s\S]{0,180}"
                + @"sync[ \t]*=[ \t]*sync[ \t]*\+[ \t]*1[ \t]*;"
                + @"[\s\S]{0,100}sync[ \t]*==[ \t]*2",
                "La synchronisation du dialogue a ete alteree : "
                    + dialogue.Controller + ".");
            Require(text,
                @"OnSignal[ \t]*\([ \t]*2[ \t]*\)[\s\S]{0,260}"
                + @"EndScript[ \t]*\([ \t]*\)[ \t]*;",
                "L'interruption du dialogue a ete alteree : "
                    + dialogue.Controller + ".");
            foreach (string actor in new[] {
                dialogue.VariableA,
                dialogue.VariableB
            })
                Require(text,
                    @"SendSignal[ \t]*\([ \t]*" + Regex.Escape(actor)
                    + @"[ \t]*,[ \t]*" + dialogue.EndSignal
                    + @"[ \t]*\)[ \t]*;",
                    "Le retour de fin de dialogue manque pour "
                        + dialogue.Controller + ".");
        }

        private static void ValidateAssets(string gamePath)
        {
            foreach (string registryPath in RegistryPaths)
            {
                byte[] registry = ReadSource(ResolveSource(
                    gamePath, registryPath, MissionArchives));
                foreach (DialogueSpec dialogue in Dialogues)
                {
                    foreach (string actor in new[] {
                        dialogue.ActorA, dialogue.ActorB, dialogue.Controller
                    })
                        if (!HasBinding(registry, actor, actor + ".scr"))
                            throw new InvalidDataException(
                                "Liaison cooperative absente dans "
                                + registryPath + " : " + actor + ".");
                }
            }

            byte[] actors = ReadSource(ResolveSource(
                gamePath, "Missions/Co_Libye1/actors.bin",
                MissionArchives));
            foreach (DialogueSpec dialogue in Dialogues)
            {
                foreach (string actor in new[] {
                    dialogue.ActorA, dialogue.ActorB, dialogue.Controller
                })
                    if (!ContainsNullTerminated(actors, actor))
                        throw new InvalidDataException(
                            "Acteur de dialogue Libye 1 absent : "
                            + actor + ".");

                ValidateParticipants(gamePath, dialogue);
                byte[] solo = ReadSource(ResolveSource(
                    gamePath, SoloPath(dialogue), ScriptArchives));
                ValidatePatched(dialogue, solo);
            }

            ValidateLanguageResources(gamePath);
        }

        private static void ValidateParticipants(
            string gamePath, DialogueSpec dialogue)
        {
            foreach (string actor in new[] {
                dialogue.ActorA, dialogue.ActorB
            })
            {
                string relative = "Scripts/Co_Libye1/" + actor + ".scr";
                string text = Encoding.GetEncoding(1252).GetString(
                    ReadSource(ResolveSource(
                        gamePath, relative, ScriptArchives)));
                Require(text,
                    @"SendSignal[ \t]*\([ \t]*speech[ \t]*,[ \t]*1"
                    + @"[ \t]*\)[ \t]*;",
                    "Le depart du dialogue manque chez " + actor + ".");
                Require(text,
                    @"OnSignal[ \t]*\([ \t]*" + dialogue.EndSignal
                    + @"[ \t]*\)",
                    "Le retour de dialogue manque chez " + actor + ".");
                Require(text,
                    @"OnAlarm[ \t]*\([ \t]*\)[\s\S]{0,420}"
                    + @"SendSignal[ \t]*\([ \t]*speech[ \t]*,[ \t]*2",
                    "L'interruption sur alarme manque chez " + actor + ".");
                Require(text,
                    @"OnDeath[ \t]*\([ \t]*\)[\s\S]{0,180}"
                    + @"SendSignal[ \t]*\([ \t]*speech[ \t]*,[ \t]*2",
                    "L'interruption sur mort manque chez " + actor + ".");
            }
        }

        private static void ValidateLanguageResources(string gamePath)
        {
            HashSet<string> required = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            foreach (DialogueSpec dialogue in Dialogues)
                foreach (VoiceSpec voice in dialogue.Voices)
                {
                    required.Add("Sounds/" + voice.Id + ".wav");
                    required.Add("Tables/Dabing/" + voice.Id + ".dat");
                }

            HashSet<string> found = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase);
            string[] languageArchives = Directory.GetFiles(
                gamePath, "Lang*.dta");
            foreach (string archivePath in languageArchives)
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                    {
                        string name = entry.Name.Replace((char)92, '/');
                        if (required.Contains(name) && entry.Size > 0)
                            found.Add(name);
                    }
            foreach (string name in required)
                if (!found.Contains(name))
                    throw new InvalidDataException(
                        "Ressource vocale Libye 1 absente ou vide : "
                        + name + ".");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Libye 1 trop court.");
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
                    "Champ invalide dans le registre Libye 1.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Libye 1.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, (int)rawLength - 7);
            offset += (int)rawLength;
            return value;
        }

        private static bool ContainsNullTerminated(byte[] data, string value)
        {
            byte[] needle = Encoding.GetEncoding(1252).GetBytes(value + "\0");
            for (int start = 0; start <= data.Length - needle.Length; start++)
            {
                int index = 0;
                while (index < needle.Length
                    && ToLowerAscii(data[start + index])
                        == ToLowerAscii(needle[index]))
                    index++;
                if (index == needle.Length) return true;
            }
            return false;
        }

        private static byte ToLowerAscii(byte value)
        {
            return value >= (byte)'A' && value <= (byte)'Z'
                ? (byte)(value + 32) : value;
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
