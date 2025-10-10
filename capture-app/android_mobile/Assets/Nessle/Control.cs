using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using ObserveThing;
using Testing;
using Unity.VisualScripting;
using UnityEngine;

namespace Nessle
{
    public interface IControl : IDisposable
    {
        IControl parent { get; }
        Style style { get; }
        string identifier { get; }
        string identifierFull { get; }
        GameObject gameObject { get; }
        RectTransform transform { get; }

        IValueObservable<Rect> rect { get; }

        void AddBinding(IDisposable binding);
        void AddBinding(params IDisposable[] bindings);
        void RemoveBinding(IDisposable binding);
        void RemoveBinding(params IDisposable[] bindings);

        void SetParent(IControl control);
        void AddChild(IControl control);
        void RemoveChild(IControl control);
        void SetSiblingIndex(int index);

        void SetStyle(Style style);
        void HandleControlHierarchyChanged();

        void UseStyle<T>(StyleProperty<T> property, Action<T> onChanged);
    }

    public interface IControl<out T> : IControl
    {
        public T props { get; }
    }

    public class Control : IControl
    {
        private abstract class StyleUsage
        {
            public abstract void SetStyle(Style style);
            public abstract void SetState(string state);
        }

        private class StyleUsage<T> : StyleUsage
        {
            public StyleProperty<T> property { get; }
            public Action<T> handleStyleChanged { get; }

            private Style _style;
            private string _state;
            private T _value;
            private T _transitionStartValue;
            private T _transitionValue;
            private IDisposable _subscription;
            private bool _transitioning;
            private TaskHandle _transition = TaskHandle.Complete;
            private Func<T, T, float, T> _interpolate;
            private bool _canTransition => _interpolate != null;

            public StyleUsage(StyleProperty<T> property, Action<T> handleStyleChanged, Func<T, T, float, T> interpolate)
            {
                this.property = property;
                this.handleStyleChanged = handleStyleChanged;
                _interpolate = interpolate;
            }

            public override void SetStyle(Style style)
            {
                _style = style;
                _subscription?.Dispose();
                var source = style.TryGetPropertyValue(property, _state, out var value) ? value : property.defaultValue;
                _subscription = source.Subscribe(HandleStyleChanged);
            }

            public override void SetState(string state)
            {
                _state = state;
                _subscription?.Dispose();
                var source = _style.TryGetPropertyValue(property, state, out var value) ? value : property.defaultValue;

                if (!_canTransition)
                {
                    _subscription = source.Subscribe(HandleStyleChanged);
                    return;
                }

                _transitionStartValue = _transitioning ? _transitionValue : _value;
                _transitioning = true;
                _subscription = source.Subscribe(HandleStyleChanged);

                _transition.Cancel();
                _transition = TaskHandle.Execute(token => PerformTransition(
                    _style.TryGetPropertyValue(StyleProperties.Transition, state, out var transition) ?
                        transition.Peek() : StyleProperties.Transition.defaultValue.Peek(),
                    token
                ));
            }

            private async UniTask PerformTransition(AnimationCurve curve, CancellationToken token)
            {
                if (curve == null)
                {
                    _transitionValue = _value;
                    handleStyleChanged(_value);
                    _transitioning = false;
                    return;
                }

                float elapsedTime = 0;
                float duration = curve[curve.keys.Length - 1].time;

                while (!token.IsCancellationRequested && elapsedTime < duration)
                {
                    _transitionValue = _interpolate(_transitionStartValue, _value, curve.Evaluate(elapsedTime));
                    handleStyleChanged(_transitionValue);
                    await UniTask.WaitForEndOfFrame();
                    elapsedTime += Time.deltaTime;
                }
            }

            private void HandleStyleChanged(IValueEventArgs<T> args)
            {
                _value = args.currentValue;

                if (_transitioning)
                    return;

                handleStyleChanged(args.currentValue);
            }
        }

        public IControl parent { get; private set; }
        public Style style { get; private set; } = new Style();
        public Style styleSelf { get; private set; } = new Style();
        public ValueObservable<string> styleState { get; private set; } = new ValueObservable<string>();
        public string identifier { get; private set; }
        public string identifierFull { get; private set; }
        public GameObject gameObject { get; private set; }
        public RectTransform transform { get; private set; }
        public IValueObservable<Rect> rect => _rect;

        private ValueObservable<Rect> _rect = new ValueObservable<Rect>();
        private HashSet<IControl> _children = new HashSet<IControl>();
        private List<IDisposable> _bindings = new List<IDisposable>();
        private HashSet<StyleUsage> _styleUsages = new HashSet<StyleUsage>();

        public Control(string identifier, params Type[] components)
            : this(identifier, new GameObject(identifier, components)) { }

        public Control(string identifier, GameObject gameObject)
        {
            this.identifier = identifierFull = identifier;
            this.gameObject = gameObject;

            gameObject.name = identifier;

            transform = gameObject.GetOrAddComponent<RectTransform>();
            gameObject.GetOrAddComponent<RectTransformChangedHandler>().onReceivedEvent += x => _rect.value = x;
        }

        private Func<T, T, float, T> GetInterplationMethod<T>()
        {
            if (typeof(T) == typeof(float))
            {
                Func<float, float, float, float> del = Mathf.Lerp;
                return (Func<T, T, float, T>)(object)del;
            }
            else if (typeof(T) == typeof(Vector2))
            {
                Func<Vector2, Vector2, float, Vector2> del = Vector2.Lerp;
                return (Func<T, T, float, T>)(object)del;
            }
            else if (typeof(T) == typeof(Vector3))
            {
                Func<Vector3, Vector3, float, Vector3> del = Vector3.Lerp;
                return (Func<T, T, float, T>)(object)del;
            }
            else if (typeof(T) == typeof(Vector4))
            {
                Func<Vector4, Vector4, float, Vector4> del = Vector4.Lerp;
                return (Func<T, T, float, T>)(object)del;
            }
            else if (typeof(T) == typeof(Quaternion))
            {
                Func<Quaternion, Quaternion, float, Quaternion> del = Quaternion.Lerp;
                return (Func<T, T, float, T>)(object)del;
            }
            else if (typeof(T) == typeof(Color))
            {
                Func<Color, Color, float, Color> del = Color.Lerp;
                return (Func<T, T, float, T>)(object)del;
            }

            return null;
        }

        public void AddBinding(IDisposable binding)
        {
            _bindings.Add(binding);
        }

        public void AddBinding(params IDisposable[] bindings)
        {
            _bindings.AddRange(bindings);
        }

        public void RemoveBinding(IDisposable binding)
        {
            _bindings.Remove(binding);
        }

        public void RemoveBinding(params IDisposable[] bindings)
        {
            foreach (var binding in bindings)
                _bindings.Remove(binding);
        }

        public void SetSiblingIndex(int index)
        {
            transform.SetSiblingIndex(index);
        }

        public void SetParent(IControl parent)
        {
            var prevParent = this.parent;
            this.parent = parent;

            if (prevParent != null)
                prevParent.RemoveChild(this);

            if (parent != null)
                parent.AddChild(this);

            HandleControlHierarchyChanged();
        }

        public void SetStyle(Style style)
        {
            styleSelf = style ?? new Style();
            HandleControlHierarchyChanged();
        }

        public void HandleControlHierarchyChanged()
        {
            identifierFull = parent == null ? identifier : $"{parent.identifierFull}.{identifier}";
            style = parent == null ? styleSelf : parent.style.AppendStyle(styleSelf);

            foreach (var usage in _styleUsages)
                usage.SetStyle(style);

            foreach (var child in _children)
                child.HandleControlHierarchyChanged();
        }

        public void UseStyle<T>(StyleProperty<T> styleProperty, Action<T> apply)
        {
            var usage = new StyleUsage<T>(styleProperty, apply, GetInterplationMethod<T>());
            usage.SetStyle(style);
            _styleUsages.Add(usage);
        }

        public void AddChild(IControl child)
        {
            if (child.parent != this)
            {
                child.SetParent(this);
                return;
            }

            _children.Add(child);
            child.transform.SetParent(transform, false);
        }

        public void RemoveChild(IControl child)
        {
            if (child.parent == this)
            {
                child.SetParent(null);
                return;
            }

            _children.Remove(child);
            child.transform.SetParent(null, false);
        }

        public virtual void Dispose()
        {
            _rect.Dispose();

            foreach (var child in _children)
                child.Dispose();

            foreach (var binding in _bindings)
                binding.Dispose();

            UnityEngine.Object.Destroy(gameObject);
        }
    }

    public class Control<T> : Control, IControl<T>
    {
        public T props { get; }

        public Control(string identifier, T props, params Type[] components)
            : this(identifier, props, new GameObject(identifier, components)) { }

        public Control(string identifier, T props, GameObject gameObject)
            : base(identifier, gameObject)
        {
            this.props = props;
        }

        public override void Dispose()
        {
            base.Dispose();

            if (props is IDisposable propsDisposable)
                propsDisposable.Dispose();
        }
    }
}
