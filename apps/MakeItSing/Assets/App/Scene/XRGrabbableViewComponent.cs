using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    [RequireComponent(typeof(XRGrabbableControl))]
    public class XRGrabbableViewComponent : MonoBehaviour, ISceneObjectViewComponent
    {
        private XRGrabbableControl _control;

        private void Awake()
        {
            _control = GetComponent<XRGrabbableControl>();
        }

        public void Setup(SceneObjectId objectId)
        {
            var objectState = App.state.scene.objects[objectId];
            _control.Setup(new()
            {
                allowGrab = Observables.ObservableCombineValues(objectState.isMine, objectState.allowOwnershipTransfer, (isMine, canTransfer) => isMine || canTransfer),
                onGrabbed = () => objectState.ownerID.value = App.state.playerID.value,
                onReleased = () =>
                {
                    if (objectState.ownerID.value == App.state.playerID.value)
                        objectState.ownerID.value = 0;
                }
            });
        }

        public void Teardown()
        {
            _control.Dispose();
        }

        public void WriteInitialState(SceneState state, SceneObjectId id) { }
    }
}