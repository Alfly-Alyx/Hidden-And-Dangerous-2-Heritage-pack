using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace HD2CustomMissionManager
{
    internal static class SoloPackProgram
    {
        [DllImport("kernel32.dll")]
        private static extern bool AttachConsole(int processId);

        [STAThread]
        private static int Main(string[] args)
        {
            if (args.Length > 0)
            {
                AttachConsole(-1);
                try
                {
                    string message;
                    if (args[0] == "--check" && args.Length == 2)
                        message = SoloMissionPackBuilder.Check(args[1]);
                    else if (args[0] == "--install" && args.Length == 2)
                        message = SoloMissionPackBuilder.Install(args[1], Console.WriteLine);
                    else if (args[0] == "--restore" && args.Length == 2)
                        message = SoloMissionPackBuilder.Restore(args[1], Console.WriteLine);
                    else if (args[0] == "--export-library" && args.Length == 3)
                        message = SoloMissionPackBuilder.ExportLibrary(
                            args[1], args[2], Console.WriteLine);
                    else if (args[0] == "--self-test" && args.Length == 1)
                        message = SoloMissionPackBuilder.RunSelfTests();
                    else
                        throw new ArgumentException("Commande inconnue.");
                    SafeWrite(message, false);
                    return 0;
                }
                catch (Exception error)
                {
                    SafeWrite("ERREUR : " + error.Message, true);
                    return 2;
                }
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SoloMissionPackForm());
            return 0;
        }

        private static void SafeWrite(string value, bool error)
        {
            try
            {
                Console.OutputEncoding = Encoding.UTF8;
                if (error) Console.Error.WriteLine(value);
                else Console.WriteLine(value);
            }
            catch (IOException) { }
        }
    }
}
