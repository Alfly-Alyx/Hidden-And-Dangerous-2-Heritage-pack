using System;
using System.Collections.Generic;
using System.IO;

namespace HD2CommunityInstaller
{
    internal sealed class TreePatchStats
    {
        public bool Placeholder;
        public int Records;
        public int WarningFlags;
        public int FailureFlags;
        public int BothFlags;
        public int BoundaryLabels;
        public int ChangedRecords { get { return WarningFlags + FailureFlags + BothFlags; } }
        public int ChangedItems { get { return ChangedRecords + BoundaryLabels; } }
    }

    internal static class TreeKlzPatcher
    {
        private const uint Magic = 0x43666947;
        private const int CollisionHeaderSize = 164;
        private const byte MissionAreaMask = 0x60;

        private static readonly int[,] Sections = {
            { 72, 32 }, { 88, 32 }, { 80, 192 },
            { 112, 32 }, { 104, 160 }, { 96, 32 }
        };

        public static TreePatchStats Patch(byte[] data)
        {
            TreePatchStats stats = new TreePatchStats();
            RenameBoundaryLabels(data, stats);
            foreach (int offset in RecordOffsets(data, stats))
            {
                byte flags = (byte)(data[offset + 1] & MissionAreaMask);
                if (flags == 0x40) stats.WarningFlags++;
                else if (flags == 0x20) stats.FailureFlags++;
                else if (flags == MissionAreaMask) stats.BothFlags++;
                data[offset + 1] = (byte)(data[offset + 1] & ~MissionAreaMask);
            }
            return stats;
        }

        public static TreePatchStats Audit(byte[] data)
        {
            byte[] copy = (byte[])data.Clone();
            return Patch(copy);
        }

        private static void RenameBoundaryLabels(byte[] data, TreePatchStats stats)
        {
            if (data == null) throw new ArgumentNullException("data");
            if (data.Length == 16) return;
            if (data.Length < 24 || ReadUInt32(data, 0) != Magic)
                throw new InvalidDataException("Signature tree.klz invalide.");

            uint count = ReadUInt32(data, 12);
            if (count > (data.Length - 24) / 4)
                throw new InvalidDataException("Table des objets tree.klz hors fichier.");
            byte[] marker = { (byte)'H', (byte)'2', (byte)'B', (byte)'O', (byte)'R', (byte)'D' };
            for (uint index = 0; index < count; index++)
            {
                uint objectOffset = ReadUInt32(data, checked(24 + (int)index * 4));
                long labelOffset = (long)objectOffset + 4;
                if (labelOffset < 0 || labelOffset >= data.Length)
                    throw new InvalidDataException("Etiquette d'objet tree.klz hors fichier.");
                int end = checked((int)labelOffset);
                while (end < data.Length && data[end] != 0) end++;
                if (end >= data.Length)
                    throw new InvalidDataException("Etiquette d'objet tree.klz non terminee.");

                bool changed = false;
                for (int position = checked((int)labelOffset); position <= end - 6; position++)
                {
                    if (!AsciiEquals(data[position], 'b')
                        || !AsciiEquals(data[position + 1], 'o')
                        || !AsciiEquals(data[position + 2], 'r')
                        || !AsciiEquals(data[position + 3], 'd')
                        || !AsciiEquals(data[position + 4], 'e')
                        || !AsciiEquals(data[position + 5], 'r')) continue;
                    Buffer.BlockCopy(marker, 0, data, position, marker.Length);
                    changed = true;
                    position += marker.Length - 1;
                }
                if (changed) stats.BoundaryLabels++;
            }
        }

        private static bool AsciiEquals(byte value, char expectedLower)
        {
            if (value >= (byte)'A' && value <= (byte)'Z') value += 32;
            return value == (byte)expectedLower;
        }

        private static IEnumerable<int> RecordOffsets(byte[] data, TreePatchStats stats)
        {
            if (data == null) throw new ArgumentNullException("data");
            if (data.Length == 16)
            {
                stats.Placeholder = true;
                yield break;
            }
            if (data.Length < 24 || ReadUInt32(data, 0) != Magic)
                throw new InvalidDataException("Signature tree.klz invalide.");

            long collision = ReadUInt32(data, 8);
            if (collision < 24 || collision + CollisionHeaderSize > data.Length)
                throw new InvalidDataException("En-tete de collisions tree.klz hors fichier.");
            uint gridX = ReadUInt32(data, checked((int)collision + 24));
            uint gridZ = ReadUInt32(data, checked((int)collision + 28));
            uint gridY = ReadUInt32(data, checked((int)collision + 48));
            if (gridX == 0 || gridY == 0 || gridZ == 0)
                throw new InvalidDataException("Dimensions de grille tree.klz invalides.");

            long position = collision + CollisionHeaderSize
                + 4L * ((long)gridX + 1 + (long)gridY + 1 + (long)gridZ + 1)
                + 16;
            for (int section = 0; section < Sections.GetLength(0); section++)
            {
                int countOffset = Sections[section, 0];
                int recordSize = Sections[section, 1];
                uint count = ReadUInt32(data, checked((int)collision + countOffset));
                if (count > data.Length / recordSize)
                    throw new InvalidDataException("Nombre de collisions tree.klz invraisemblable.");
                long end = position + (long)count * recordSize;
                if (position < 0 || end > data.Length)
                    throw new InvalidDataException("Table de collisions tree.klz hors fichier.");
                for (uint index = 0; index < count; index++)
                {
                    stats.Records++;
                    yield return checked((int)(position + (long)index * recordSize));
                }
                position = end;
            }
        }

        private static uint ReadUInt32(byte[] data, int offset)
        {
            if (offset < 0 || offset > data.Length - 4)
                throw new InvalidDataException("Lecture tree.klz hors fichier.");
            return (uint)data[offset] | ((uint)data[offset + 1] << 8)
                | ((uint)data[offset + 2] << 16) | ((uint)data[offset + 3] << 24);
        }
    }
}
