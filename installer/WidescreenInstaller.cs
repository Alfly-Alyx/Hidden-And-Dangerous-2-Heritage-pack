using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace HD2CommunityInstaller
{
    internal static class WidescreenInstaller
    {
        private const string ResourceName = "HD2CommunityInstaller.WidescreenFix.zip";
        private const string ArchiveSha256 = "8B8315B88420FCFED9891F2D39886F6384BDA1B32CDD299AC27D728391E65A9F";
        private static readonly Dictionary<string, string> Expected =
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
                { "d3d8.dll", "A07F2B90B0EA9CFFB568218E500EA3280B750C195E83D82A6BB7A252642708E3" },
                { "Maps/2e_camra.tga", "43B609F80497959D1127B2A7F3F0FCAAEA1322A8BD9F770ECEEEC4146D2D1EF0" },
                { "Maps/2e_scope.tga", "8E6E892F11B710F395853EA97CA4D09337FF4842AF543986941A59ADF90738E1" },
                { "Maps/e_zamer.tga", "0D86A937580805EBFE1F932F218E6407ACB4D7DC365A34C0C50385A7522F6FD7" },
                { "scripts/HiddenandDangerous2.WidescreenFix.asi", "8375F31A2A1F6C6B401AF40BB4F8C741FD3BA90B36B14603176FB71465D62768" },
                { "scripts/HiddenandDangerous2.WidescreenFix.ini", "337A157743D015644EA7DB069C5BDE05D4084C511730F480237B96146D96E701" }
            };

        public static string DetectStatus(string gamePath)
        {
            int ready = 0;
            foreach (KeyValuePair<string, string> item in Expected)
            {
                string target = InstallerCore.SafeGameTarget(gamePath, item.Key);
                if (File.Exists(target)
                    && String.Equals(CmpInstaller.ComputeSha256(target), item.Value,
                        StringComparison.OrdinalIgnoreCase)) ready++;
            }
            if (ready == Expected.Count) return "deja actif";
            if (ready == 0) return "a installer";
            return "partiel (" + ready + "/" + Expected.Count + " fichiers)";
        }

        public static string ValidateOnly()
        {
            byte[] archive = ReadEmbeddedArchive();
            ValidateEntries(archive);
            return "Correctif ecran large verifie : " + Expected.Count
                + " fichiers, archive SHA-256 " + ArchiveSha256 + ".";
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress, "Installation du support ecran large et haute resolution...");
            byte[] archiveBytes = ReadEmbeddedArchive();
            ValidateEntries(archiveBytes);
            using (MemoryStream memory = new MemoryStream(archiveBytes, false))
            using (ZipArchive archive = new ZipArchive(memory, ZipArchiveMode.Read, false))
            {
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    string relative = entry.FullName.Replace('\\', '/');
                    string expectedHash;
                    if (!Expected.TryGetValue(relative, out expectedHash)) continue;
                    string target = InstallerCore.SafeGameTarget(gamePath, relative);
                    InstallerCore.PrepareTarget(gamePath, relative, target, journal, prepared);
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    string temporary = target + ".hd2pack.tmp";
                    try
                    {
                        using (Stream input = entry.Open())
                        using (FileStream output = new FileStream(
                            temporary, FileMode.Create, FileAccess.Write, FileShare.None))
                            input.CopyTo(output);
                        string actual = CmpInstaller.ComputeSha256(temporary);
                        if (!String.Equals(actual, expectedHash, StringComparison.OrdinalIgnoreCase))
                            throw new InvalidDataException(
                                "Empreinte invalide dans le correctif ecran large : " + relative);
                        File.Copy(temporary, target, true);
                        journal.RecordHash(relative, actual);
                    }
                    finally
                    {
                        if (File.Exists(temporary)) File.Delete(temporary);
                    }
                }
            }
            InstallLicense(gamePath, journal, prepared);
            InstallerCore.Report(progress, "Support ecran large installe (FOV, HUD et visees corriges).");
        }

        private static byte[] ReadEmbeddedArchive()
        {
            using (Stream stream = Assembly.GetExecutingAssembly()
                .GetManifestResourceStream(ResourceName))
            {
                if (stream == null)
                    throw new InvalidDataException("Archive ecran large embarquee introuvable.");
                using (MemoryStream memory = new MemoryStream())
                {
                    stream.CopyTo(memory);
                    byte[] bytes = memory.ToArray();
                    using (SHA256 sha = SHA256.Create())
                    {
                        string actual = BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "");
                        if (!String.Equals(actual, ArchiveSha256,
                            StringComparison.OrdinalIgnoreCase))
                            throw new InvalidDataException(
                                "Empreinte de l'archive ecran large invalide.");
                    }
                    return bytes;
                }
            }
        }

        private static void ValidateEntries(byte[] archiveBytes)
        {
            int files = 0;
            using (MemoryStream memory = new MemoryStream(archiveBytes, false))
            using (ZipArchive archive = new ZipArchive(memory, ZipArchiveMode.Read, false))
            {
                foreach (ZipArchiveEntry entry in archive.Entries)
                {
                    string relative = entry.FullName.Replace('\\', '/');
                    if (entry.Length == 0) continue;
                    string expected;
                    if (!Expected.TryGetValue(relative, out expected))
                        throw new InvalidDataException(
                            "Fichier inattendu dans le correctif ecran large : " + relative);
                    string actual;
                    using (Stream input = entry.Open())
                    using (SHA256 sha = SHA256.Create())
                        actual = BitConverter.ToString(sha.ComputeHash(input)).Replace("-", "");
                    if (!String.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException(
                            "Empreinte invalide dans le correctif ecran large : " + relative);
                    files++;
                }
            }
            if (files != Expected.Count)
                throw new InvalidDataException("Archive ecran large incomplete.");
        }

        private static void InstallLicense(
            string gamePath, StateJournal journal, HashSet<string> prepared)
        {
            const string relative = "scripts/HiddenandDangerous2.WidescreenFix.LICENSE.txt";
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            InstallerCore.PrepareTarget(gamePath, relative, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string text = "MIT License\r\n\r\nCopyright (c) 2018 ThirteenAG\r\n\r\n"
                + "Permission is hereby granted, free of charge, to any person obtaining a copy "
                + "of this software and associated documentation files (the Software), to deal "
                + "in the Software without restriction, including without limitation the rights "
                + "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies "
                + "of the Software, and to permit persons to whom the Software is furnished to do so, "
                + "subject to the following conditions:\r\n\r\n"
                + "The above copyright notice and this permission notice shall be included in all "
                + "copies or substantial portions of the Software.\r\n\r\n"
                + "THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, "
                + "INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A "
                + "PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT "
                + "HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION "
                + "OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE "
                + "SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\r\n";
            File.WriteAllText(target, text, new UTF8Encoding(false));
            journal.RecordHash(relative, CmpInstaller.ComputeSha256(target));
        }
    }
}
