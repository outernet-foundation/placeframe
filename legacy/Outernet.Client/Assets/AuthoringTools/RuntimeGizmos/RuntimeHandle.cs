using FofX.Stateful;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.Client.AuthoringTools
{
    public class RuntimeHandleProps : ObservableObject
    {
        public ObservablePrimitive<Vector3> position { get; private set; }
        public ObservablePrimitive<Quaternion> rotation { get; private set; }
        public ObservablePrimitive<float> scale { get; private set; }
        public ObservablePrimitive<Color> color { get; private set; }

        public ObservablePrimitive<bool> disabled { get; private set; }
        public ObservablePrimitive<bool> isPressed { get; private set; }
        public ObservablePrimitive<bool> isHovered { get; private set; }

        public RuntimeHandleProps() : base() { }

        public RuntimeHandleProps(Vector3 position = default, Quaternion? rotation = default, float scale = 1f, Color? color = default)
        {
            this.position = new ObservablePrimitive<Vector3>(position);
            this.rotation = new ObservablePrimitive<Quaternion>(rotation ?? Quaternion.identity);
            this.scale = new ObservablePrimitive<float>(scale);
            this.color = new ObservablePrimitive<Color>(color ?? Color.white);
        }
    }

    public interface IRuntimeHandle
    {
        public RuntimeHandleProps props { get; }
        public bool TryGetInputDistance(Ray inputRay, out float distance);
        public GameObject gameObject { get; }
    }

    public abstract class RuntimeHandle<T> : Control<T>,
        IRuntimeHandle,
        IPointerEnterHandler,
        IPointerExitHandler,
        IPointerDownHandler,
        IPointerUpHandler
        where T : RuntimeHandleProps, new()
    {
        RuntimeHandleProps IRuntimeHandle.props => props;

        private Camera _camera;

        private void Awake()
        {
            _camera = Camera.main;
        }

        private void LateUpdate()
        {
            float newScale = CalcSize(props.position.value);
            if (newScale != props.scale.value)
                props.scale.ExecuteSet(newScale, logLevel: FofX.LogLevel.None);

            if (props.disabled.value)
            {
                Draw(props.color.value.WithAlpha(0.333f));
            }
            else if (props.isPressed.value)
            {
                Draw(Color.yellow);
            }
            else if (props.isHovered.value)
            {
                Draw(Color.cyan);
            }
            else
            {
                Draw(props.color.value);
            }
        }

        protected override void Bind()
        {
            RuntimeHandlesRaycaster.RegisterHandle(this);

            AddBinding(
                props.position.OnChange(x => transform.position = x),
                props.rotation.OnChange(x => transform.rotation = x),
                props.scale.OnChange(x => transform.localScale = Vector3.one * x),
                Bindings.OnRelease(() => RuntimeHandlesRaycaster.DeregisterHandle(this))
            );
        }

        private float CalcSize(Vector3 position)
        {
            Transform camTransform = _camera.transform;
            float z = Vector3.Dot(position - camTransform.position, camTransform.TransformDirection(new Vector3(0f, 0f, 1f)));
            Vector3 vector = _camera.WorldToScreenPoint(camTransform.position + camTransform.TransformDirection(new Vector3(0f, 0f, z)));
            Vector3 vector2 = _camera.WorldToScreenPoint(camTransform.position + camTransform.TransformDirection(new Vector3(1f, 0f, z)));
            float magnitude = (vector - vector2).magnitude;
            return 80f / Mathf.Max(magnitude, 0.0001f);
        }

        protected abstract void Draw(Color color);

        public bool TryGetInputDistance(Ray inputRay, out float distance)
        {
            if (props.disabled.value)
            {
                distance = 0;
                return false;
            }

            return TryGetInputDistanceInteral(inputRay, out distance);
        }

        protected abstract bool TryGetInputDistanceInteral(Ray inputRay, out float distance);

        public virtual void OnPointerEnter(PointerEventData eventData)
        {
            if (props.disabled.value)
                return;

            props.isHovered.ExecuteSet(true, logLevel: FofX.LogLevel.None);
        }

        public virtual void OnPointerExit(PointerEventData eventData)
        {
            props.isHovered.ExecuteSet(false, logLevel: FofX.LogLevel.None);
        }

        public virtual void OnPointerDown(PointerEventData eventData)
        {
            if (props.disabled.value)
                return;

            props.isPressed.ExecuteSet(true, logLevel: FofX.LogLevel.None);
        }

        public virtual void OnPointerUp(PointerEventData eventData)
        {
            props.isPressed.ExecuteSet(false, logLevel: FofX.LogLevel.None);
        }
    }
}