global using Log = Outernet.Logging.Log<LogGroup>;
global using Logger = Outernet.Logging.Logger<LogGroup>;

using System;
using Outernet.Logging;

[Flags]
public enum LogGroup
{
    None = 0,
    [LogGroupColor("#4E79A7")] Default = 1 << 0,
    [LogGroupColor("#E15759")] UncaughtException = 1 << 1,
    [LogGroupColor("#76B7B2")] Rest = 1 << 2,
    [LogGroupColor("#EDC948")] Localizer = 1 << 3,
    [LogGroupColor("#59A14F")] Capture = 1 << 4,
    [LogGroupColor("#B07AA1")] Zed = 1 << 5,
}
