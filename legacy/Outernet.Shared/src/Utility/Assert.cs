using System;
using System.Diagnostics;

namespace Outernet.Shared
{
    public class AssertionFailedException : Exception
    {
        public AssertionFailedException(string message) : base(message) { }
    }

    public static class Assert
    {
        [Conditional("DEBUG")]
        public static void ASSERT(bool condition, string message)
        {
            // Breaks if debugging, but continues running if no debugger is attached.
            Debug.Assert(condition, message);

            // Throws an exception to ensure that the issue is logged in production builds.
            if (!condition)
            {
                throw new AssertionFailedException(message);
            }
        }
    }
}