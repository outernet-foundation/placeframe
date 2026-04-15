using System;

namespace Outernet.Logging
{
    [AttributeUsage(AttributeTargets.Field)]
    public class LogGroupColorAttribute : Attribute
    {
        public string HexColor { get; }
        public LogGroupColorAttribute(string hexColor) => HexColor = hexColor;
    }
}
