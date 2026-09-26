using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net;
using System.Security.Cryptography;

namespace HD2CommunityInstaller
{
    internal static class GuideDownloader
    {
        private const string RawBase =
            "https://raw.githubusercontent.com/Alfly-Alyx/"
            + "Hidden-And-Dangerous-2-Heritage-pack/"
            + "1087cc1bba83ee39d4510b2cfdc7461e954c5642/output/pdf/";

        private sealed class Guide
        {
            public string FileName;
            public string Sha256;
        }

        private static readonly Guide[] French = {
            new Guide {
                FileName = "HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf",
                Sha256 = "4848778AC9CE108C1DDE7BFD1BE88DA1AC5E2136F33FA397DEB8E707FD578165"
            },
            new Guide {
                FileName = "HD2-Rapport-des-Decouvertes.pdf",
                Sha256 = "C470739CC680B6F7E0676B7A4C25B3A952A1A17E01EC5C3F77FD077786C94BEF"
            }
        };

        private static readonly Guide[] English = {
            new Guide {
                FileName = "HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf",
                Sha256 = "CD79A648A80E81458B2D2882185AB27A3C2F2DCEFDFC1668F71071454073FB87"
            },
            new Guide {
                FileName = "HD2-Discovery-Report-EN.pdf",
                Sha256 = "C6BF216A0F6B5CCC39495FB74465159935E5BCACD65FFEA7B4AFCE01FAD9D60A"
            }
        };

        public static bool UseFrench
        {
            get
            {
                return String.Equals(
                    CultureInfo.CurrentUICulture.TwoLetterISOLanguageName,
                    "fr", StringComparison.OrdinalIgnoreCase);
            }
        }

        public static string LanguageName
        {
            get { return UseFrench ? "francais" : "anglais"; }
        }

        public static string ValidateOnly()
        {
            foreach (Guide guide in French)
                ValidateDefinition(guide);
            foreach (Guide guide in English)
                ValidateDefinition(guide);
            return "Telechargement des guides verifie : deux PDF francais ou anglais, "
                + "empreintes SHA-256 obligatoires.";
        }

        public static string DetectStatus()
        {
            string desktop = Environment.GetFolderPath(
                Environment.SpecialFolder.DesktopDirectory);
            Guide[] guides = UseFrench ? French : English;
            int ready = 0;
            foreach (Guide guide in guides)
            {
                string target = Path.Combine(desktop, guide.FileName);
                try
                {
                    if (File.Exists(target) && String.Equals(
                        CmpInstaller.ComputeSha256(target), guide.Sha256,
                        StringComparison.OrdinalIgnoreCase)) ready++;
                }
                catch { }
            }
            if (ready == guides.Length)
                return "deja presents en " + LanguageName;
            if (ready == 0) return "a telecharger en " + LanguageName;
            return "partiels (" + ready + "/" + guides.Length + ", "
                + LanguageName + ")";
        }

        public static void Install(Action<string> progress)
        {
            ValidateOnly();
            string desktop = Environment.GetFolderPath(
                Environment.SpecialFolder.DesktopDirectory);
            if (String.IsNullOrWhiteSpace(desktop))
                throw new DirectoryNotFoundException(
                    "Le Bureau Windows de l'utilisateur est introuvable.");
            Directory.CreateDirectory(desktop);
            ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072;
            Guide[] guides = UseFrench ? French : English;
            InstallerCore.Report(progress, "Telechargement des deux guides PDF en "
                + LanguageName + " vers le Bureau...");
            foreach (Guide guide in guides)
            {
                string target = Path.Combine(desktop, guide.FileName);
                if (File.Exists(target) && String.Equals(
                        CmpInstaller.ComputeSha256(target), guide.Sha256,
                        StringComparison.OrdinalIgnoreCase))
                    continue;
                byte[] data;
                using (WebClient client = new WebClient())
                {
                    client.Headers[HttpRequestHeader.UserAgent] =
                        "HD2-Heritage-Pack/" + AppConfig.Version;
                    data = client.DownloadData(new Uri(RawBase + guide.FileName));
                }
                string actual = ComputeSha256(data);
                if (!String.Equals(actual, guide.Sha256,
                        StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "Le guide telecharge ne correspond pas a l'empreinte publiee : "
                        + guide.FileName);
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, data);
                    File.Copy(temporary, target, true);
                }
                finally { if (File.Exists(temporary)) File.Delete(temporary); }
            }
            InstallerCore.Report(progress,
                "Guides PDF " + LanguageName + " disponibles sur le Bureau.");
        }

        private static void ValidateDefinition(Guide guide)
        {
            if (String.IsNullOrWhiteSpace(guide.FileName)
                || !guide.FileName.EndsWith(".pdf", StringComparison.OrdinalIgnoreCase)
                || guide.FileName.IndexOf('/') >= 0 || guide.FileName.IndexOf('\\') >= 0
                || guide.Sha256 == null || guide.Sha256.Length != 64)
                throw new InvalidDataException("Definition de guide PDF invalide.");
        }

        private static string ComputeSha256(byte[] data)
        {
            using (SHA256 hash = SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(data)).Replace("-", "");
        }
    }
}
