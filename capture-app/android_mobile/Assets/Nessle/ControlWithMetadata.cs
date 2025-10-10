using System;
using ObserveThing;
using UnityEngine;

namespace Nessle
{
    public interface IControlWithMetadata<TProps, TData> : IControl<TProps>
    {
        IControl<TProps> control { get; }
        TData metadata { get; }
    }

    public class UnityControlWithMetadata<TProps, TData> : IControlWithMetadata<TProps, TData>, IControl
    {
        public IControl<TProps> control { get; }
        public TData metadata { get; }
        public IControl parent => control.parent;
        public string identifier => control.identifier;
        public string identifierFull => control.identifierFull;
        public TProps props => control.props;

        public RectTransform transform => _control.transform;
        public GameObject gameObject => _control.gameObject;
        public IValueObservable<Rect> rect => _control.rect;

        private IControl _control;

        public UnityControlWithMetadata(IControl<TProps> control, TData metadata)
        {
            if (control is not IControl unityControl)
                throw new Exception($"{parent} is not a {nameof(IControl)}");

            this.control = control;
            this.metadata = metadata;

            _control = unityControl;
        }

        public void AddBinding(IDisposable binding)
            => control.AddBinding(binding);

        public void AddBinding(params IDisposable[] bindings)
            => control.AddBinding(bindings);

        public void RemoveBinding(IDisposable binding)
            => control.RemoveBinding(binding);

        public void RemoveBinding(params IDisposable[] bindings)
            => control.RemoveBinding(bindings);

        public void SetParent(IControl parent)
            => control.SetParent(parent);

        public void SetSiblingIndex(int index)
            => control.SetSiblingIndex(index);

        void IControl.AddChild(IControl child)
            => _control.AddChild(child);

        void IControl.RemoveChild(IControl child)
            => _control.RemoveChild(child);

        public void Dispose()
            => control.Dispose();

        public void HandleControlHierarchyChanged()
            => control.HandleControlHierarchyChanged();
    }
}
