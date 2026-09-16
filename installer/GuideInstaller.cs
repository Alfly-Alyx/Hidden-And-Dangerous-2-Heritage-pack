using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;

namespace HD2CommunityInstaller
{
    internal static class GuideInstaller
    {
        private sealed class EmbeddedGuide
        {
            public string ResourceName;
            public string RelativePath;
        }

        private static readonly EmbeddedGuide[] Guides = {
            new EmbeddedGuide {
                ResourceName = "HD2CommunityInstaller.GuideJoueur.pdf",
                RelativePath = "Guides/HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf"
            },
            new EmbeddedGuide {
                ResourceName = "HD2CommunityInstaller.RapportDecouvertes.pdf",
                RelativePath = "Guides/HD2-Rapport-des-Decouvertes.pdf"
            },
            new EmbeddedGuide {
                ResourceName = "HD2CommunityInstaller.PlayerGuideEN.pdf",
                RelativePath = "Guides/HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf"
            },
            new EmbeddedGuide {
                ResourceName = "HD2CommunityInstaller.DiscoveryReportEN.pdf",
                RelativePath = "Guides/HD2-Discovery-Report-EN.pdf"
            }
        };

        public static string ValidateOnly()
        {
            Assembly assembly = Assembly.GetExecutingAssembly();
            foreach (EmbeddedGuide guide in Guides)
                using (Stream stream = assembly.GetManifestResourceStream(guide.ResourceName))
                    if (stream == null || stream.Length < 1024)
                        throw new InvalidDataException(
                            "Guide PDF integre absent ou incomplet : " + guide.ResourceName);
            return "Guides verifies : quatre PDF francais et anglais integres.";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            ValidateOnly();
            InstallerCore.Report(progress, "Installation des quatre guides PDF...");
            Assembly assembly = Assembly.GetExecutingAssembly();
            foreach (EmbeddedGuide guide in Guides)
            {
                string target = InstallerCore.SafeGameTarget(gamePath, guide.RelativePath);
                InstallerCore.PrepareTarget(
                    gamePath, guide.RelativePath, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    using (Stream input = assembly.GetManifestResourceStream(guide.ResourceName))
                    using (FileStream output = new FileStream(
                        temporary, FileMode.Create, FileAccess.Write, FileShare.None))
                    {
                        if (input == null)
                            throw new InvalidDataException(
                                "Ressource PDF introuvable : " + guide.ResourceName);
                        input.CopyTo(output);
                    }
                    File.Copy(temporary, target, true);
                    journal.RecordHash(
                        guide.RelativePath, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
            }
        }
    }
}