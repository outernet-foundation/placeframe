using System;
using PlaceframeApiClient.Model;

namespace Placeframe.Core
{
    public readonly struct LocalCapture
    {
        public readonly Guid Id;
        public readonly DateTime RecordedAt;
        public readonly DeviceType Type;

        public LocalCapture(Guid id, DateTime recordedAt, DeviceType type)
        {
            Id = id;
            RecordedAt = recordedAt;
            Type = type;
        }
    }
}
