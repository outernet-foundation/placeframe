using System;
using PlaceframeApiClient.Model;

namespace Placeframe.Core
{
    public readonly struct LocalCapture
    {
        public readonly Guid Id;
        public readonly string Name;
        public readonly DateTime RecordedAt;
        public readonly DeviceType Type;
        public readonly long? SizeBytes;

        public LocalCapture(Guid id, string name, DateTime recordedAt, DeviceType type, long? sizeBytes = null)
        {
            Id = id;
            Name = name;
            RecordedAt = recordedAt;
            Type = type;
            SizeBytes = sizeBytes;
        }
    }
}
