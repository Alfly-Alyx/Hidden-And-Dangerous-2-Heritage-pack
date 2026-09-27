using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;

namespace HD2CommunityInstaller
{
    internal static class ManagedMissionTreeInventory
    {
        internal static Dictionary<string, string> ReadHashes(string gamePath)
        {
            Dictionary<string, string> hashes = new Dictionary<string, string>(
                StringComparer.OrdinalIgnoreCase);
            string state = InstallerCore.SafeGameTarget(
                gamePath, "STATIC_MENU_MANAGED_FILES.json");
            if (!File.Exists(state)) return hashes;

            Dictionary<string, object> document;
            try
            {
                JavaScriptSerializer json = new JavaScriptSerializer {
                    MaxJsonLength = 16 * 1024 * 1024
                };
                document = json.DeserializeObject(File.ReadAllText(state, Encoding.UTF8))
                    as Dictionary<string, object>;
            }
            catch (Exception error)
            {
                throw new InvalidDataException(
                    "Inventaire des missions personnalisees illisible.", error);
            }

            object files;
            if (document == null || !document.TryGetValue("files", out files)
                || !(files is object[]))
                throw new InvalidDataException(
                    "Inventaire des missions personnalisees invalide.");
            foreach (object item in (object[])files)
            {
                Dictionary<string, object> entry = item as Dictionary<string, object>;
                object path, hash;
                if (entry == null || !entry.TryGetValue("relative", out path)
                    || !entry.TryGetValue("sha256", out hash))
                    throw new InvalidDataException(
                        "Entree invalide dans l'inventaire des missions personnalisees.");
                string relative = Convert.ToString(path).Replace('\\', '/');
                if (!relative.StartsWith("Missions/", StringComparison.OrdinalIgnoreCase)
                    || !relative.EndsWith("/tree.klz", StringComparison.OrdinalIgnoreCase))
                    continue;
                string expected = Convert.ToString(hash);
                if (expected.Length != 64)
                    throw new InvalidDataException(
                        "Empreinte de mission personnalisee invalide : " + relative);
                hashes[InstallerCore.SafeGameTarget(gamePath, relative)] = expected;
            }
            return hashes;
        }
    }
}