using Microsoft.Win32;
using System;
using System.Management;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace HD2CommunityInstaller
{
    internal sealed class HardwareProfile
    {
        public string Level;
        public string Gpu;
        public ulong RamBytes;
        public int LogicalProcessors;
        public int NativeWidth;
        public int NativeHeight;
        public int Width;
        public int Height;

        public string Description
        {
            get
            {
                string resolution = Width + " x " + Height;
                if (Width != NativeWidth || Height != NativeHeight)
                    resolution += " sur ecran " + NativeWidth + " x " + NativeHeight;
                return resolution + ", profil " + Level
                    + " (" + LogicalProcessors + " processeurs logiques, "
                    + Math.Max(1, (long)(RamBytes / (1024UL * 1024 * 1024))) + " Go RAM"
                    + (String.IsNullOrWhiteSpace(Gpu) ? "" : ", " + Gpu) + ")";
            }
        }
    }

    internal static class GraphicsConfigurator
    {
        private const string RegistryPath = @"SOFTWARE\Illusion Softworks\Hidden & Dangerous 2";
        private const int EnumCurrentSettings = -1;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        private struct DisplayMode
        {
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
            public string DeviceName;
            public short SpecVersion;
            public short DriverVersion;
            public short Size;
            public short DriverExtra;
            public int Fields;
            public int PositionX;
            public int PositionY;
            public int DisplayOrientation;
            public int DisplayFixedOutput;
            public short Color;
            public short Duplex;
            public short YResolution;
            public short TTOption;
            public short Collate;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
            public string FormName;
            public short LogPixels;
            public int BitsPerPel;
            public int PelsWidth;
            public int PelsHeight;
            public int DisplayFlags;
            public int DisplayFrequency;
            public int ICMMethod;
            public int ICMIntent;
            public int MediaType;
            public int DitherType;
            public int Reserved1;
            public int Reserved2;
            public int PanningWidth;
            public int PanningHeight;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        private sealed class MemoryStatus
        {
            public uint Length = (uint)Marshal.SizeOf(typeof(MemoryStatus));
            public uint MemoryLoad;
            public ulong TotalPhysical;
            public ulong AvailablePhysical;
            public ulong TotalPageFile;
            public ulong AvailablePageFile;
            public ulong TotalVirtual;
            public ulong AvailableVirtual;
            public ulong AvailableExtendedVirtual;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern bool GlobalMemoryStatusEx([In, Out] MemoryStatus buffer);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern bool EnumDisplaySettings(
            string deviceName, int modeNumber, ref DisplayMode mode);

        public static HardwareProfile DetectHardware()
        {
            HardwareProfile profile = new HardwareProfile();
            profile.LogicalProcessors = Math.Max(1, Environment.ProcessorCount);
            MemoryStatus memory = new MemoryStatus();
            if (GlobalMemoryStatusEx(memory)) profile.RamBytes = memory.TotalPhysical;
            profile.Gpu = DetectGpu();

            bool weakGpu = ContainsAny(profile.Gpu,
                "Microsoft Basic", "Standard VGA", "GMA ", "SiS ", "VIA ");
            bool high = !weakGpu && profile.RamBytes >= 8UL * 1024 * 1024 * 1024
                && profile.LogicalProcessors >= 4;
            bool balanced = !weakGpu && profile.RamBytes >= 4UL * 1024 * 1024 * 1024
                && profile.LogicalProcessors >= 2;
            profile.Level = high ? "eleve" : (balanced ? "equilibre" : "compatibilite");

            int nativeWidth;
            int nativeHeight;
            DetectNativeResolution(out nativeWidth, out nativeHeight);
            profile.NativeWidth = nativeWidth;
            profile.NativeHeight = nativeHeight;
            int maxWidth = high ? 3840 : (balanced ? 2560 : 1920);
            int maxHeight = high ? 2160 : (balanced ? 1440 : 1080);
            double scale = Math.Min(1.0,
                Math.Min((double)maxWidth / nativeWidth, (double)maxHeight / nativeHeight));
            profile.Width = Math.Max(800, ((int)Math.Floor(nativeWidth * scale) / 2) * 2);
            profile.Height = Math.Max(600, ((int)Math.Floor(nativeHeight * scale) / 2) * 2);
            return profile;
        }

        public static string DetectStatus()
        {
            try
            {
                HardwareProfile profile = DetectHardware();
                byte[] current = ReadSettings();
                int width = ReadInt32(current, 2);
                int height = ReadInt32(current, 6);
                byte expected26 = profile.Level == "eleve" ? (byte)0 : (byte)1;
                byte expected33 = profile.Level == "eleve" ? (byte)1 : (byte)4;
                if (width == profile.Width && height == profile.Height
                    && current.Length >= 35 && current[26] == expected26
                    && current[33] == expected33)
                    return "deja applique (" + width + " x " + height
                        + ", profil recommande " + profile.Level + ")";
                return "a appliquer : " + profile.Description;
            }
            catch (Exception ex)
            {
                return "indetermine (" + ex.Message + ")";
            }
        }

        public static string ValidateOnly()
        {
            HardwareProfile profile = DetectHardware();
            byte[] data = ReadSettings();
            if (data.Length < 35)
                throw new InvalidOperationException("Reglage LS3D_setup incomplet.");
            byte[] encodingProbe = new byte[35];
            WriteInt32(encodingProbe, 2, profile.Width);
            WriteInt32(encodingProbe, 6, profile.Height);
            WriteInt32(encodingProbe, 10, 32);
            if (ReadInt32(encodingProbe, 2) != profile.Width
                || ReadInt32(encodingProbe, 6) != profile.Height
                || ReadInt32(encodingProbe, 10) != 32)
                throw new InvalidOperationException("Encodage de resolution invalide.");
            if (profile.NativeWidth < profile.Width || profile.NativeHeight < profile.Height
                || profile.Width > 3840 || profile.Height > 2160)
                throw new InvalidOperationException("Resolution d'ecran incoherente.");
            return "Configuration graphique validable : " + profile.Description + ".";
        }

        public static void Apply(StateJournal journal, Action<string> progress)
        {
            HardwareProfile profile = DetectHardware();
            byte[] original = ReadSettings();
            if (original.Length < 35)
                throw new InvalidOperationException("Reglage LS3D_setup incomplet.");
            byte[] updated = (byte[])original.Clone();
            WriteInt32(updated, 2, profile.Width);
            WriteInt32(updated, 6, profile.Height);
            WriteInt32(updated, 10, 32);

            // Les deux valeurs ci-dessous sont celles du preset haute qualite 1.12.
            // Le reste du bloc (carte graphique, son et choix utilisateur) est preserve.
            if (profile.Level == "eleve")
            {
                updated[26] = 0;
                updated[33] = 1;
            }
            else
            {
                updated[26] = 1;
                updated[33] = 4;
            }
            WriteSettings(updated);
            journal.RecordGraphics(original, updated, profile.Level);
            InstallerCore.Report(progress, "Graphismes automatiques appliques : "
                + profile.Description + ".");
        }

        public static bool HasRestoreConflict(InstallState state)
        {
            if (state == null || state.InstalledGraphics == null) return false;
            try { return !BytesEqual(ReadSettings(), state.InstalledGraphics); }
            catch { return true; }
        }

        public static void Restore(InstallState state, Action<string> progress)
        {
            if (state == null || state.OriginalGraphics == null) return;
            if (HasRestoreConflict(state))
                throw new InvalidOperationException(
                    "Les reglages graphiques ont ete modifies depuis l'installation.");
            WriteSettings(state.OriginalGraphics);
            InstallerCore.Report(progress, "Reglages graphiques d'origine restaures.");
        }

        private static string DetectGpu()
        {
            try
            {
                string best = null;
                int score = Int32.MinValue;
                using (ManagementObjectSearcher searcher = new ManagementObjectSearcher(
                    "SELECT Name, AdapterRAM FROM Win32_VideoController"))
                using (ManagementObjectCollection results = searcher.Get())
                    foreach (ManagementObject item in results)
                    {
                        string name = Convert.ToString(item["Name"]);
                        int current = 0;
                        if (ContainsAny(name, "NVIDIA", "AMD", "Radeon", "GeForce"))
                            current += 100;
                        ulong ram = 0;
                        try { ram = Convert.ToUInt64(item["AdapterRAM"]); } catch { }
                        current += (int)Math.Min(50UL, ram / (256UL * 1024 * 1024));
                        if (current > score) { score = current; best = name; }
                    }
                return best;
            }
            catch { return null; }
        }

        private static void DetectNativeResolution(out int width, out int height)
        {
            DisplayMode mode = new DisplayMode();
            mode.Size = checked((short)Marshal.SizeOf(typeof(DisplayMode)));
            if (EnumDisplaySettings(null, EnumCurrentSettings, ref mode)
                && mode.PelsWidth >= 800 && mode.PelsHeight >= 600)
            {
                width = mode.PelsWidth;
                height = mode.PelsHeight;
                return;
            }
            width = Math.Max(800, Screen.PrimaryScreen.Bounds.Width);
            height = Math.Max(600, Screen.PrimaryScreen.Bounds.Height);
        }

        private static bool ContainsAny(string value, params string[] needles)
        {
            if (String.IsNullOrWhiteSpace(value)) return false;
            foreach (string needle in needles)
                if (value.IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0)
                    return true;
            return false;
        }

        private static byte[] ReadSettings()
        {
            using (RegistryKey root = RegistryKey.OpenBaseKey(
                RegistryHive.LocalMachine, RegistryView.Registry32))
            using (RegistryKey key = root.OpenSubKey(RegistryPath, false))
            {
                if (key == null)
                    throw new InvalidOperationException("Configuration H&D2 absente du registre.");
                byte[] value = key.GetValue("LS3D_setup") as byte[];
                if (value == null)
                    throw new InvalidOperationException("Reglage LS3D_setup absent du registre.");
                return (byte[])value.Clone();
            }
        }

        private static void WriteSettings(byte[] data)
        {
            using (RegistryKey root = RegistryKey.OpenBaseKey(
                RegistryHive.LocalMachine, RegistryView.Registry32))
            using (RegistryKey key = root.OpenSubKey(RegistryPath, true))
            {
                if (key == null)
                    throw new InvalidOperationException("Configuration H&D2 absente du registre.");
                key.SetValue("LS3D_setup", data, RegistryValueKind.Binary);
            }
        }

        private static int ReadInt32(byte[] data, int offset)
        {
            if (data == null || offset < 0 || offset > data.Length - 4)
                throw new InvalidOperationException("Reglage LS3D_setup incomplet.");
            return data[offset] | (data[offset + 1] << 8)
                | (data[offset + 2] << 16) | (data[offset + 3] << 24);
        }

        private static void WriteInt32(byte[] data, int offset, int value)
        {
            data[offset] = (byte)(value & 0xFF);
            data[offset + 1] = (byte)((value >> 8) & 0xFF);
            data[offset + 2] = (byte)((value >> 16) & 0xFF);
            data[offset + 3] = (byte)((value >> 24) & 0xFF);
        }

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left == null || right == null || left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}
