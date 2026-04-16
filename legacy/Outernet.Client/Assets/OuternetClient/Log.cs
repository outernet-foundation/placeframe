global using Log = Outernet.Logging.Log<Outernet.Client.LogGroup>;
global using Logger = Outernet.Logging.Logger<Outernet.Client.LogGroup>;

using System;
using Outernet.Logging;

namespace Outernet.Client
{
    [Flags]
    public enum LogGroup
    {
        None = 0,
        [LogGroupColor("#4E79A7")] Default = 1 << 0,
        [LogGroupColor("#E15759")] UncaughtException = 1 << 1,
        [LogGroupColor("#59A14F")] LoggingTests = 1 << 2,
        [LogGroupColor("#F28E2B")] Grpc = 1 << 3,
        [LogGroupColor("#B07AA1")] SyncedStateClient = 1 << 4,
        MagicLeapCamera = 1 << 5,
        [LogGroupColor("#9C755F")] Immersal = 1 << 6,
        [LogGroupColor("#76B7B2")] Rest = 1 << 7,
        [LogGroupColor("#EDC948")] Localizer = 1 << 8,
        PlaneDetector = 1 << 9,
        [LogGroupColor("#FF9DA7")] Permissions = 1 << 10,
        BugReports = 1 << 11,
        ContentManagement = 1 << 12,
        Stateful = 1 << 13
    }
}
