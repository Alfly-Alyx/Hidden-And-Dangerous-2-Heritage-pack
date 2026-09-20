using System;
using System.IO;

namespace HD2HeritageMasterBridge
{
    // Compatible implementation derived from Luigi Auriemma's
    // enctypex_decoder.c, GPL-2.0-or-later. This port is distributed under
    // the Heritage Pack's GPL-3.0-or-later licence.
    internal static class EnctypeX
    {
        private static int KeyIndex(
            byte[] state, int count, byte[] identity, ref int sum, ref int keyPosition)
        {
            if (count == 0) return 0;
            int mask = 1;
            if (count > 1)
                while (mask < count) mask = (mask << 1) + 1;

            int attempts = 0;
            while (true)
            {
                sum = state[sum & 255] + identity[keyPosition];
                keyPosition++;
                if (keyPosition >= identity.Length)
                {
                    keyPosition = 0;
                    sum += identity.Length;
                }
                int result = sum & mask;
                attempts++;
                if (attempts > 11) result %= count;
                if (result <= count) return result;
            }
        }

        private static byte[] Initialize(byte[] identity)
        {
            if (identity == null || identity.Length == 0)
                throw new InvalidDataException("Cle enctypeX vide.");
            byte[] state = new byte[261];
            for (int index = 0; index < 256; index++) state[index] = (byte)index;
            int sum = 0;
            int keyPosition = 0;
            for (int index = 255; index >= 0; index--)
            {
                int target = KeyIndex(
                    state, index, identity, ref sum, ref keyPosition);
                byte swap = state[index];
                state[index] = state[target];
                state[target] = swap;
            }
            state[256] = state[1];
            state[257] = state[3];
            state[258] = state[5];
            state[259] = state[7];
            state[260] = state[sum & 255];
            return state;
        }

        private static byte[] CreateState(
            byte[] response, byte[] gameKey, byte[] validate, out int encryptedOffset)
        {
            if (response == null || response.Length == 0)
                throw new InvalidDataException("Reponse enctypeX vide.");
            if (gameKey == null || gameKey.Length == 0)
                throw new InvalidDataException("Cle GameSpy vide.");
            if (validate == null || validate.Length != 8)
                throw new InvalidDataException("Jeton GameSpy invalide.");

            int headerLength = (response[0] ^ 0xec) + 2;
            if (headerLength > response.Length)
                throw new InvalidDataException("Entete enctypeX tronquee.");
            int challengeLength = response[headerLength - 1] ^ 0xea;
            encryptedOffset = headerLength + challengeLength;
            if (encryptedOffset > response.Length)
                throw new InvalidDataException("Defi enctypeX tronque.");

            byte[] identity = (byte[])validate.Clone();
            for (int index = 0; index < challengeLength; index++)
            {
                int slot = (gameKey[index % gameKey.Length] * index) & 7;
                identity[slot] ^= (byte)(identity[index & 7]
                    ^ response[headerLength + index]);
            }
            return Initialize(identity);
        }

        private static byte Transform(byte[] state, byte value, bool encrypt)
        {
            int rotor = state[256];
            int ratchet = (state[257] + state[rotor]) & 255;
            rotor = (rotor + 1) & 255;
            int avalanche = state[258];
            int lastPlain = state[259];
            int lastCipher = state[260];

            byte swap = state[lastCipher];
            state[lastCipher] = state[ratchet];
            state[ratchet] = state[lastPlain];
            state[lastPlain] = state[rotor];
            state[rotor] = swap;
            avalanche = (avalanche + state[swap]) & 255;

            byte transformed = (byte)(value
                ^ state[(state[avalanche] + state[rotor]) & 255]
                ^ state[state[(state[lastPlain] + state[lastCipher]
                    + state[ratchet]) & 255]]);
            state[256] = (byte)rotor;
            state[257] = (byte)ratchet;
            state[258] = (byte)avalanche;
            state[259] = encrypt ? value : transformed;
            state[260] = encrypt ? transformed : value;
            return transformed;
        }

        public static byte[] Decrypt(
            byte[] response, byte[] gameKey, byte[] validate)
        {
            int encryptedOffset;
            byte[] state = CreateState(
                response, gameKey, validate, out encryptedOffset);
            byte[] clear = new byte[response.Length - encryptedOffset];
            for (int index = 0; index < clear.Length; index++)
                clear[index] = Transform(
                    state, response[encryptedOffset + index], false);
            return clear;
        }

        public static byte[] EncryptWithHeader(
            byte[] templateResponse, byte[] clear, byte[] gameKey, byte[] validate)
        {
            int encryptedOffset;
            byte[] state = CreateState(
                templateResponse, gameKey, validate, out encryptedOffset);
            byte[] response = new byte[encryptedOffset + clear.Length];
            Buffer.BlockCopy(templateResponse, 0, response, 0, encryptedOffset);
            for (int index = 0; index < clear.Length; index++)
                response[encryptedOffset + index] = Transform(
                    state, clear[index], true);
            return response;
        }

        public static byte[] CreateHeader()
        {
            byte[] header = new byte[37];
            new Random().NextBytes(header);
            // OpenSpy uses ten crypt-header bytes and twenty-five challenge bytes.
            header[0] = (byte)(10 ^ 0xec);
            header[11] = (byte)(25 ^ 0xea);
            return header;
        }

        public static void SelfTest()
        {
            byte[] key = System.Text.Encoding.ASCII.GetBytes("sK8pQ9");
            byte[] validate = System.Text.Encoding.ASCII.GetBytes("Ghfg0Vhq");
            byte[] clear = System.Text.Encoding.ASCII.GetBytes(
                "HD2 Heritage Pack enctypeX roundtrip");
            byte[] header = CreateHeader();
            byte[] encrypted = EncryptWithHeader(header, clear, key, validate);
            byte[] decoded = Decrypt(encrypted, key, validate);
            if (decoded.Length != clear.Length)
                throw new InvalidDataException("Echec du test enctypeX.");
            for (int index = 0; index < clear.Length; index++)
                if (clear[index] != decoded[index])
                    throw new InvalidDataException("Echec du test enctypeX.");
        }
    }
}
