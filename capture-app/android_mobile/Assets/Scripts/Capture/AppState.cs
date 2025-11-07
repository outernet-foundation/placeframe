using System;
using FofX.Stateful;

namespace PlerionClient.Client
{
    public enum CaptureType
    {
        ARFoundation,
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
        public ObservablePrimitive<string> plerionAPIBaseUrl { get; private set; }
        public ObservablePrimitive<string> plerionKeycloakUrl { get; private set; }
        public ObservablePrimitive<CaptureType> captureMode { get; private set; }
        public ObservablePrimitive<CaptureStatus> captureStatus { get; private set; }
        public ObservableDictionary<Guid, CaptureState> captures { get; private set; }
    }

    public enum CaptureUploadStatus
    {
        NotUploaded,
        ReconstructionNotStarted,
        Initializing,
        Uploading,
        Reconstructing,
        Uploaded,
        Failed
    }

    public class CaptureState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<CaptureType> type { get; private set; }
        public ObservablePrimitive<CaptureUploadStatus> status { get; private set; }
        public ObservablePrimitive<float> statusPercentage { get; private set; }
        public ObservablePrimitive<Guid> reconstructionId { get; private set; }
        public ObservablePrimitive<Guid> localizationMapId { get; private set; }
        public ObservablePrimitive<bool> active { get; private set; } = new ObservablePrimitive<bool>(true);

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;
    }
}