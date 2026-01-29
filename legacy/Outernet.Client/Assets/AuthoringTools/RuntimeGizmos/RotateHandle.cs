using FofX.Stateful;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.Client.AuthoringTools
{
    public class RotateHandle : RuntimeHandle<RotateHandle.Props>, IBeginDragHandler, IDragHandler
    {
        public class Props : RuntimeHandleProps
        {
            public ObservablePrimitive<float> radius { get; private set; }
            public ObservablePrimitive<Vector3> normal { get; private set; }

            public Props() : base() { }

            public Props(float radius = 1f, Vector3? normal = default, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default)
                : base(position, rotation, scale, color)
            {
                this.radius = new ObservablePrimitive<float>(radius);
                this.normal = new ObservablePrimitive<Vector3>(normal ?? Vector3.up);
            }
        }

        private Vector3 _rotatedNormal => props.rotation.value * props.normal.value;
        private Vector3 _relativeGrabPoint;
        private Vector3 _headOnScreenRight;

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(float radius = 1f, Vector3? normal = default, Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default)
            => InitializeAndBind(new Props(radius, normal, position, rotation, scale, color));

        private bool ViewIsHeadOn()
        {
            var toCamera = Camera.main.transform.position - props.position.value;
            var angle = Vector3.Angle(_rotatedNormal, toCamera);

            return angle > 170f || angle < 10f;
        }

        protected override void Draw(Color color)
        {
            if (props.isPressed.value)
            {
                RuntimeGizmos.DrawRay(
                    props.position.value,
                    transform.TransformDirection(_relativeGrabPoint).normalized * props.scale.value * props.radius.value,
                    props.scale.value * 0.025f,
                    color,
                    false
                );
            }

            if (ViewIsHeadOn() || props.isPressed.value)
            {
                RuntimeGizmos.DrawCircle(
                    props.position.value,
                    _rotatedNormal,
                    props.scale.value * props.radius.value,
                    color,
                    false
                );

                return;
            }

            RuntimeGizmos.DrawHalfTorus(
                props.position.value,
                Vector3.ProjectOnPlane(Camera.main.transform.position - props.position.value, _rotatedNormal),
                _rotatedNormal,
                props.scale.value * props.radius.value,
                color,
                false
            );
        }

        protected override bool TryGetInputDistanceInteral(Ray inputRay, out float distance)
        {
            if (!RuntimeHandles.RaycastCircle(
                inputRay,
                props.position.value,
                _rotatedNormal,
                props.scale.value * props.radius.value,
                props.scale.value * 0.2f,
                out distance
            ))
            {
                return false;
            }

            return ViewIsHeadOn() || Vector3.Dot(
                (inputRay.GetPoint(distance) - props.position.value).normalized,
                inputRay.direction.normalized
            ) < 0;
        }

        public override void OnPointerDown(PointerEventData eventData)
        {
            base.OnPointerDown(eventData);

            var ray = eventData.pressEventCamera.ScreenPointToRay(new Vector3(
                eventData.position.x,
                eventData.position.y,
                eventData.pressEventCamera.nearClipPlane
            ));

            TryGetInputDistanceInteral(ray, out var dist);
            var direction = Vector3.ProjectOnPlane(ray.GetPoint(dist) - props.position.value, _rotatedNormal);
            _headOnScreenRight = Vector3.Cross(direction, _rotatedNormal);
            _relativeGrabPoint = transform.InverseTransformDirection(direction);
        }

        public void OnBeginDrag(PointerEventData eventData)
        {
            UndoRedoManager.RegisterUndo("Rotate");
        }

        public void OnDrag(PointerEventData eventData)
        {
            var right = ViewIsHeadOn() ?
                _headOnScreenRight :
                Vector3.Cross(_rotatedNormal, props.position.value - eventData.pressEventCamera.transform.position);

            var screenspaceCenter = eventData.pressEventCamera.WorldToScreenPoint(props.position.value);
            var screenspaceRight = eventData.pressEventCamera.WorldToScreenPoint(props.position.value + right) - screenspaceCenter;

            screenspaceRight.z = 0;

            var delta = Vector3.Project(eventData.delta, screenspaceRight);
            delta.x /= Screen.width;
            delta.y /= Screen.height;

            float direction = Vector3.Dot(screenspaceRight.normalized, delta.normalized) > 0 ? -1 : 1;
            var degrees = delta.magnitude * direction * 180f;

            props.rotation.ExecuteSet(
                Quaternion.AngleAxis(degrees, _rotatedNormal) *
                props.rotation.value,
                logLevel: FofX.LogLevel.None
            );
        }
    }
}