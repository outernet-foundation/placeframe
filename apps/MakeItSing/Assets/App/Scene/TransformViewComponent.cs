using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    [RequireComponent(typeof(TransformControl))]
    public class TransformViewComponent : MonoBehaviour, ISceneObjectViewComponent
    {
        private TransformControl _transformControl;

        private void Awake()
        {
            _transformControl = GetComponent<TransformControl>();
        }

        public void Setup(SceneObjectId objectId)
        {
            var objectState = App.state.scene.objects[objectId];
            var transformState = App.state.scene.transforms[objectId];

            _transformControl.Setup(new()
            {
                transform =
                {
                    localPosition = transformState.localPosition.ObservableNetworkSmooth(objectState.isMine.ObservableSelect(x => x ? -1 : 0.6f)),
                    localRotation = transformState.localRotation.ObservableNetworkSmooth(objectState.isMine.ObservableSelect(x => x ? -1 : 160f)),
                    localScale = transformState.localScale.ObservableNetworkSmooth(objectState.isMine.ObservableSelect(x => x ? -1 : 0.6f)),
                    onLocalPositionChanged = x => transformState.localPosition.value = x,
                    onLocalRotationChanged = x => transformState.localRotation.value = x,
                    onLocalScaleChanged = x => transformState.localScale.value = x
                }
            });
        }

        public void Teardown()
        {
            _transformControl.Dispose();
        }

        public void WriteInitialState(SceneState state, SceneObjectId id)
        {
            var transformState = state.transforms.GetOrAdd(id);
            transformState.localPosition.value = transform.localPosition;
            transformState.localRotation.value = transform.localRotation;
            transformState.localScale.value = transform.localScale;
        }
    }
}