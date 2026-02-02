using Unity.Mathematics;

using FofX.Stateful;

using CesiumForUnity;
using System;
using Placeframe.Core;

namespace Outernet.Client.AuthoringTools
{
    public class ECEFPositionInspector : CustomObservableNodeInspector
    {
        protected override IDisposable BindTarget(IObservableNode target)
        {
            var ecefPosition = (ObservablePrimitive<double3>)target;
            var ecefInput = UIBuilder.Double3Control("ECEF", LabelType.Adaptive, props.interactable.value);
            var gpsInput = UIBuilder.Double3Control("GPS", LabelType.Adaptive, props.interactable.value);
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
                ecefPosition.ExecuteSet(CesiumWgs84Ellipsoid.LongitudeLatitudeHeightToEarthCenteredEarthFixed(gpsInput.value));
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
                    gpsInput.value = CesiumWgs84Ellipsoid.EarthCenteredEarthFixedToLongitudeLatitudeHeight(x);
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