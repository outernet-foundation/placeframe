using System;
using System.Linq;
using FofX.Stateful;
using Outernet.Client.Location;
using Placeframe.Core;
using UnityEngine;

namespace Outernet.Client.AuthoringTools
{
    public class ECEFRotationInspector : CustomObservableNodeInspector
    {
        protected override IDisposable BindTarget(IObservableNode target)
        {
            var ecefRotation = (ObservablePrimitive<Quaternion>)target;
            var localInput = UIBuilder.QuaternionControl(
                interactable: props.interactable.value,
                attributes: props.attributes.ToArray()
            );
            localInput.transform.SetParent(rect, false);

            bool pushingChanges = false;

            localInput.onValueChanged += () =>
            {
                if (pushingChanges)
                    return;

                UndoRedoManager.RegisterUndo("Set Rotation");
                ecefRotation.ExecuteSet(VisualPositioningSystem.UnityWorldToEcef(default, localInput.value).rotation);
            };

            return Bindings.Compose(
                localInput,
                ecefRotation.OnChange(x =>
                {
                    pushingChanges = true;
                    localInput.value = VisualPositioningSystem.EcefToUnityWorld(default, x).rotation;
                    pushingChanges = false;
                })
            );
        }
    }
}
