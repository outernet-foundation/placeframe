using System;
using FofX.Stateful;
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

    public class SettingsState : ObservableObject
    {
        public ObservablePrimitive<string> domain { get; private set; }
        public ObservablePrimitive<string> username { get; private set; }
        public ObservablePrimitive<string> password { get; private set; }
    }

    public class AppState : ObservableObject
    {
        public ObservablePrimitive<string> placeframeAuthAudience { get; private set; }
        public ObservablePrimitive<bool> loginRequested { get; private set; }
        public ObservablePrimitive<AuthStatus> authStatus { get; private set; }
        public ObservablePrimitive<string> authError { get; private set; }
        public ObservablePrimitive<bool> loggedIn { get; private set; }

        public SettingsState settings { get; private set; }

        public ObservablePrimitive<AppMode> mode { get; private set; }

        public ObservablePrimitive<DeviceType> captureMode { get; private set; } =
            new ObservablePrimitive<DeviceType>(DeviceType.ARFoundation);
        public ObservablePrimitive<CaptureStatus> captureStatus { get; private set; }
        public ObservableDictionary<Guid, CaptureState> captures { get; private set; }

        public ObservablePrimitive<bool> localizing { get; private set; }
        public ObservablePrimitive<Guid> mapForLocalization { get; private set; }

        protected override void PostInitializeInternal()
        {
            loggedIn.RegisterDerived(
                _ => loggedIn.value = authStatus.value == AuthStatus.LoggedIn,
                ObservationScope.Self,
                authStatus
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

    public class CaptureState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<DeviceType> type { get; private set; }
        public ObservablePrimitive<DateTime> createdAt { get; private set; }
        public ObservablePrimitive<CaptureUploadStatus> status { get; private set; }
        public ObservablePrimitive<float> statusPercentage { get; private set; }
        public ObservablePrimitive<Guid> reconstructionId { get; private set; }
        public ObservablePrimitive<Guid> localizationMapId { get; private set; }
        public ObservablePrimitive<bool> hasLocalFiles { get; private set; }
        public ObservablePrimitive<ReconstructionManifest> manifest { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key) => id = key;
    }
}
