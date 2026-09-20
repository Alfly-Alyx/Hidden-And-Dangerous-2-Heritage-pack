using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace HD2CustomMissionManager
{
    internal static class Program
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
                        message = MissionPackageCore.ValidateLibrary(args[1]);
                    else if (args[0] == "--catalogue-test" && args.Length == 4)
                        message = MissionPackageCore.BuildCatalogueForTest(
                            args[1], args[2], args[3]);
                    else if (args[0] == "--runtime-test" && args.Length == 3)
                        message = MissionPackageCore.RuntimeHashesForTest(args[1], args[2]);
                    else if (args[0] == "--integrate" && args.Length == 4)
                        message = MissionPackageCore.Integrate(args[1], args[2], args[3]);
                    else if (args[0] == "--restore" && args.Length == 2)
                        message = MissionPackageCore.Restore(args[1]);
                    else if (args[0] == "--import-user" && args.Length == 5)
                        message = MissionPackageCore.ImportUserMission(
                            args[1], args[2], args[3], args[4]);
                    else if (args[0] == "--detect-language" && args.Length == 2)
                        message = GameLanguageDetector.Detect(args[1]);
                    else if (args[0] == "--self-test-safety" && args.Length == 2)
                        message = MissionPackageCore.RunSafetySelfTests(args[1]);
                    else
                        throw new ArgumentException("Commande de validation inconnue.");
                    SafeConsoleWrite(message, false);
                    return 0;
                }
                catch (Exception error)
                {
                    SafeConsoleWrite("ERREUR : " + error.Message, true);
                    return 2;
                }
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SimpleMainForm());
            return 0;
        }

        private static void SafeConsoleWrite(string value, bool error)
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
