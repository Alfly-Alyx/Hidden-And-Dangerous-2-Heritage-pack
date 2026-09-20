using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;

namespace HD2HeritageMasterBridge
{
    internal sealed class ListRequest
    {
        public string ForGame;
        public string FromGame;
        public byte[] Validate;
        public string[] Fields;
    }

    internal struct ServerEndpoint : IEquatable<ServerEndpoint>
    {
        public readonly uint Address;
        public readonly ushort Port;

        public ServerEndpoint(uint address, ushort port)
        {
            Address = address;
            Port = port;
        }

        public bool Equals(ServerEndpoint other)
        {
            return Address == other.Address && Port == other.Port;
        }

        public override bool Equals(object value)
        {
            return value is ServerEndpoint && Equals((ServerEndpoint)value);
        }

        public override int GetHashCode()
        {
            return unchecked(((int)Address * 397) ^ Port);
        }

        public override string ToString()
        {
            return String.Format("{0}.{1}.{2}.{3}:{4}",
                (Address >> 24) & 255, (Address >> 16) & 255,
                (Address >> 8) & 255, Address & 255, Port);
        }
    }

    internal sealed class ParsedList
    {
        public byte[] Clear;
        public int TableEnd;
        public readonly List<ServerEndpoint> Servers =
            new List<ServerEndpoint>();
    }

    internal static class MasterProtocol
    {
        public static readonly byte[] Hd2GameKey =
            Encoding.ASCII.GetBytes("sK8pQ9");

        private static string ReadNts(byte[] data, ref int offset)
        {
            int start = offset;
            while (offset < data.Length && data[offset] != 0) offset++;
            if (offset >= data.Length)
                throw new InvalidDataException("Chaine GameSpy tronquee.");
            string value = Encoding.ASCII.GetString(data, start, offset - start);
            offset++;
            return value;
        }

        public static bool TryParseListRequest(byte[] packet, out ListRequest request)
        {
            request = null;
            try
            {
                if (packet == null || packet.Length < 18) return false;
                int declared = (packet[0] << 8) | packet[1];
                if (declared != packet.Length || packet[2] != 0) return false;
                int offset = 3;
                offset += 2; // protocol and encoding versions
                offset += 4; // game version
                string forGame = ReadNts(packet, ref offset);
                string fromGame = ReadNts(packet, ref offset);
                if (offset + 8 > packet.Length) return false;
                byte[] validate = new byte[8];
                Buffer.BlockCopy(packet, offset, validate, 0, validate.Length);
                offset += validate.Length;
                ReadNts(packet, ref offset); // filter
                string fields = ReadNts(packet, ref offset);
                request = new ListRequest {
                    ForGame = forGame,
                    FromGame = fromGame,
                    Validate = validate,
                    Fields = fields.Split(
                        new[] { '\\' }, StringSplitOptions.RemoveEmptyEntries)
                };
                return String.Equals(forGame, "hd2", StringComparison.OrdinalIgnoreCase)
                    && String.Equals(fromGame, "hd2", StringComparison.OrdinalIgnoreCase);
            }
            catch
            {
                request = null;
                return false;
            }
        }

        private static int SkipTables(byte[] clear, out byte[] fieldTypes)
        {
            if (clear == null || clear.Length < 7)
                throw new InvalidDataException("Liste GameSpy tronquee.");
            int offset = 6;
            int fieldCount = clear[offset++];
            fieldTypes = new byte[fieldCount];
            for (int index = 0; index < fieldCount; index++)
            {
                if (offset >= clear.Length)
                    throw new InvalidDataException("Table de champs tronquee.");
                fieldTypes[index] = clear[offset++];
                ReadNts(clear, ref offset);
            }
            if (offset >= clear.Length)
                throw new InvalidDataException("Table de valeurs tronquee.");
            int popularCount = clear[offset++];
            for (int index = 0; index < popularCount; index++)
                ReadNts(clear, ref offset);
            return offset;
        }

        public static ParsedList ParseList(byte[] clear)
        {
            byte[] fieldTypes;
            int offset = SkipTables(clear, out fieldTypes);
            ParsedList parsed = new ParsedList {
                Clear = clear,
                TableEnd = offset
            };
            int defaultPort = (clear[4] << 8) | clear[5];
            while (offset < clear.Length)
            {
                int flags = clear[offset++];
                if (flags == 0 && offset + 4 <= clear.Length
                    && clear[offset] == 255 && clear[offset + 1] == 255
                    && clear[offset + 2] == 255 && clear[offset + 3] == 255)
                    return parsed;
                if ((flags & 0x80) != 0)
                    throw new InvalidDataException(
                        "Regles GameSpy completes non prises en charge.");
                if (offset + 4 > clear.Length)
                    throw new InvalidDataException("Adresse GameSpy tronquee.");
                uint address = ((uint)clear[offset] << 24)
                    | ((uint)clear[offset + 1] << 16)
                    | ((uint)clear[offset + 2] << 8)
                    | clear[offset + 3];
                offset += 4;
                int port = defaultPort;
                if ((flags & 0x10) != 0)
                {
                    if (offset + 2 > clear.Length)
                        throw new InvalidDataException("Port GameSpy tronque.");
                    port = (clear[offset] << 8) | clear[offset + 1];
                    offset += 2;
                }
                if ((flags & 0x02) != 0) offset += 4;
                if ((flags & 0x20) != 0) offset += 2;
                if ((flags & 0x08) != 0) offset += 4;
                if (offset > clear.Length)
                    throw new InvalidDataException("Adresse etendue GameSpy tronquee.");

                if ((flags & 0x40) != 0)
                {
                    for (int index = 0; index < fieldTypes.Length; index++)
                    {
                        if (offset >= clear.Length)
                            throw new InvalidDataException("Valeur GameSpy tronquee.");
                        if (fieldTypes[index] == 0)
                        {
                            int marker = clear[offset++];
                            if (marker == 255) ReadNts(clear, ref offset);
                        }
                        else if (fieldTypes[index] == 2)
                            offset += 2;
                        else
                            offset++;
                        if (offset > clear.Length)
                            throw new InvalidDataException("Valeur GameSpy tronquee.");
                    }
                }
                parsed.Servers.Add(new ServerEndpoint(address, (ushort)port));
            }
            throw new InvalidDataException("Fin de liste GameSpy absente.");
        }

        public static byte[] BuildMergedList(
            ParsedList template, IEnumerable<ServerEndpoint> endpoints)
        {
            MemoryStream output = new MemoryStream();
            output.Write(template.Clear, 0, template.TableEnd);
            HashSet<ServerEndpoint> unique = new HashSet<ServerEndpoint>();
            foreach (ServerEndpoint endpoint in endpoints)
                unique.Add(endpoint);
            List<ServerEndpoint> ordered = new List<ServerEndpoint>(unique);
            ordered.Sort(delegate(ServerEndpoint left, ServerEndpoint right) {
                int address = left.Address.CompareTo(right.Address);
                return address != 0 ? address : left.Port.CompareTo(right.Port);
            });
            foreach (ServerEndpoint endpoint in ordered)
            {
                output.WriteByte(0x10);
                output.WriteByte((byte)((endpoint.Address >> 24) & 255));
                output.WriteByte((byte)((endpoint.Address >> 16) & 255));
                output.WriteByte((byte)((endpoint.Address >> 8) & 255));
                output.WriteByte((byte)(endpoint.Address & 255));
                output.WriteByte((byte)((endpoint.Port >> 8) & 255));
                output.WriteByte((byte)(endpoint.Port & 255));
            }
            output.WriteByte(0);
            output.WriteByte(255);
            output.WriteByte(255);
            output.WriteByte(255);
            output.WriteByte(255);
            return output.ToArray();
        }

        public static ParsedList BuildEmptyTemplate(ListRequest request)
        {
            MemoryStream output = new MemoryStream();
            output.WriteByte(127);
            output.WriteByte(0);
            output.WriteByte(0);
            output.WriteByte(1);
            output.WriteByte((byte)(11004 >> 8));
            output.WriteByte((byte)(11004 & 255));
            if (request.Fields.Length > 255)
                throw new InvalidDataException("Trop de champs GameSpy.");
            output.WriteByte((byte)request.Fields.Length);
            foreach (string field in request.Fields)
            {
                output.WriteByte(0);
                byte[] name = Encoding.ASCII.GetBytes(field);
                output.Write(name, 0, name.Length);
                output.WriteByte(0);
            }
            output.WriteByte(0);
            byte[] clear = output.ToArray();
            return new ParsedList { Clear = clear, TableEnd = clear.Length };
        }

        public static void SelfTest()
        {
            byte[] packet = new byte[] {
                0, 40, 0, 1, 3, 1, 0, 0, 0,
                (byte)'h', (byte)'d', (byte)'2', 0,
                (byte)'h', (byte)'d', (byte)'2', 0,
                (byte)'G', (byte)'h', (byte)'f', (byte)'g',
                (byte)'0', (byte)'V', (byte)'h', (byte)'q',
                0, (byte)'\\', (byte)'h', (byte)'o', (byte)'s',
                (byte)'t', (byte)'n', (byte)'a', (byte)'m', (byte)'e', 0,
                0, 0, 0, 0
            };
            ListRequest request;
            if (!TryParseListRequest(packet, out request))
                throw new InvalidDataException("Echec du test de requete GameSpy.");
            ParsedList template = BuildEmptyTemplate(request);
            byte[] merged = BuildMergedList(template, new[] {
                new ServerEndpoint(0x4e2fffe0, 11004),
                new ServerEndpoint(0x4e2fffe0, 11004)
            });
            ParsedList parsed = ParseList(merged);
            if (parsed.Servers.Count != 1)
                throw new InvalidDataException("Echec du test de fusion GameSpy.");
        }
    }
}
