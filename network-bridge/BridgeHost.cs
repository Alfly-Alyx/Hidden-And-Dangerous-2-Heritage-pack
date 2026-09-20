using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;

namespace HD2HeritageMasterBridge
{
    internal sealed class UpstreamResult
    {
        public byte[] Raw;
        public ParsedList Parsed;
        public string Error;
    }

    internal sealed class BridgeHost : IDisposable
    {
        public const int MasterPort = 28910;
        private const int MaximumPacket = 65535;
        private static readonly string[] Upstreams = {
            "78.47.255.224", // established H&D2 community master
            "134.122.16.249" // OpenSpy
        };

        private readonly object sync = new object();
        private TcpListener listener;
        private Thread acceptThread;
        private bool stopping;

        public void Start()
        {
            lock (sync)
            {
                if (listener != null) return;
                stopping = false;
                listener = new TcpListener(IPAddress.Loopback, MasterPort);
                listener.Start(16);
                acceptThread = new Thread(AcceptLoop);
                acceptThread.IsBackground = true;
                acceptThread.Name = "HD2 master bridge";
                acceptThread.Start();
            }
            BridgeLog.Write("Pont demarre sur 127.0.0.1:" + MasterPort + ".");
        }

        public void Stop()
        {
            TcpListener active;
            lock (sync)
            {
                stopping = true;
                active = listener;
                listener = null;
            }
            if (active != null)
            {
                try { active.Stop(); }
                catch { }
            }
            if (acceptThread != null && acceptThread.IsAlive)
                acceptThread.Join(3000);
            BridgeLog.Write("Pont arrete.");
        }

        private void AcceptLoop()
        {
            while (!stopping)
            {
                try
                {
                    TcpClient client = listener.AcceptTcpClient();
                    ThreadPool.QueueUserWorkItem(HandleClient, client);
                }
                catch (SocketException)
                {
                    if (!stopping) BridgeLog.Write("Echec d'acceptation TCP.");
                }
                catch (ObjectDisposedException) { }
                catch (Exception error)
                {
                    BridgeLog.Write("Erreur d'acceptation: " + error.Message);
                }
            }
        }

        private static void HandleClient(object state)
        {
            using (TcpClient client = (TcpClient)state)
            {
                try
                {
                    client.ReceiveTimeout = 5000;
                    client.SendTimeout = 5000;
                    byte[] requestBytes = ReadPacket(client.GetStream());
                    ListRequest request;
                    if (!MasterProtocol.TryParseListRequest(requestBytes, out request))
                    {
                        RelayPrimary(client.GetStream(), requestBytes);
                        return;
                    }

                    UpstreamResult[] results = QueryBoth(
                        requestBytes, request.Validate);
                    List<ServerEndpoint> endpoints = new List<ServerEndpoint>();
                    UpstreamResult template = null;
                    foreach (UpstreamResult result in results)
                    {
                        if (result == null || result.Parsed == null) continue;
                        if (template == null) template = result;
                        endpoints.AddRange(result.Parsed.Servers);
                    }

                    byte[] header;
                    ParsedList baseList;
                    if (template == null)
                    {
                        header = EnctypeX.CreateHeader();
                        baseList = MasterProtocol.BuildEmptyTemplate(request);
                    }
                    else
                    {
                        header = template.Raw;
                        baseList = template.Parsed;
                    }
                    byte[] clear = MasterProtocol.BuildMergedList(baseList, endpoints);
                    byte[] response = EnctypeX.EncryptWithHeader(
                        header, clear, MasterProtocol.Hd2GameKey, request.Validate);
                    NetworkStream stream = client.GetStream();
                    stream.Write(response, 0, response.Length);
                    stream.Flush();
                    BridgeLog.Write("Liste fusionnee envoyee: "
                        + new HashSet<ServerEndpoint>(endpoints).Count + " serveur(s)."
                        + DescribeErrors(results));
                }
                catch (Exception error)
                {
                    BridgeLog.Write("Erreur client: " + error.Message);
                }
            }
        }

        private static string DescribeErrors(UpstreamResult[] results)
        {
            List<string> errors = new List<string>();
            for (int index = 0; index < results.Length; index++)
                if (results[index] == null || results[index].Parsed == null)
                    errors.Add(Upstreams[index] + ": "
                        + (results[index] == null ? "aucune reponse" : results[index].Error));
            return errors.Count == 0 ? String.Empty
                : " Source(s) indisponible(s): " + String.Join("; ", errors.ToArray());
        }

        private static byte[] ReadPacket(NetworkStream stream)
        {
            byte[] lengthBytes = ReadExactly(stream, 2);
            int length = (lengthBytes[0] << 8) | lengthBytes[1];
            if (length < 3 || length > MaximumPacket)
                throw new InvalidDataException("Longueur GameSpy invalide.");
            byte[] packet = new byte[length];
            packet[0] = lengthBytes[0];
            packet[1] = lengthBytes[1];
            byte[] rest = ReadExactly(stream, length - 2);
            Buffer.BlockCopy(rest, 0, packet, 2, rest.Length);
            return packet;
        }

        private static byte[] ReadExactly(Stream stream, int count)
        {
            byte[] data = new byte[count];
            int offset = 0;
            while (offset < count)
            {
                int read = stream.Read(data, offset, count - offset);
                if (read <= 0) throw new EndOfStreamException();
                offset += read;
            }
            return data;
        }

        private static UpstreamResult[] QueryBoth(
            byte[] request, byte[] validate)
        {
            UpstreamResult[] results = new UpstreamResult[Upstreams.Length];
            Thread[] workers = new Thread[Upstreams.Length];
            for (int index = 0; index < Upstreams.Length; index++)
            {
                int slot = index;
                workers[index] = new Thread(delegate() {
                    results[slot] = QueryUpstream(
                        Upstreams[slot], request, validate);
                });
                workers[index].IsBackground = true;
                workers[index].Name = "HD2 master query " + Upstreams[index];
                workers[index].Start();
            }

            DateTime deadline = DateTime.UtcNow.AddMilliseconds(6500);
            foreach (Thread worker in workers)
            {
                int remaining = (int)Math.Max(0,
                    (deadline - DateTime.UtcNow).TotalMilliseconds);
                if (remaining > 0) worker.Join(remaining);
            }

            // A timed-out background query may still finish after this method
            // returns.  Copy the current references so that a late result cannot
            // alter the response already being assembled for this client.
            UpstreamResult[] snapshot = new UpstreamResult[results.Length];
            Array.Copy(results, snapshot, results.Length);
            return snapshot;
        }

        private static UpstreamResult QueryUpstream(
            string host, byte[] request, byte[] validate)
        {
            UpstreamResult result = new UpstreamResult();
            try
            {
                using (TcpClient client = Connect(host, MasterPort, 3000))
                {
                    client.ReceiveTimeout = 3000;
                    client.SendTimeout = 3000;
                    NetworkStream stream = client.GetStream();
                    stream.Write(request, 0, request.Length);
                    stream.Flush();
                    MemoryStream response = new MemoryStream();
                    byte[] buffer = new byte[4096];
                    while (response.Length < 1024 * 1024)
                    {
                        int read;
                        try { read = stream.Read(buffer, 0, buffer.Length); }
                        catch (IOException) { break; }
                        if (read <= 0) break;
                        response.Write(buffer, 0, read);
                        try
                        {
                            byte[] raw = response.ToArray();
                            byte[] clear = EnctypeX.Decrypt(
                                raw, MasterProtocol.Hd2GameKey, validate);
                            ParsedList parsed = MasterProtocol.ParseList(clear);
                            result.Raw = raw;
                            result.Parsed = parsed;
                            return result;
                        }
                        catch (InvalidDataException) { }
                    }
                    if (response.Length == 0)
                        throw new IOException("reponse vide");
                    byte[] finalRaw = response.ToArray();
                    result.Raw = finalRaw;
                    result.Parsed = MasterProtocol.ParseList(EnctypeX.Decrypt(
                        finalRaw, MasterProtocol.Hd2GameKey, validate));
                }
            }
            catch (Exception error)
            {
                result.Error = error.Message;
            }
            return result;
        }

        private static TcpClient Connect(string host, int port, int timeout)
        {
            TcpClient client = new TcpClient(AddressFamily.InterNetwork);
            IAsyncResult pending = client.BeginConnect(host, port, null, null);
            if (!pending.AsyncWaitHandle.WaitOne(timeout))
            {
                client.Close();
                throw new TimeoutException("delai de connexion depasse");
            }
            client.EndConnect(pending);
            return client;
        }

        private static void RelayPrimary(NetworkStream destination, byte[] request)
        {
            using (TcpClient upstream = Connect(Upstreams[0], MasterPort, 3000))
            {
                upstream.ReceiveTimeout = 3000;
                NetworkStream source = upstream.GetStream();
                source.Write(request, 0, request.Length);
                source.Flush();
                byte[] buffer = new byte[4096];
                while (true)
                {
                    int read;
                    try { read = source.Read(buffer, 0, buffer.Length); }
                    catch (IOException) { break; }
                    if (read <= 0) break;
                    destination.Write(buffer, 0, read);
                }
                destination.Flush();
            }
        }

        public void Dispose()
        {
            Stop();
        }
    }

    internal static class BridgeLog
    {
        private static readonly object Sync = new object();

        public static void Write(string message)
        {
            try
            {
                string root = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
                    "HD2 Community Pack");
                Directory.CreateDirectory(root);
                string path = Path.Combine(root, "network-bridge.log");
                lock (Sync)
                {
                    if (File.Exists(path) && new FileInfo(path).Length > 1024 * 1024)
                        File.Delete(path);
                    File.AppendAllText(path,
                        DateTime.UtcNow.ToString("u") + " " + message + Environment.NewLine);
                }
            }
            catch { }
        }
    }
}
