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
        Initializing,
        Uploading,
        ReconstructionNotStarted,
        Reconstructing,
        Uploaded,
        MapCreated,
        Failed,
    }

    public enum CaptureClientPhase
    {
        Idle,
        Initializing,
        Uploading,
        Failed,
    }

    public class CaptureState : StateObject, IKeyedStateNode<Guid>
    {
        public Guid id { get; private set; }

        public StateValue<string> name { get; private set; }
        public StateValue<DeviceType> type { get; private set; }
        public StateValue<DateTime> recordedAt { get; private set; }
        public StateValue<CaptureUploadStatus> status { get; private set; }
        public StateValue<CaptureClientPhase> clientPhase { get; private set; }
        public StateValue<bool> serverCaptureExists { get; private set; }
        public StateValue<float> statusPercentage { get; private set; }
        public StateValue<Guid> reconstructionId { get; private set; }
        public StateValue<Guid> localizationMapId { get; private set; }
        public StateValue<bool> hasLocalFiles { get; private set; }
        public StateValue<ReconstructionRead> reconstruction { get; private set; }

        void IKeyedStateNode<Guid>.AssignKey(Guid key) => id = key;

        protected override void PostInitializeInternal()
        {
            status.Derive(
                Observables.ObservableCombineValues(
                    clientPhase, serverCaptureExists, reconstruction, localizationMapId,
                    ComputeStatus
                )
            );
        }

        private static CaptureUploadStatus ComputeStatus(
            CaptureClientPhase clientPhase,
            bool serverCaptureExists,
            ReconstructionRead reconstruction,
            Guid localizationMapId
        )
        {
            switch (clientPhase)
            {
                case CaptureClientPhase.Initializing: return CaptureUploadStatus.Initializing;
                case CaptureClientPhase.Uploading: return CaptureUploadStatus.Uploading;
                case CaptureClientPhase.Failed: return CaptureUploadStatus.Failed;
            }

            if (localizationMapId != Guid.Empty)
                return CaptureUploadStatus.MapCreated;

            if (reconstruction != null)
            {
                switch (reconstruction.Status)
                {
                    case ReconstructionStatus.Succeeded: return CaptureUploadStatus.Uploaded;
                    case ReconstructionStatus.Failed:
                    case ReconstructionStatus.Cancelled: return CaptureUploadStatus.Failed;
                    default: return CaptureUploadStatus.Reconstructing;
                }
            }

            return serverCaptureExists
                ? CaptureUploadStatus.ReconstructionNotStarted
                : CaptureUploadStatus.NotUploaded;
        }
    }
}
