using System;
using System.Collections.Generic;
using UnityEngine;
using FofX.Stateful;

namespace Placeframe.MapRegistrationTool
{
    public abstract class ViewBase : MonoBehaviour, IDisposable
    {
        private List<IDisposable> _bindings = new List<IDisposable>();

        public void AddBinding(IDisposable binding)
        {
            _bindings.Add(binding);
        }

        public void RemoveBinding(IDisposable binding)
        {
            _bindings.Remove(binding);
        }

        public void AddBinding(params IDisposable[] bindings)
        {
            _bindings.AddRange(bindings);
        }

        public void RemoveBinding(params IDisposable[] bindings)
        {
            foreach (var binding in bindings)
                _bindings.Remove(binding);
        }

        public virtual void Dispose()
        {
            foreach (var binding in _bindings)
                binding.Dispose();

            _bindings.Clear();
        }

        protected virtual void OnDestroy()
        {
            Dispose();
        }
    }

    public abstract class Control : ViewBase
    {
        public abstract IObservableNode propsAsNode { get; }
        public abstract bool isSetup { get; }

        public abstract void Setup();
    }

    public abstract class Control<T> : Control where T : class, IObservableNode, new()
    {
        public T props { get; protected set; }
        public override IObservableNode propsAsNode => props;
        public override bool isSetup => _isSetup;

        private bool _isSetup;

        public override void Setup()
            => InitializeAndBind(new T());

        protected void InitializeAndBind(T props)
        {
            if (isSetup)
                throw new Exception($"{this} has already been setup!");

            props.Initialize("props", App.state.context);
            this.props = props;

            AddBinding(Bindings.OnRelease(() => props.context.ExecuteActionOrDelay(props, FofX.LogLevel.Trace, new DisposeViewPropsAction())));
            Bind();

            _isSetup = true;
        }

        public override void Dispose()
        {
            _isSetup = false;
            base.Dispose();
        }

        protected abstract void Bind();

        private class DisposeViewPropsAction : ObservableNodeAction<T>
        {
            public override void Execute(T target)
            {
                target.Dispose();
            }
        }
    }
}