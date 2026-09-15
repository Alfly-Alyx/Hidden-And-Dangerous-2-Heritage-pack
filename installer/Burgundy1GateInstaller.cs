using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Burgundy1GateInstaller
    {
        private static readonly string[] ScriptPaths = {
            "Scripts/Burgundy1/bur1_04.scr",
            "Scripts/Co_Burgundy1/bur1_04.scr"
        };

        private static readonly string[] RegistryPaths = {
            "Missions/Burgundy1/Scripts.dta",
            "Missions/Co_Burgundy1/mpscripts.dta"
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (string relative in ScriptPaths)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, relative, ScriptArchives));
                byte[] patched = PatchScript(original);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "La barriere semble deja corrigee dans " + relative + ".");
                ValidatePatched(patched);
                if (!BytesEqual(patched, PatchScript(patched)))
                    throw new InvalidDataException(
                        "Le correctif de barriere Burgundy 1 n'est pas idempotent.");
            }
            ValidateAssets(gamePath);
            return "Burgundy 1 verifie : la barriere retrouve sa commande "
                + "officielle de fermeture et son garde son trajet de retour "
                + "en solo et en cooperation.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (string relative in ScriptPaths)
                {
                    string target = InstallerCore.SafeGameTarget(gamePath, relative);
                    if (!File.Exists(target)) return false;
                    ValidatePatched(File.ReadAllBytes(target));
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
                "Restauration de la barriere et du trajet de son garde Burgundy 1...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (string relative in ScriptPaths)
            {
                DormantSource source = ResolveSource(
                    gamePath, relative, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(original);
                ValidatePatched(patched);
                if (BytesEqual(original, patched)) continue;

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
                changed++;
            }
            InstallerCore.Log(
                "Burgundy 1 : fermeture de barriere et retour du garde restaures dans "
                + changed + " variantes.");
            InstallerCore.Report(progress,
                "La barriere Burgundy 1 se referme et son garde rejoint de nouveau son poste apres le passage du camion.");
        }

        private static byte[] PatchScript(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            Regex active = new Regex(
                @"Delay\s*\(\s*20000\s*\)\s*;\s*SendSignal\s*\(\s*zavora\s*,\s*2\s*\)\s*;",
                RegexOptions.IgnoreCase);
            if (active.Matches(text).Count != 1)
            {
                Regex wrong = new Regex(
                    @"(Delay\s*\(\s*20000\s*\)\s*;\s*SendSignal\s*\(\s*zavora\s*,\s*)0(\s*\)\s*;)",
                    RegexOptions.IgnoreCase);
                if (wrong.Matches(text).Count != 1)
                    throw new InvalidDataException(
                        "Structure inattendue de la fermeture de barriere Burgundy 1.");
                text = wrong.Replace(text, "${1}2${2}", 1);
            }

            Regex activeMove = new Regex(
                @"(?m)^[ \t]*HUMAN_Move\s*\(\s*""04_01""\s*\)\s*;",
                RegexOptions.IgnoreCase);
            if (activeMove.Matches(text).Count != 1)
            {
                Regex dormantMove = new Regex(
                    @"(?m)^([ \t]*)//[ \t]*HUMAN_Move\s*\(\s*""04_01""\s*\)\s*;[ \t]*\r?$",
                    RegexOptions.IgnoreCase);
                if (dormantMove.Matches(text).Count != 1)
                    throw new InvalidDataException(
                        "Trajet historique du garde de barriere Burgundy 1 absent.");
                text = dormantMove.Replace(text, "${1}HUMAN_Move(\"04_01\");", 1);
            }

            return ansi.GetBytes(text);
        }

        private static void ValidatePatched(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!Regex.IsMatch(text,
                @"SendSignal\s*\(\s*zavora\s*,\s*1\s*\)\s*;[\s\S]{0,100}Delay\s*\(\s*20000\s*\)\s*;[\s\S]{0,80}SendSignal\s*\(\s*zavora\s*,\s*2\s*\)\s*;",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "La sequence ouverture/fermeture Burgundy 1 n'est pas valide.");
            if (!Regex.IsMatch(text,
                @"SendSignal\s*\(\s*zavora\s*,\s*2\s*\)\s*;[\s\S]{0,100}HUMAN_Move\s*\(\s*""04_01""\s*\)\s*;[\s\S]{0,100}SaveGameValue\s*\(\s*61\s*,\s*[12]\s*\)\s*;",
                RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Le retour du garde apres la fermeture Burgundy 1 n'est pas valide.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] gate = ReadSource(ResolveSource(
                gamePath, "Scripts/Burgundy1/zavora.scr", ScriptArchives));
            string text = Encoding.GetEncoding(1252).GetString(gate);
            if (!Regex.IsMatch(text,
                    @"OnSignal\s*\(\s*1\s*\)[\s\S]{0,100}SetActorState\s*\(\s*zavora\s*,\s*1\s*\)",
                    RegexOptions.IgnoreCase)
                || !Regex.IsMatch(text,
                    @"OnSignal\s*\(\s*2\s*\)[\s\S]{0,100}SetActorState\s*\(\s*zavora\s*,\s*0\s*\)",
                    RegexOptions.IgnoreCase))
                throw new InvalidDataException(
                    "Les commandes officielles de la barriere Burgundy 1 sont absentes.");

            foreach (string registryPath in RegistryPaths)
            {
                byte[] registry = ReadSource(ResolveSource(
                    gamePath, registryPath, MissionArchives));
                if (!HasBinding(registry, "bu1_04", "bur1_04.scr")
                    || !HasBinding(registry,
                        "la_zavora_.zavora", "zavora.scr"))
                    throw new InvalidDataException(
                        "Liaisons de barriere absentes dans " + registryPath + ".");
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Burgundy 1 trop court.");
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
                    "Registre de scripts Burgundy 1 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Burgundy 1.");
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

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}
