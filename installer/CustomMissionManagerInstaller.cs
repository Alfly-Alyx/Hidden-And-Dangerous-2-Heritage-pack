using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace HD2CommunityInstaller
{
    internal static class CustomMissionManagerInstaller
    {
        private const string ManagerHashResource =
            "HD2CommunityInstaller.CustomMissionManager.sha256";

        private sealed class EmbeddedFile
        {
            public string ResourceName;
            public string RelativePath;
            public string Sha256;
            public bool PreserveExisting;
            public bool Executable;
        }

        private static readonly EmbeddedFile[] Files = {
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissionManager.exe",
                RelativePath = "HD2-Custom-Mission-Manager.exe",
                Executable = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.Readme",
                RelativePath = "CustomMissions/README.md",
                Sha256 = "506AD7624A1FFED8CF8356C10529FA6468AB3AFF52035A14BC92E69199E91C3F",
                PreserveExisting = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.Schema",
                RelativePath = "CustomMissions/mission.schema.json",
                Sha256 = "C53CDD71AAB058D3B8E4E94B6A1140663B7D9A0B577B040FFD6850CA3EDE9D75",
                PreserveExisting = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.TemplateManifest",
                RelativePath = "CustomMissions/_modele/mission.json",
                Sha256 = "9439500FB79D571160E22B2884DE1662E73ED779641329A3C7AA5E737DA5946F",
                PreserveExisting = true
            },
            new EmbeddedFile {
                ResourceName = "HD2CommunityInstaller.CustomMissions.TemplateReadme",
                RelativePath = "CustomMissions/_modele/payload/Missions/MaMission/LISEZ_MOI.txt",
                Sha256 = "A48C1FFE82BDD37BD943CF259B7468AD4DF5D65F96096A6C5CD3269BAE834A03",
                PreserveExisting = true
            }
        };

        public static string ValidateOnly()
        {
            foreach (EmbeddedFile file in Files)
                ValidateFile(file, ReadResource(file));
            return "Gestionnaire de missions personnalisees verifie : executable et squelette embarques.";
        }

        public static string DetectStatus(string gamePath)
        {
            int ready = 0;
            foreach (EmbeddedFile file in Files)
            {
                string target = InstallerCore.SafeGameTarget(gamePath, file.RelativePath);
                if (!File.Exists(target)) continue;
                if (file.Executable)
                {
                    try
                    {
                        ValidateFile(file, File.ReadAllBytes(target));
                        ready++;
                    }
                    catch (InvalidDataException) { }
                }
                else if (String.Equals(
                    CmpInstaller.ComputeSha256(target), file.Sha256,
                    StringComparison.OrdinalIgnoreCase))
                    ready++;
            }
            if (ready == Files.Length) return "installe";
            if (ready == 0) return "a installer";
            return "partiel (" + ready + "/" + Files.Length + " fichiers)";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(
                progress, "Installation du gestionnaire de missions personnalisees...");
            foreach (EmbeddedFile file in Files)
            {
                byte[] content = ReadResource(file);
                ValidateFile(file, content);
                string relative = file.RelativePath.Replace(
                    '/', Path.DirectorySeparatorChar);
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                bool tracked = prepared.Contains(relative);
                if (file.PreserveExisting && File.Exists(target) && !tracked)
                {
                    InstallerCore.Report(
                        progress, "Fichier CustomMissions existant conserve : "
                            + file.RelativePath);
                    continue;
                }

                InstallerCore.PrepareTarget(
                    gamePath, relative, target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string temporary = target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, content);
                    ValidateFile(file, File.ReadAllBytes(temporary));
                    File.Copy(temporary, target, true);
                    journal.RecordHash(
                        relative, CmpInstaller.ComputeSha256(target));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
            }
            InstallerCore.Report(
                progress, "Gestionnaire installe; missions utilisateur conservees.");
        }

        private static byte[] ReadResource(EmbeddedFile file)
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(file.ResourceName))
            {
                if (stream == null)
                    throw new InvalidDataException(
                        "Ressource du gestionnaire introuvable : " + file.ResourceName);
                using (MemoryStream memory = new MemoryStream())
                {
                    stream.CopyTo(memory);
                    return memory.ToArray();
                }
            }
        }

        private static void ValidateFile(EmbeddedFile file, byte[] content)
        {
            if (file.Executable)
            {
                ValidateExecutable(content);
                string expected = ReadManagerHash();
                string actual = ComputeSha256(content);
                if (!String.Equals(actual, expected,
                    StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException(
                        "Empreinte invalide pour le gestionnaire de missions.");
                return;
            }
            string skeletonHash = ComputeSha256(content);
            if (!String.Equals(skeletonHash, file.Sha256,
                StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "Empreinte invalide dans le squelette CustomMissions : "
                        + file.RelativePath);
        }

        private static string ReadManagerHash()
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(ManagerHashResource))
            {
                if (stream == null)
                    throw new InvalidDataException(
                        "Empreinte embarquee du gestionnaire introuvable.");
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.ASCII, false))
                {
                    string expected = reader.ReadToEnd().Trim();
                    if (expected.Length != 64)
                        throw new InvalidDataException(
                            "Empreinte embarquee du gestionnaire invalide.");
                    for (int index = 0; index < expected.Length; index++)
                        if (!Uri.IsHexDigit(expected[index]))
                            throw new InvalidDataException(
                                "Empreinte embarquee du gestionnaire invalide.");
                    return expected;
                }
            }
        }

        private static string ComputeSha256(byte[] content)
        {
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(
                    sha.ComputeHash(content)).Replace("-", "");
        }

        private static void ValidateExecutable(byte[] content)
        {
            if (content == null || content.Length < 65536
                || content[0] != (byte)'M' || content[1] != (byte)'Z')
                throw new InvalidDataException(
                    "Executable du gestionnaire absent ou invalide.");
            int peOffset = BitConverter.ToInt32(content, 0x3C);
            if (peOffset < 0x40 || peOffset > content.Length - 26
                || content[peOffset] != (byte)'P'
                || content[peOffset + 1] != (byte)'E'
                || content[peOffset + 2] != 0
                || content[peOffset + 3] != 0
                || BitConverter.ToUInt16(content, peOffset + 4) != 0x014C
                || BitConverter.ToUInt16(content, peOffset + 24) != 0x010B)
                throw new InvalidDataException(
                    "Executable Windows x86 du gestionnaire invalide.");
        }
    }
}
