using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    [RequireComponent(typeof(XRGrabbableControl))]
    public class XRGrabbableViewComponent : MonoBehaviour, ISceneObjectViewComponent
    {
        private XRGrabbableControl _control;

        private SceneObjectState _objectState;
        private SceneTransformState _transformState;

        private void Awake()
        {
            _control = GetComponent<XRGrabbableControl>();
        }

        public void Setup(SceneObjectId objectId)
        {
            _objectState = App.state.scene.objects[objectId];
            App.state.scene.transforms.TryGetValue(objectId, out _transformState);

            _control.Setup(new()
            {
                allowGrab = Observables.ObservableCombineValues(_objectState.isMine, _objectState.allowOwnershipTransfer, (isMine, canTransfer) => isMine || canTransfer),
                onGrabbed = () =>
                {
                    App.ExecuteTransaction(state =>
                    {
                        _objectState.ownerID.value = state.playerID.value;

                        if (!state.scene.highFrequencyPrimitives.ContainsKey(_transformState.localPosition.nodePath))
                        {
                            new AddHighFrequencyPrimitive(
                                _transformState.localPosition,
                                PlayerIdHelpers.HighFrequencyPathIdHelper.AllocateID(),
                                state.playerID.value,
                                8
                            ).ExecuteTransaction(state);
                        }

                        if (!state.scene.highFrequencyPrimitives.ContainsKey(_transformState.localRotation.nodePath))
                        {
                            new AddHighFrequencyPrimitive(
                                _transformState.localRotation,
                                PlayerIdHelpers.HighFrequencyPathIdHelper.AllocateID(),
                                state.playerID.value,
                                8
                            ).ExecuteTransaction(state);
                        }

                        if (!state.scene.highFrequencyPrimitives.ContainsKey(_transformState.localScale.nodePath))
                        {
                            new AddHighFrequencyPrimitive(
                                _transformState.localScale,
                                PlayerIdHelpers.HighFrequencyPathIdHelper.AllocateID(),
                                state.playerID.value,
                                8
                            ).ExecuteTransaction(state);
                        }
                    });
                },
                onReleased = () =>
                {
                    if (_objectState.ownerID.value != App.state.playerID.value)
                        return;

                    App.ExecuteTransaction(state =>
                    {
                        _objectState.ownerID.value = 0;

                        if (_transformState == null)
                            return;

                        new RemoveHighFrequencyPrimitive(_transformState.localPosition).ExecuteTransaction(state);
                        new RemoveHighFrequencyPrimitive(_transformState.localRotation).ExecuteTransaction(state);
                        new RemoveHighFrequencyPrimitive(_transformState.localScale).ExecuteTransaction(state);
                    });
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