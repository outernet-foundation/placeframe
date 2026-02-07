using FofX.Stateful;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Placeframe.MapRegistrationTool
{
    public class PlaneHandle : RuntimeHandle<PlaneHandle.Props>, IBeginDragHandler, IDragHandler
    {
        public class Props : RuntimeHandleProps
        {
            public ObservablePrimitive<Rect> rect { get; private set; }

            public Props() : base() { }

            public Props(Rect rect = default, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default)
                : base(position, rotation, scale, color)
            {
                this.rect = new ObservablePrimitive<Rect>(rect);
            }
        }

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(Rect rect = default, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default)
            => InitializeAndBind(new Props(rect, position, rotation, scale, color));

        protected override void Draw(Color color)
        {
            var prevMatrix = RuntimeGizmos.matrix;
            RuntimeGizmos.matrix = transform.localToWorldMatrix;

            RuntimeGizmos.DrawRay(props.rect.value.min, Vector3.right * props.rect.value.width, 0.015f, color, false);
            RuntimeGizmos.DrawRay(props.rect.value.min, Vector3.up * props.rect.value.height, 0.015f, color, false);
            RuntimeGizmos.DrawRay(props.rect.value.max, -Vector3.right * props.rect.value.width, 0.015f, color, false);
            RuntimeGizmos.DrawRay(props.rect.value.max, -Vector3.up * props.rect.value.height, 0.015f, color, false);

            RuntimeGizmos.DrawPlane(
                props.rect.value.center,
                Vector3.right,
                Vector3.up,
                props.rect.value.size,
                color.SetAlpha(color.a * 0.5f),
                false
            );

            RuntimeGizmos.matrix = prevMatrix;
        }

        protected override bool TryGetInputDistanceInteral(Ray inputRay, out float distance)
        {
            var plane = new Plane(
                props.position.value,
                props.position.value + (props.rotation.value * Vector3.right),
                props.position.value + (props.rotation.value * Vector3.up)
            );

            if (!plane.Raycast(inputRay, out distance))
                return false;

            return props.rect.value.Contains(transform.InverseTransformPoint(inputRay.GetPoint(distance)));
        }

        public void OnBeginDrag(PointerEventData eventData)
        {
            UndoRedoManager.RegisterUndo("Translate");
        }

        public void OnDrag(PointerEventData eventData)
        {
            var plane = new Plane(
                props.position.value,
                props.position.value + (props.rotation.value * Vector3.right),
                props.position.value + (props.rotation.value * Vector3.up)
            );

            var prevRay = eventData.pressEventCamera.ScreenPointToRay(new Vector3(
                eventData.position.x - eventData.delta.x,
                eventData.position.y - eventData.delta.y,
                eventData.pressEventCamera.nearClipPlane
            ));

            var currentRay = eventData.pressEventCamera.ScreenPointToRay(new Vector3(
                eventData.position.x,
                eventData.position.y,
                eventData.pressEventCamera.nearClipPlane
            ));

            if (!plane.RaycastPoint(prevRay, out var prevPoint) ||
                !plane.RaycastPoint(currentRay, out var point))
            {
                return;
            }

            // Use matrix because we don't want to account for scale here
            var matrix = Matrix4x4.TRS(props.position.value, props.rotation.value, Vector3.one);
            point = matrix.inverse.MultiplyPoint(point);
            prevPoint = matrix.inverse.MultiplyPoint(prevPoint);

            var delta = point - prevPoint;
            props.position.ExecuteSet(
                props.position.value +
                (props.rotation.value * Vector3.right * delta.x) +
                (props.rotation.value * Vector3.up * delta.y),
                logLevel: FofX.LogLevel.None
            );
        }
    }
}