using System;

namespace HD2CommunityInstaller
{
    internal static class DiagnosticStatusMatcher
    {
        public static bool HasStatus(
            string diagnostic, string prefix, string status)
        {
            if (String.IsNullOrEmpty(diagnostic)
                || String.IsNullOrEmpty(prefix)
                || String.IsNullOrEmpty(status)) return false;
            foreach (string line in diagnostic.Split(new[] { "\r\n", "\n", "\r" },
                StringSplitOptions.RemoveEmptyEntries))
            {
                if (!line.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                    continue;
                string value = line.Substring(prefix.Length).TrimStart();
                return value.StartsWith(status, StringComparison.OrdinalIgnoreCase);
            }
            return false;
        }

        public static string ValidateOnly()
        {
            const string prefix = "Fusion des listes Internet :";
            if (!HasStatus(prefix + " deja active (service actuel + OpenSpy)",
                    prefix, "deja active"))
                throw new InvalidOperationException(
                    "La detection refuse un etat Internet configure.");
            if (HasStatus(prefix + " a configurer", prefix, "deja active"))
                throw new InvalidOperationException(
                    "La detection confond configuree et non configuree.");
            if (HasStatus(prefix + " partiellement active", prefix, "deja active"))
                throw new InvalidOperationException(
                    "La detection confond configuree et partielle.");
            if (!HasStatus("CMP officiel : deja installee (version 2.6.5, 156 cartes)",
                "CMP officiel :", "deja installee"))
                throw new InvalidOperationException(
                    "La detection refuse un etat actif suivi de details.");
            if (!HasStatus("Deblocage des missions : deja actif (profil Alfly)",
                "Deblocage des missions :", "deja actif"))
                throw new InvalidOperationException(
                    "La detection refuse un profil dont les missions sont debloquees.");
            if (!HasStatus(
                    "Rapports automatiques : deja actif (demarre et s'arrete avec le jeu)",
                    "Rapports automatiques :", "deja actif"))
                throw new InvalidOperationException(
                    "La detection refuse le moniteur de diagnostics actif.");
            if (!HasStatus("Guides PDF sur le Bureau : deja presents en francais",
                    "Guides PDF sur le Bureau :", "deja presents"))
                throw new InvalidOperationException(
                    "La detection refuse les guides deja telecharges.");
            string hosts = "# BEGIN HD2 Community MasterList\r\n"
                + "78.47.255.224 hd2.available.gamespy.com\r\n"
                + "78.47.255.224 hd2.master.gamespy.com\r\n"
                + "127.0.0.1 hd2.ms14.gamespy.com\r\n"
                + "# END HD2 Community MasterList\r\n";
            if (InstallerCore.CountConfiguredMasterAliases(hosts)
                != AppConfig.MasterAliases.Length)
                throw new InvalidOperationException(
                    "La detection refuse une liste de serveurs Windows en CRLF.");
            string slashGuide =
                "Guides/HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf";
            string backslashGuide =
                @"Guides\HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf";
            if (!String.Equals(
                    InstallState.NormalizeRelativePath(slashGuide),
                    InstallState.NormalizeRelativePath(backslashGuide),
                    StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException(
                    "Le journal ne normalise pas les separateurs de chemins.");
            if (!InstallState.IsExternalReleaseGuide(slashGuide)
                || InstallState.IsExternalReleaseGuide(
                    @"Guides\HD2-Guide-Joueur-Secrets-et-Easter-Eggs.txt"))
                throw new InvalidOperationException(
                    "Le journal ne distingue pas exactement les PDF externes.");
            return "Detection exacte des etats de l'interface verifiee.";
        }
    }
}
