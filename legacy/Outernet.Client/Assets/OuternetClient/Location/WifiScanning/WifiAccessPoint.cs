using System;

namespace Outernet.Client.Location
{
    [Serializable]
    public class WifiAccessPoint
    {
        public string macAddress;
        public int signalStrength;
        public int SignalToNoiseRatio = 0;
        public int channel;
    }
}