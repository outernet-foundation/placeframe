using System;
using FofX.Stateful;
using ObserveThing;
using PlaceframeApiClient.Model;

namespace Placeframe.Client
{
    public enum CaptureStatus
    {
        Idle,
        Starting,
        Capturing,
        Stopping,
    }

    public enum AppMode
    {
        Capture,
        Validation,
    }

    public enum LocalizationSessionStatus
    {
        Inactive,
        Starting,
        Active,
        Stopping,
        Error,
    }

    public enum AuthStatus
    {
        LoggedOut,
        LoggingIn,
        LoggedIn,
        Error,
    }

    public enum ZedStatusKind
    {
        Unknown,
        Connecting,
        Ready,
        Recording,
        DegradedDiskLow,
        DegradedError,
        Unreachable,
        LostMidCapture,
    }

    public class SettingsState : StateObject
    {
        public StateValue<string> domain { get; private set; }
        public StateValue<string> username { get; private set; }
        public StateValue<string> password { get; private set; }
    }

    public class AppState : StateObject
    {
        public StateValue<string> placeframeAuthAudience { get; private set; }
        public StateValue<bool> loginRequested { get; private set; }
        public StateValue<AuthStatus> authStatus { get; private set; }
        public StateValue<string> authError { get; private set; }
        public StateValue<bool> loggedIn { get; private set; }

        public SettingsState settings { get; private set; }

        public StateValue<AppMode> mode { get; private set; }

        public StateValue<DeviceType> captureMode { get; private set; } =
            new StateValue<DeviceType>(DeviceType.ARFoundation);
        public StateValue<CaptureStatus> captureStatus { get; private set; }
        public StateDictionary<Guid, CaptureState> captures { get; private set; }

        public StateValue<ZedStatusKind> zedStatus { get; private set; } =
            new StateValue<ZedStatusKind>(ZedStatusKind.Unknown);

        public StateValue<bool> localizing { get; private set; }
        public StateValue<Guid> mapForLocalization { get; private set; }

        protected override void PostInitializeInternal()
        {
            loggedIn.Derive(
                authStatus.ObservableSelect(status => status == AuthStatus.LoggedIn)
            );
        }
    }

    public enum CaptureUploadStatus
    {
        NotUploaded,
        UploadRequested,
        Initializing,
        Uploading,
        ReconstructionNotStarted,
        ReconstructRequested,
        Reconstructing,
        Uploaded,
        CreateMapRequested,
        MapCreated,
        Failed,
    }

    public class CaptureState : StateObject, IKeyedStateNode<Guid>
    {
        public Guid id { get; private set; }

        public StateValue<string> name { get; private set; }
        public StateValue<DeviceType> type { get; private set; }
        public StateValue<DateTime> createdAt { get; private set; }
        public StateValue<CaptureUploadStatus> status { get; private set; }
        public StateValue<float> statusPercentage { get; private set; }
        public StateValue<Guid> reconstructionId { get; private set; }
        public StateValue<Guid> localizationMapId { get; private set; }
        public StateValue<bool> hasLocalFiles { get; private set; }
        public StateValue<ReconstructionManifest> manifest { get; private set; }

        void IKeyedStateNode<Guid>.AssignKey(Guid key) => id = key;
    }
}
