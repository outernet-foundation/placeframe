using System;
using System.Linq;
using System.Collections.Generic;

using Unity.Mathematics;
using UnityEngine;

using FofX.Stateful;

namespace Placeframe.MapRegistrationTool
{
    public enum AuthStatus
    {
        LoggedOut,
        LoggingIn,
        LoggedIn,
        Error,
    }

    public class AppState : ObservableObject
    {
        public ObservablePrimitive<string> placeframeAuthAudience;
        public ObservablePrimitive<bool> loginRequested { get; private set; }
        public ObservablePrimitive<AuthStatus> authStatus { get; private set; }
        public ObservablePrimitive<string> authError { get; private set; }
        public ObservablePrimitive<bool> loggedIn { get; private set; }

        public ObservablePrimitive<double2> roughGrainedLocation { get; private set; }
        public ObservableDictionary<Guid, TransformState> transforms { get; private set; }
        public ObservableDictionary<Guid, MapState> maps { get; private set; }

        public UserSettings settings { get; private set; }
        public ObservablePrimitive<double2?> location { get; private set; }
        public ObservablePrimitive<bool> locationContentLoaded { get; private set; }

        public ObservableSet<Guid> selectedObjects { get; private set; }

        public ObservablePrimitive<bool> saveRequested { get; private set; }
        public ObservablePrimitive<bool> hasUnsavedChanges { get; private set; }

        public IEnumerable<IObservableDictionary<Guid>> componentDictionaries
        {
            get
            {
                yield return maps;
                yield return transforms;
            }
        }

        protected override void PostInitializeInternal()
        {
            loggedIn.RegisterDerived(
                _ => loggedIn.value = authStatus.value == AuthStatus.LoggedIn,
                ObservationScope.Self,
                authStatus
            );
        }

        public IEnumerable<TransformState> SelectedTransforms()
            => SelectedTransforms(selectedObjects).Distinct();

        public bool HasSelectedTransforms()
            => SelectedTransforms(selectedObjects).FirstOrDefault() != default;

        private IEnumerable<TransformState> SelectedTransforms(IEnumerable<Guid> sceneObjects)
            => sceneObjects.Select(x => transforms[x]);
    }

    public class MapState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid uuid { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<int> id { get; private set; }

        [HideInInspectorUI]
        public ObservablePrimitive<Guid> reconstructionID { get; private set; }
        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<Lighting> lighting { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => uuid = key;
    }

    public class TransformState : ObservableObject, IKeyedObservableNode<Guid>
    {
        public Guid id { get; private set; }

        [InspectorType(typeof(ECEFPositionInspector), LabelType.Adaptive)]
        public ObservablePrimitive<double3> position { get; private set; }

        [InspectorType(typeof(ECEFRotationInspector), LabelType.Adaptive)]
        public ObservablePrimitive<Quaternion> rotation { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;
    }

    public class UserSettings : ObservableObject
    {
        public ObservablePrimitive<string> domain { get; private set; }
        public ObservablePrimitive<string> username { get; private set; }
        public ObservablePrimitive<string> password { get; private set; }
        public ObservablePrimitive<bool> loaded { get; private set; }
        public ObservablePrimitive<double2?> lastLocation { get; private set; }
        public ObservablePrimitive<bool> restoreLocationAutomatically { get; private set; }
        public ObservableList<LocationHistoryData> locationHistory { get; private set; }
        public ObservablePrimitive<float> nodeFetchRadius { get; private set; }
        public ObservableSet<string> activeTilesets { get; private set; }
    }

    public class LocationHistoryData : ObservableObject
    {
        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<double2> location { get; private set; }
    }
}
