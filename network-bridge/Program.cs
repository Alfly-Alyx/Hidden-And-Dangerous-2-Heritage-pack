using System;
using System.ServiceProcess;
using System.Threading;

namespace HD2HeritageMasterBridge
{
    internal sealed class MasterBridgeService : ServiceBase
    {
        private BridgeHost host;

        public MasterBridgeService()
        {
            ServiceName = "HD2HeritageMasterBridge";
            AutoLog = true;
            CanStop = true;
        }

        protected override void OnStart(string[] args)
        {
            host = new BridgeHost();
            host.Start();
        }

        protected override void OnStop()
        {
            if (host != null)
            {
                host.Dispose();
                host = null;
            }
        }
    }

    internal static class Program
    {
        private static int Main(string[] args)
        {
            try
            {
                if (args.Length > 0 && String.Equals(
                    args[0], "--self-test", StringComparison.OrdinalIgnoreCase))
                {
                    EnctypeX.SelfTest();
                    MasterProtocol.SelfTest();
                    Console.WriteLine("Pont GameSpy H&D2 : tests internes reussis.");
                    return 0;
                }
                if (args.Length > 0 && String.Equals(
                    args[0], "--console", StringComparison.OrdinalIgnoreCase))
                {
                    using (BridgeHost host = new BridgeHost())
                    using (ManualResetEvent stop = new ManualResetEvent(false))
                    {
                        Console.CancelKeyPress += delegate(object sender, ConsoleCancelEventArgs e) {
                            e.Cancel = true;
                            stop.Set();
                        };
                        host.Start();
                        Console.WriteLine(
                            "Pont H&D2 actif sur 127.0.0.1:28910. Ctrl+C pour arreter.");
                        stop.WaitOne();
                    }
                    return 0;
                }
                ServiceBase.Run(new MasterBridgeService());
                return 0;
            }
            catch (Exception error)
            {
                BridgeLog.Write("Erreur fatale: " + error);
                Console.Error.WriteLine(error);
                return 1;
            }
        }
    }
}
