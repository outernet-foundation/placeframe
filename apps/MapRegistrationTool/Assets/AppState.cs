using System;
using System.Linq;
using System.Collections.Generic;

using Unity.Mathematics;
using UnityEngine;

using FofX.Stateful;

namespace Outernet.MapRegistrationTool
{
    public class AppState : ObservableObject
    {
        public ObservablePrimitive<bool> loggedIn { get; private set; }
        public ObservablePrimitive<double2> roughGrainedLocation { get; private set; }
        public ObservableDictionary<Guid, TransformState> transforms { get; private set; }
        public ObservableDictionary<Guid, MapState> maps { get; private set; }

        public ObservablePrimitive<double4x4> ecefToUnityWorldMatrix { get; private set; } = new ObservablePrimitive<double4x4>(double4x4.identity);
        public ObservablePrimitive<double4x4> unityWorldToEcefMatrix { get; private set; }

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
            unityWorldToEcefMatrix.RegisterDerived(
                _ => unityWorldToEcefMatrix.value = math.inverse(ecefToUnityWorldMatrix.value),
                ObservationScope.Self,
                ecefToUnityWorldMatrix
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

        [InspectorType(typeof(UIElements.ECEFPositionInspector), LabelType.Adaptive)]
        public ObservablePrimitive<double3> position { get; private set; }

        [InspectorType(typeof(UIElements.ECEFRotationInspector), LabelType.Adaptive)]
        public ObservablePrimitive<Quaternion> rotation { get; private set; }

        void IKeyedObservableNode<Guid>.AssignKey(Guid key)
            => id = key;
    }

    public class UserSettings : ObservableObject
    {
        public ObservablePrimitive<bool> loaded { get; private set; }
        public ObservablePrimitive<double2?> lastLocation { get; private set; }
        public ObservablePrimitive<bool> restoreLocationAutomatically { get; private set; }
        public ObservableList<LocationHistoryData> locationHistory { get; private set; }
        public ObservablePrimitive<float> nodeFetchRadius { get; private set; }
    }

    public class LocationHistoryData : ObservableObject
    {
        public ObservablePrimitive<string> name { get; private set; }
        public ObservablePrimitive<double2> location { get; private set; }
    }
}
