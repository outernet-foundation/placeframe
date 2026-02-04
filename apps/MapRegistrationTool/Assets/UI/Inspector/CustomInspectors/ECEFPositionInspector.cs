using Unity.Mathematics;

using FofX.Stateful;
using System;
using Placeframe.Core;

namespace Placeframe.MapRegistrationTool
{
    public class ECEFPositionInspector : CustomObservableNodeInspector
    {
        protected override IDisposable BindTarget(IObservableNode target)
        {
            var ecefPosition = (ObservablePrimitive<double3>)target;
            var ecefInput = UIBuilder.Double3Control("ECEF", LabelType.Adaptive, props.interactable.value);
            var gpsInput = UIBuilder.CartographicCoordinatesControl("GPS", LabelType.Adaptive, props.interactable.value);
            var localInput = UIBuilder.Vector3Control("Local", LabelType.Adaptive, props.interactable.value);

            ecefInput.transform.SetParent(rect, false);
            gpsInput.transform.SetParent(rect, false);
            localInput.transform.SetParent(rect, false);

            bool pushingChanges = false;

            ecefInput.onValueChanged += () =>
            {
                if (pushingChanges)
                    return;

                UndoRedoManager.RegisterUndo("Set Position");
                ecefPosition.ExecuteSet(ecefInput.value);
            };

            gpsInput.onValueChanged += () =>
            {
                if (pushingChanges)
                    return;

                UndoRedoManager.RegisterUndo("Set Position");
                ecefPosition.ExecuteSet(WGS84.CartographicToEcef(CartographicCoordinates.FromLatitudeLongitudeHeight(
                    gpsInput.value.Latitude, gpsInput.value.Longitude, gpsInput.value.Height)));
            };

            localInput.onValueChanged += () =>
            {
                if (pushingChanges)
                    return;

                UndoRedoManager.RegisterUndo("Set Position");
                ecefPosition.ExecuteSet(VisualPositioningSystem.UnityWorldToEcef(localInput.value, default).position);
            };

            return Bindings.Compose(
                ecefPosition.OnChange(x =>
                {
                    pushingChanges = true;
                    ecefInput.value = x;
                    gpsInput.value = WGS84.EcefToCartographic(x);
                    localInput.value = VisualPositioningSystem.EcefToUnityWorld(x, default).position;
                    pushingChanges = false;
                }),
                ecefInput,
                gpsInput,
                localInput
            );
        }
    }
}