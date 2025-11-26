using UnityEngine;

using FofX.Stateful;

using System.Linq;
using System;

namespace Outernet.MapRegistrationTool
{
    public class ECEFRotationInspector : CustomObservableNodeInspector
    {
        protected override IDisposable BindTarget(IObservableNode target)
        {
            var ecefRotation = (ObservablePrimitive<Quaternion>)target;
            var localInput = UIBuilder.QuaternionControl(interactable: props.interactable.value, attributes: props.attributes.ToArray());
            localInput.transform.SetParent(rect, false);

            bool pushingChanges = false;

            localInput.onValueChanged += () =>
            {
                if (pushingChanges)
                    return;

                UndoRedoManager.RegisterUndo("Set Rotation");
                ecefRotation.ExecuteSet(LocationUtilities.UnityWorldToEcef(default, localInput.value).rotation);
            };

            return Bindings.Compose(
                localInput,
                ecefRotation.OnChange(x =>
                {
                    pushingChanges = true;
                    localInput.value = LocationUtilities.EcefToUnityWorld(default, x).rotation;
                    pushingChanges = false;
                })
            );
        }
    }
}