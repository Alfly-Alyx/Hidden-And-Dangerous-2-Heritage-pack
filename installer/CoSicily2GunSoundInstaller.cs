using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class CoSicily2GunSoundInstaller
    {
        private sealed class GunSpec
        {
            public string Actor;
            public string Script;
        }

        private const string RegistryPath =
            "Missions/Co_Sicily2/MpScripts.dta";

        private static readonly GunSpec[] Guns = {
            new GunSpec { Actor = "PAK40_1", Script = "Sic2_delo_1.scr" },
            new GunSpec { Actor = "PAK40_2", Script = "Sic2_delo_2.scr" }
        };

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            foreach (GunSpec gun in Guns)
            {
                byte[] original = ReadSource(ResolveSource(
                    gamePath, CooperativeScriptPath(gun), ScriptArchives));
                byte[] patched = PatchScript(gun, original);
                if (BytesEqual(original, patched))
                    throw new InvalidDataException(
                        "Le son du canon " + gun.Actor
                        + " semble deja actif dans l'archive cooperative.");
                ValidatePatched(gun, patched);
                if (!BytesEqual(patched, PatchScript(gun, patched)))
                    throw new InvalidDataException(
                        "La restauration sonore de Sicily 2 n'est pas idempotente.");
            }
            ValidateAssets(gamePath);
            return "Sicily 2 cooperative verifiee : les deux canons peuvent "
                + "retrouver le son de destruction conserve dans leurs homologues solo.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                foreach (GunSpec gun in Guns)
                {
                    string target = InstallerCore.SafeGameTarget(
                        gamePath, CooperativeScriptPath(gun));
                    if (!File.Exists(target)) return false;
                    ValidatePatched(gun, File.ReadAllBytes(target));
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
                "Restauration du son des canons dans Sicily 2 cooperative...");
            ValidateAssets(gamePath);
            int changed = 0;
            foreach (GunSpec gun in Guns)
            {
                string relative = CooperativeScriptPath(gun);
                DormantSource source = ResolveSource(
                    gamePath, relative, ScriptArchives);
                string target = InstallerCore.SafeGameTarget(
                    gamePath, relative);
                byte[] original = File.Exists(target)
                    ? File.ReadAllBytes(target) : ReadSource(source);
                byte[] patched = PatchScript(gun, original);
                ValidatePatched(gun, patched);
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

            InstallerCore.Log("Sicily 2 cooperative : son de destruction "
                + "restaure dans " + changed + " scripts de canons.");
            InstallerCore.Report(progress,
                "Les deux canons de Sicily 2 cooperative retrouvent leur son de destruction.");
        }

        private static byte[] PatchScript(GunSpec gun, byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (ActiveSoundRegex().Matches(text).Count == 1
                && DormantSoundRegex().Matches(text).Count == 0)
                return data;
            if (ActiveSoundRegex().Matches(text).Count != 0
                || DormantSoundRegex().Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Vestige sonore absent ou ambigu dans " + gun.Script + ".");

            text = DormantSoundRegex().Replace(text, delegate(Match match) {
                return match.Groups["indent"].Value
                    + match.Groups["code"].Value;
            }, 1);
            return ansi.GetBytes(text);
        }

        private static Regex DormantSoundRegex()
        {
            return new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*(?<code>PlaySound[ \t]*"
                + @"\([ \t]*6[ \t]*,[ \t]*2[ \t]*\)[ \t]*;)[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static Regex ActiveSoundRegex()
        {
            return new Regex(
                @"(?m)^[ \t]*PlaySound[ \t]*\([ \t]*6[ \t]*,[ \t]*2"
                + @"[ \t]*\)[ \t]*;[ \t]*\r?$",
                RegexOptions.IgnoreCase);
        }

        private static void ValidatePatched(GunSpec gun, byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (ActiveSoundRegex().Matches(text).Count != 1
                || DormantSoundRegex().Matches(text).Count != 0)
                throw new InvalidDataException(
                    "Son de destruction non restaure dans " + gun.Script + ".");
            string[] required = {
                "OnSignal(1)",
                "SetActorState(EX1, 1)",
                "SetActorState(EX2, 1)",
                "SetActorState(delo, 2)"
            };
            foreach (string marker in required)
                if (text.IndexOf(marker,
                        StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Logique cooperative alteree dans " + gun.Script
                        + " : " + marker + ".");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            foreach (GunSpec gun in Guns)
            {
                if (!HasBinding(registry, gun.Actor, gun.Script))
                    throw new InvalidDataException(
                        "Liaison Sicily 2 absente : " + gun.Actor
                        + " -> " + gun.Script + ".");

                byte[] solo = ReadSource(ResolveSource(
                    gamePath, SoloScriptPath(gun), ScriptArchives));
                string soloText = Encoding.GetEncoding(1252).GetString(solo);
                if (ActiveSoundRegex().Matches(soloText).Count != 1
                    || DormantSoundRegex().Matches(soloText).Count != 0)
                    throw new InvalidDataException(
                        "Homologue solo sonore absent dans " + gun.Script + ".");

                byte[] cooperative = ReadSource(ResolveSource(
                    gamePath, CooperativeScriptPath(gun), ScriptArchives));
                string cooperativeText =
                    Encoding.GetEncoding(1252).GetString(cooperative);
                if (DormantSoundRegex().Matches(cooperativeText).Count != 1
                    || ActiveSoundRegex().Matches(cooperativeText).Count != 0)
                    throw new InvalidDataException(
                        "Vestige cooperative non confirme dans " + gun.Script + ".");
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Sicily 2 trop court.");
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
                    "Champ invalide dans le registre Sicily 2.");
            uint rawLength = BitConverter.ToUInt32(data, offset + 2);
            if (rawLength < 7 || rawLength > Int32.MaxValue
                || offset > data.Length - (int)rawLength
                || data[offset + (int)rawLength - 1] != 0)
                throw new InvalidDataException(
                    "Taille de champ invalide dans le registre Sicily 2.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, (int)rawLength - 7);
            offset += (int)rawLength;
            return value;
        }

        private static string CooperativeScriptPath(GunSpec gun)
        {
            return "Scripts/Co_Sicily2/" + gun.Script;
        }

        private static string SoloScriptPath(GunSpec gun)
        {
            return "Scripts/Sicily2/" + gun.Script;
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
