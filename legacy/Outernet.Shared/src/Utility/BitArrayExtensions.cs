using System.Collections;

namespace Outernet.Shared
{
    public static class BitArrayExtensions
    {
        // https://stackoverflow.com/questions/5063178/counting-bits-set-in-a-net-bitarray-class
        public static int NumSetBits(this BitArray bitArray)
        {
            int[] ints = new int[(bitArray.Count >> 5) + 1];
            bitArray.CopyTo(ints, 0);
            int count = 0;
            for (int i = 0; i < ints.Length; i++)
            {
                // System.Numerics.BitOperations.PopCount is no longer accessible in .NET 8 and I couldn't figure what is supposed to replace it
                //
                // count += System.Numerics.BitOperations.PopCount(dirtyFlags.Data);

                // Use Hamming weight algorithm (HAKMEM PopCount) to count set bits
                int c = ints[i];
                c = c - ((c >> 1) & 0x55555555);
                c = (c & 0x33333333) + ((c >> 2) & 0x33333333);
                c = ((c + (c >> 4) & 0xF0F0F0F) * 0x1010101) >> 24;
                count += c;
            }

            return count;
        }
    }
}