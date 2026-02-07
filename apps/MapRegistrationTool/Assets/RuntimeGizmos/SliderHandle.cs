using FofX.Stateful;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Placeframe.MapRegistrationTool
{
    public class SliderHandle : RuntimeHandle<SliderHandle.Props>, IBeginDragHandler, IDragHandler
    {
        public class Props : RuntimeHandleProps
        {
            public ObservablePrimitive<Vector3> direction { get; private set; }
            public ObservablePrimitive<float> length { get; private set; }

            public Props() : base() { }

            public Props(Vector3 direction = default, float length = 1f, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default)
                : base(position, rotation, scale, color)
            {
                this.direction = new ObservablePrimitive<Vector3>(direction);
                this.length = new ObservablePrimitive<float>(length);
            }
        }

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(Vector3 direction = default, float length = 1f, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default)
            => InitializeAndBind(new Props(direction, length, position, rotation, scale, color));

        protected override void Draw(Color color)
        {
            var prevMatrix = RuntimeGizmos.matrix;
            RuntimeGizmos.matrix = transform.localToWorldMatrix;

            RuntimeGizmos.DrawArrow(
                Vector3.zero,
                props.direction.value.normalized * props.length.value,
                color,
                0.015f,
                false
            );

            RuntimeGizmos.matrix = prevMatrix;
        }

        protected override bool TryGetInputDistanceInteral(Ray inputRay, out float distance)
        {
            return RuntimeHandles.RaycastCylinder(
                inputRay,
                props.position.value,
                props.rotation.value * props.direction.value,
                props.length.value * props.scale.value,
                props.scale.value * 0.1f,
                out distance
            );
        }

        public void OnBeginDrag(PointerEventData eventData)
        {
            UndoRedoManager.RegisterUndo("Translate");
        }

        public void OnDrag(PointerEventData eventData)
        {
            var worldPosition = props.position.value;
            var worldNormal = props.rotation.value * props.direction.value;

            var screenPosition = eventData.pressEventCamera.WorldToScreenPoint(worldPosition);
            var screenNormal = eventData.pressEventCamera.WorldToScreenPoint(worldPosition + worldNormal) - screenPosition;

            if (screenNormal.x == 0 && screenNormal.y == 0)
                return;

            var screenNormalZ = screenNormal.z;
            screenNormal.z = 0;

            var screenProjectedDelta = Vector3.Project(eventData.delta, screenNormal.normalized);
            screenProjectedDelta.z = (screenNormal.x != 0 ?
                screenProjectedDelta.x / screenNormal.x :
                screenProjectedDelta.y / screenNormal.y) * screenNormalZ;

            var worldProjectedDelta = eventData.pressEventCamera.ScreenToWorldPoint(screenPosition + screenProjectedDelta) - worldPosition;
            var dragDistance = Vector3.Dot(worldNormal, worldProjectedDelta.normalized) > 0 ?
                worldProjectedDelta.magnitude : -worldProjectedDelta.magnitude;

            props.position.ExecuteSet(
                props.position.value +
                (props.rotation.value * props.direction.value.normalized * dragDistance),
                logLevel: FofX.LogLevel.None
            );
        }
    }
}