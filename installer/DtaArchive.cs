using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace HD2CommunityInstaller
{
    internal sealed class DtaEntry
    {
        public int Index;
        public string Name;
        public int Size;
        public int Blocks;
        public bool Encrypted;
        public long HeaderOffset;
        public long DataOffset;
        internal int NameLength;
    }

    internal sealed class DtaArchive : IDisposable
    {
        private readonly FileStream stream;
        private readonly ulong key;
        private readonly bool isIsd1;
        private readonly long archiveLength;
        public readonly List<DtaEntry> Entries = new List<DtaEntry>();

        public DtaArchive(string path)
        {
            stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read,
                131072, FileOptions.RandomAccess);
            archiveLength = stream.Length;
            byte[] signature = ReadExact(4);
            string version = Encoding.ASCII.GetString(signature);
            if (version != "ISD0" && version != "ISD1")
                throw new InvalidDataException("Signature DTA non prise en charge : " + version);
            isIsd1 = version == "ISD1";

            byte[] encryptedHeader = ReadExact(16);
            uint identifier = ReadUInt32(encryptedHeader, 0) & 0xFFFFFF00U;
            if (identifier == 0x7654A100U)
                key = 0x22BCDA987654A3F0UL;
            else if (identifier == 0xB438AB00U)
                key = 0xF26527FAB438D0A5UL;
            else if (identifier == 0x5D805600U)
                key = 0x10ACB2525D805270UL;
            else if (identifier == 0x0AB4EB00U)
                key = 0xCF7612980AB4E72DUL;
            else if (identifier == 0xA0A08600U)
                key = 0xA0A0A0A0A0A0A0A1UL;
            else
                throw new InvalidDataException(
                    "Archive DTA non reconnue (identifiant "
                    + identifier.ToString("X8") + ").");

            Xor(encryptedHeader);
            uint fileCount = ReadUInt32(encryptedHeader, 0);
            uint tableOffset = ReadUInt32(encryptedHeader, 4);
            uint tableSize = ReadUInt32(encryptedHeader, 8);
            if (fileCount == 0 || fileCount > Int32.MaxValue
                || tableSize < (ulong)fileCount * 28UL
                || (ulong)tableOffset + (ulong)fileCount * 28UL > (ulong)archiveLength)
                throw new InvalidDataException("Table de fichiers DTA invalide.");

            stream.Position = tableOffset;
            byte[] table = ReadExact(checked((int)fileCount * 28));
            Xor(table);
            for (int index = 0; index < (int)fileCount; index++)
                Entries.Add(ReadEntry(table, index));
        }

        public byte[] Read(DtaEntry entry)
        {
            if (entry == null || entry.Index < 0 || entry.Index >= Entries.Count)
                throw new ArgumentException("Entree DTA invalide.", "entry");
            stream.Position = entry.HeaderOffset + 32;
            byte[] encodedName = ReadExact(entry.NameLength);
            Xor(encodedName);
            if (!String.Equals(DecodeName(encodedName), entry.Name, StringComparison.Ordinal))
                throw new InvalidDataException("Nom DTA incoherent : " + entry.Name);

            byte[] blockSizes = null;
            byte[] blockTypes = null;
            if (isIsd1)
            {
                blockSizes = ReadExact(checked(entry.Blocks * 4));
                blockTypes = ReadExact(entry.Blocks);
                Xor(blockTypes);
            }

            using (MemoryStream result = new MemoryStream(entry.Size))
            {
                for (int blockIndex = 0; blockIndex < entry.Blocks; blockIndex++)
                {
                    int rawSize;
                    int type = 0;
                    if (isIsd1)
                    {
                        rawSize = checked((int)(ReadUInt32(blockSizes, blockIndex * 4) & 0xFFFFU));
                        type = blockTypes[blockIndex];
                    }
                    else
                    {
                        rawSize = checked((int)(ReadUInt32(ReadExact(4), 0) & 0xFFFFU));
                        if (rawSize < 1)
                            throw new InvalidDataException("Bloc DTA vide : " + entry.Name);
                    }
                    byte[] block = ReadExact(rawSize);
                    if (entry.Encrypted) Xor(block);
                    if (!isIsd1)
                    {
                        type = block[0];
                        byte[] payload = new byte[block.Length - 1];
                        Buffer.BlockCopy(block, 1, payload, 0, payload.Length);
                        block = payload;
                    }

                    if (type == 0)
                        result.Write(block, 0, block.Length);
                    else if (type == 1)
                    {
                        byte[] expanded = DecompressLzss(block, entry.Size - checked((int)result.Length));
                        result.Write(expanded, 0, expanded.Length);
                    }
                    else
                        throw new InvalidDataException(
                            "Compression DTA non prise en charge dans " + entry.Name + ".");
                    if (result.Length > entry.Size)
                        throw new InvalidDataException("Entree DTA trop grande : " + entry.Name);
                }
                if (result.Length != entry.Size)
                    throw new InvalidDataException(
                        "Taille DTA incoherente pour " + entry.Name + " ("
                        + result.Length + "/" + entry.Size + ").");
                return result.ToArray();
            }
        }

        private DtaEntry ReadEntry(byte[] table, int index)
        {
            int offset = checked(index * 28);
            int tableNameLength = ReadUInt16(table, offset + 2);
            long headerOffset = ReadUInt32(table, offset + 4);
            long dataOffset = ReadUInt32(table, offset + 8);
            if (headerOffset < 20 || headerOffset + 32 > archiveLength)
                throw new InvalidDataException("En-tete DTA hors archive.");

            stream.Position = headerOffset;
            byte[] header = ReadExact(32);
            Xor(header);
            uint rawSize = ReadUInt32(header, 16);
            uint rawBlocks = ReadUInt32(header, 20);
            int nameLength = isIsd1 ? header[28] : header[24];
            int flagsOffset = isIsd1 ? 29 : 25;
            if (nameLength != tableNameLength || rawSize > Int32.MaxValue
                || rawBlocks > Int32.MaxValue)
                throw new InvalidDataException("Metadonnees DTA incoherentes a l'entree " + index + ".");
            byte[] nameBytes = ReadExact(nameLength);
            Xor(nameBytes);
            string name = DecodeName(nameBytes);
            return new DtaEntry {
                Index = index,
                Name = name,
                Size = (int)rawSize,
                Blocks = (int)rawBlocks,
                Encrypted = (header[flagsOffset] & 0x80) != 0,
                HeaderOffset = headerOffset,
                DataOffset = dataOffset,
                NameLength = nameLength
            };
        }

        private byte[] DecompressLzss(byte[] source, int maximumOutput)
        {
            List<byte> destination = new List<byte>(Math.Min(maximumOutput, 1048576));
            int position = 0;
            while (position < source.Length)
            {
                if (position + 2 > source.Length)
                    throw new InvalidDataException("Groupe LZSS DTA tronque.");
                int value = (source[position] << 8) | source[position + 1];
                position += 2;
                if (value == 0)
                {
                    int segment = Math.Min(source.Length - position, 16);
                    EnsureOutput(destination.Count, segment, maximumOutput);
                    for (int i = 0; i < segment; i++) destination.Add(source[position + i]);
                    position += segment;
                    continue;
                }
                for (int bit = 0; bit < 16 && position < source.Length; bit++)
                {
                    if ((value & 0x8000) != 0)
                    {
                        if (position + 2 > source.Length)
                            throw new InvalidDataException("Reference LZSS DTA tronquee.");
                        int distance = (source[position] << 4) | (source[position + 1] >> 4);
                        int length = source[position + 1] & 0x0F;
                        if (distance == 0)
                        {
                            if (position + 4 > source.Length)
                                throw new InvalidDataException("Repetition LZSS DTA tronquee.");
                            length = ((length << 8) | source[position + 2]) + 16;
                            EnsureOutput(destination.Count, length, maximumOutput);
                            byte repeated = source[position + 3];
                            for (int i = 0; i < length; i++) destination.Add(repeated);
                            position += 4;
                        }
                        else
                        {
                            length += 3;
                            if (distance > destination.Count)
                                throw new InvalidDataException("Reference LZSS DTA invalide.");
                            EnsureOutput(destination.Count, length, maximumOutput);
                            for (int i = 0; i < length; i++)
                                destination.Add(destination[destination.Count - distance]);
                            position += 2;
                        }
                    }
                    else
                    {
                        EnsureOutput(destination.Count, 1, maximumOutput);
                        destination.Add(source[position]);
                        position++;
                    }
                    value = (value << 1) & 0xFFFF;
                }
            }
            return destination.ToArray();
        }

        private static void EnsureOutput(int current, int added, int maximum)
        {
            if (added < 0 || current > maximum - added)
                throw new InvalidDataException("Bloc LZSS DTA depasse la taille attendue.");
        }

        private byte[] ReadExact(int count)
        {
            if (count < 0 || stream.Position > archiveLength - count)
                throw new EndOfStreamException("Lecture DTA hors archive.");
            byte[] data = new byte[count];
            int read = 0;
            while (read < count)
            {
                int amount = stream.Read(data, read, count - read);
                if (amount <= 0) throw new EndOfStreamException("Archive DTA tronquee.");
                read += amount;
            }
            return data;
        }

        private void Xor(byte[] data)
        {
            byte[] keyBytes = BitConverter.GetBytes(key);
            for (int index = 0; index < data.Length; index++)
                data[index] ^= keyBytes[index % 8];
        }

        private static string DecodeName(byte[] data)
        {
            int length = data.Length;
            while (length > 0 && data[length - 1] == 0) length--;
            return Encoding.GetEncoding(1252).GetString(data, 0, length);
        }

        private static ushort ReadUInt16(byte[] data, int offset)
        {
            if (offset < 0 || offset > data.Length - 2)
                throw new InvalidDataException("Lecture DTA hors tampon.");
            return (ushort)(data[offset] | (data[offset + 1] << 8));
        }

        private static uint ReadUInt32(byte[] data, int offset)
        {
            if (offset < 0 || offset > data.Length - 4)
                throw new InvalidDataException("Lecture DTA hors tampon.");
            return (uint)data[offset] | ((uint)data[offset + 1] << 8)
                | ((uint)data[offset + 2] << 16) | ((uint)data[offset + 3] << 24);
        }

        public void Dispose()
        {
            stream.Dispose();
        }
    }
}
