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
            const string prefix = "Serveurs Internet communautaires :";
            if (!HasStatus(prefix + " configuree", prefix, "configuree"))
                throw new InvalidOperationException(
                    "La detection refuse un etat Internet configure.");
            if (HasStatus(prefix + " non configuree", prefix, "configuree"))
                throw new InvalidOperationException(
                    "La detection confond configuree et non configuree.");
            if (HasStatus(prefix + " partielle (1/3)", prefix, "configuree"))
                throw new InvalidOperationException(
                    "La detection confond configuree et partielle.");
            if (!HasStatus("CMP 2.6.5 : deja installee (156 cartes)",
                "CMP 2.6.5 :", "deja installee"))
                throw new InvalidOperationException(
                    "La detection refuse un etat actif suivi de details.");
            if (!HasStatus("Deblocage des missions : deja actif (profil Alfly)",
                "Deblocage des missions :", "deja actif"))
                throw new InvalidOperationException(
                    "La detection refuse un profil dont les missions sont debloquees.");
            string hosts = "# BEGIN HD2 Community MasterList\r\n"
                + "78.47.255.224 hd2.available.gamespy.com\r\n"
                + "78.47.255.224 hd2.master.gamespy.com\r\n"
                + "78.47.255.224 hd2.ms14.gamespy.com\r\n"
                + "# END HD2 Community MasterList\r\n";
            if (InstallerCore.CountConfiguredMasterAliases(hosts)
                != AppConfig.MasterAliases.Length)
                throw new InvalidOperationException(
                    "La detection refuse une liste de serveurs Windows en CRLF.");
            return "Detection exacte des etats de l'interface verifiee.";
        }
    }
}
