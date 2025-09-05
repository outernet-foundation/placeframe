using System;
using System.Collections.Generic;
using ObserveThing;
using UnityEngine;

namespace Nessle
{
    public interface IControl : IDisposable
    {
        IControl parent { get; }
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
    }

    public interface IControl<out T> : IControl
    {
        public T props { get; }
    }

    public class Control : IControl
    {
        public IControl parent { get; private set; }
        public GameObject gameObject { get; private set; }
        public RectTransform transform { get; private set; }
        public IValueObservable<Rect> rect => _rect;

        private ValueObservable<Rect> _rect = new ValueObservable<Rect>();
        private HashSet<IControl> _children = new HashSet<IControl>();
        private List<IDisposable> _bindings = new List<IDisposable>();

        public Control(string name = null, params Type[] components)
            : this(new GameObject(name, components)) { }

        public Control(GameObject gameObject)
        {
            this.gameObject = gameObject;
            transform = gameObject.GetOrAddComponent<RectTransform>();
            gameObject.GetOrAddComponent<RectTransformChangedHandler>().onReceivedEvent += x => _rect.value = x;
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

        public Control(T props, string name = null, params Type[] components)
            : this(props, new GameObject(name, components)) { }

        public Control(T props, GameObject gameObject)
            : base(gameObject)
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
