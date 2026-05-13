using System;
using FofX.Stateful;
using ObserveThing;
using Placeframe.Core;
using UnityEngine;

using static Nessle.Props;

namespace Plerion.MakeItSing
{
    [RequireComponent(typeof(TransformControl))]
    public class SceneOrigin : MonoBehaviour
    {
        private TransformControl _control;
        private IDisposable _subscriptions;

        private ObservableValue<Vector3> _originPosition;
        private ObservableValue<Quaternion> _originRotation;

        private void Awake()
        {
            _originPosition = new ObservableValue<Vector3>();
            _originRotation = new ObservableValue<Quaternion>();

            _subscriptions = StateObservables.SubscribeOperations(
                _ => UpdateOriginPose(),
                App.state.sceneOriginEcefPosition,
                App.state.sceneOriginEcefRotation
            );

            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += UpdateOriginPose;

            _control = GetComponent<TransformControl>();
            _control.destroyOnDispose = false;
            _control.Setup(new()
            {
                transform =
                {
                    localPosition = _originPosition.ObservableInterpolate(Value(5f)),
                    localRotation = _originRotation.ObservableInterpolate(Value(5f))
                }
            });
        }

        private void OnDestroy()
        {
            _control.Dispose();
            _subscriptions.Dispose();
        }

        private void UpdateOriginPose()
        {
            Settings.DefaultObservationContext.ExecuteBatchOperation(() =>
            {
                var pose = VisualPositioningSystem.EcefToUnityWorld(
                    App.state.sceneOriginEcefPosition.value,
                    App.state.sceneOriginEcefRotation.value
                );
                _originPosition.value = pose.position;
                _originRotation.value = pose.rotation;
            });
        }
    }
}