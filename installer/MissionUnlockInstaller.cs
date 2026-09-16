using System;
using System.IO;
using System.Text;

namespace HD2CommunityInstaller
{
    internal static class MissionUnlockInstaller
    {
        private const ushort RootTag = 0x1EDC;
        private const ushort BaseCampaignTag = 0x1F05;
        private const ushort SabreCampaignTag = 0x1F06;
        private static readonly int[] BaseUnlocked = { 23, 23, -1, 0 };
        private static readonly int[] SabreUnlocked = { 8, 8, -1, -1 };

        private sealed class ProfileLocation
        {
            public string Name;
            public string RelativePath;
            public string FullPath;
        }

        private sealed class CampaignRecords
        {
            public int BaseValueOffset;
            public int SabreValueOffset;
        }

        public static string ValidateOnly(string gamePath)
        {
            ProfileLocation profile = ResolveActiveProfile(gamePath);
            byte[] original = File.ReadAllBytes(profile.FullPath);
            CampaignRecords records = Parse(original);
            byte[] patched = (byte[])original.Clone();
            ApplyUnlockedValues(patched, records);
            if (!IsUnlocked(patched, Parse(patched)))
                throw new InvalidDataException("Le profil de test n'a pas ete debloque.");
            return "Profil actif verifie : " + profile.Name + "; 24 missions HD2 et "
                + "9 missions Sabre Squadron sont debloquables sans sauvegarde terminee.";
        }

        public static string DescribeStatus(string gamePath)
        {
            try
            {
                ProfileLocation profile = ResolveActiveProfile(gamePath);
                byte[] data = File.ReadAllBytes(profile.FullPath);
                return "Deblocage des missions : "
                    + (IsUnlocked(data, Parse(data)) ? "deja actif" : "a activer")
                    + " (profil " + profile.Name + ")";
            }
            catch (Exception ex)
            {
                return "Deblocage des missions : indetermine (" + ex.Message + ")";
            }
        }

        public static void Install(
            string gamePath, StateJournal journal, Action<string> progress)
        {
            ProfileLocation profile = ResolveActiveProfile(gamePath);
            byte[] original = File.ReadAllBytes(profile.FullPath);
            CampaignRecords records = Parse(original);
            if (IsUnlocked(original, records))
            {
                InstallerCore.Report(progress,
                    "Toutes les missions sont deja debloquees pour le profil "
                    + profile.Name + ".");
                return;
            }

            byte[] originalBase = Slice(original, records.BaseValueOffset, 16);
            byte[] originalSabre = Slice(original, records.SabreValueOffset, 16);
            byte[] patched = (byte[])original.Clone();
            ApplyUnlockedValues(patched, records);
            if (!IsUnlocked(patched, Parse(patched)))
                throw new InvalidDataException("Validation du profil debloque impossible.");

            string temporary = profile.FullPath + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                string installedHash = CmpInstaller.ComputeSha256(temporary);
                journal.RecordProfileUnlock(
                    profile.RelativePath, originalBase, originalSabre, installedHash);
                File.Copy(temporary, profile.FullPath, true);
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }

            InstallerCore.Log("Missions debloquees pour le profil " + profile.Name + ".");
            InstallerCore.Report(progress,
                "Toutes les campagnes et missions HD2 et Sabre Squadron sont disponibles "
                + "pour le profil " + profile.Name + ".");
        }

        public static void Restore(
            string gamePath, ProfileUnlockChange change, Action<string> progress)
        {
            string target = InstallerCore.SafeGameTarget(gamePath, change.RelativePath);
            if (!File.Exists(target))
            {
                InstallerCore.Report(progress,
                    "Profil absent; le deblocage des missions ne peut pas etre restaure.");
                return;
            }
            string currentHash = CmpInstaller.ComputeSha256(target);
            if (!String.Equals(currentHash, change.InstalledSha256,
                StringComparison.OrdinalIgnoreCase))
            {
                InstallerCore.Report(progress,
                    "Profil utilise depuis l'installation : progression conservee, "
                    + "aucune ancienne valeur de mission n'a ete imposee.");
                return;
            }

            byte[] data = File.ReadAllBytes(target);
            CampaignRecords records = Parse(data);
            CopyInto(change.OriginalBase, data, records.BaseValueOffset);
            CopyInto(change.OriginalSabre, data, records.SabreValueOffset);
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, data);
                File.Copy(temporary, target, true);
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
            InstallerCore.Report(progress,
                "Etat initial du deblocage des missions restaure.");
        }

        private static ProfileLocation ResolveActiveProfile(string gamePath)
        {
            InstallerCore.ValidateGamePath(gamePath);
            string config = Path.Combine(gamePath, "game.cfg");
            if (!File.Exists(config))
                throw new FileNotFoundException(
                    "Le fichier game.cfg est absent; creez d'abord un profil dans le jeu.", config);
            string name = null;
            foreach (string line in File.ReadAllLines(config, Encoding.Default))
                if (line.StartsWith("LASTPROFIL=", StringComparison.OrdinalIgnoreCase))
                    name = line.Substring("LASTPROFIL=".Length).Trim();
            if (String.IsNullOrWhiteSpace(name))
                throw new InvalidOperationException(
                    "Aucun profil actif; lancez le jeu et creez un profil avant le deblocage.");
            if (name.IndexOfAny(new[] { '/', '\\', ':' }) >= 0 || name == "." || name == "..")
                throw new InvalidDataException("Nom de profil non sur dans game.cfg.");
            string relative = "PlayersProfiles/" + name + "/profile.sav";
            string full = InstallerCore.SafeGameTarget(gamePath, relative);
            if (!File.Exists(full))
                throw new FileNotFoundException("Le profil actif est introuvable.", full);
            return new ProfileLocation { Name = name, RelativePath = relative, FullPath = full };
        }

        private static CampaignRecords Parse(byte[] data)
        {
            if (data == null || data.Length < 12 || BitConverter.ToUInt16(data, 0) != RootTag
                || BitConverter.ToInt32(data, 2) != data.Length)
                throw new InvalidDataException("Format profile.sav non reconnu.");
            CampaignRecords result = new CampaignRecords {
                BaseValueOffset = -1, SabreValueOffset = -1
            };
            int offset = 6;
            while (offset < data.Length)
            {
                if (offset > data.Length - 6)
                    throw new InvalidDataException("Enregistrement profile.sav tronque.");
                ushort tag = BitConverter.ToUInt16(data, offset);
                int length = BitConverter.ToInt32(data, offset + 2);
                if (length < 6 || offset > data.Length - length)
                    throw new InvalidDataException("Taille d'enregistrement profile.sav invalide.");
                if (tag == BaseCampaignTag || tag == SabreCampaignTag)
                {
                    if (length != 22)
                        throw new InvalidDataException("Bloc de campagne de taille inattendue.");
                    int valueOffset = offset + 6;
                    if (tag == BaseCampaignTag)
                    {
                        if (result.BaseValueOffset >= 0)
                            throw new InvalidDataException("Bloc campagne HD2 duplique.");
                        result.BaseValueOffset = valueOffset;
                    }
                    else
                    {
                        if (result.SabreValueOffset >= 0)
                            throw new InvalidDataException("Bloc campagne Sabre duplique.");
                        result.SabreValueOffset = valueOffset;
                    }
                }
                offset += length;
            }
            if (offset != data.Length || result.BaseValueOffset < 0
                || result.SabreValueOffset < 0)
                throw new InvalidDataException(
                    "Le profil ne contient pas les deux campagnes HD2 1.12 attendues.");
            return result;
        }

        private static void ApplyUnlockedValues(byte[] data, CampaignRecords records)
        {
            WriteValues(data, records.BaseValueOffset, BaseUnlocked);
            WriteValues(data, records.SabreValueOffset, SabreUnlocked);
        }

        private static bool IsUnlocked(byte[] data, CampaignRecords records)
        {
            return BitConverter.ToInt32(data, records.BaseValueOffset) >= 23
                && BitConverter.ToInt32(data, records.BaseValueOffset + 4) >= 23
                && BitConverter.ToInt32(data, records.SabreValueOffset) >= 8
                && BitConverter.ToInt32(data, records.SabreValueOffset + 4) >= 8;
        }

        private static void WriteValues(byte[] target, int offset, int[] values)
        {
            for (int index = 0; index < values.Length; index++)
                Buffer.BlockCopy(BitConverter.GetBytes(values[index]), 0,
                    target, offset + index * 4, 4);
        }

        private static byte[] Slice(byte[] source, int offset, int count)
        {
            byte[] result = new byte[count];
            Buffer.BlockCopy(source, offset, result, 0, count);
            return result;
        }

        private static void CopyInto(byte[] source, byte[] target, int offset)
        {
            if (source == null || source.Length != 16)
                throw new InvalidDataException("Valeur de progression invalide.");
            Buffer.BlockCopy(source, 0, target, offset, source.Length);
        }
    }
}