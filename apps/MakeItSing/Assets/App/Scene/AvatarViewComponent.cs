using System;
using UnityEngine;
using ObserveThing;

namespace Plerion.MakeItSing
{
    [RequireComponent(typeof(TransformViewComponent))]
    public class AvatarViewComponent : MonoBehaviour, ISceneObjectViewComponent
    {
        private IDisposable _subcription;
        private Transform _camera;

        private void LateUpdate()
        {
            var forward = _camera.forward;
            forward.y = 0;
            forward = forward.normalized;

            transform.position = _camera.position;
            transform.rotation = Quaternion.LookRotation(forward, Vector3.up);
        }

        public void Setup(SceneObjectId objectId)
        {
            _camera = Camera.main.transform;
            _subcription = App.state.scene.objects[objectId].isMine.Subscribe(isMine => enabled = isMine);
        }

        public void Teardown()
        {
            _subcription.Dispose();
        }

        public void WriteInitialState(SceneState state, SceneObjectId id) { }
    }
}