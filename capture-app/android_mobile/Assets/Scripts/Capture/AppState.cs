using System;
using FofX.Stateful;

namespace PlerionClient.Client
{
    public enum CaptureType
    {
        Local,
        Zed
    }

    public enum CaptureStatus
    {
        Idle,
        Starting,
        Capturing,
        Stopping
    }

    public class AppState : ObservableObject
    {
        public ObservablePrimitive<bool> loggedIn { get; private set; }
        public ObservablePrimitive<string> plerionAPIBaseUrl { get; private set; }
        public ObservablePrimitive<CaptureType> captureMode { get; private set; }
        public ObservablePrimitive<CaptureStatus> captureStatus { get; private set; }
        public ObservableDictionary<Guid, CaptureState> captures { get; private set; }
    }

    public class CaptureState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<CaptureType> type { get; private set; }
        public ObservablePrimitive<bool> uploaded { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;
    }
}