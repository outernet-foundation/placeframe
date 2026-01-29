using System;
using System.Collections.Generic;

namespace Outernet.Client
{
    public class ViewBinding
    {
        public static ViewBinding Default => new ViewBinding();
        public static ViewBinding Released => new ViewBinding() { released = true };

        public string name { get; set; }
        public bool released { get; private set; }

        public event Action onRelease
        {
            add => _orderedHandlers.Add(value);
            remove => _orderedHandlers.Remove(value);
        }

        private List<Action> _orderedHandlers = new List<Action>();

        public ViewBinding(string name, params Action[] onRelease)
        {
            this.name = name;

            if (onRelease != null)
                _orderedHandlers.AddRange(onRelease);
        }

        public ViewBinding(params Action[] onRelease)
            : this(null, onRelease) { }

        public ViewBinding(string name)
            : this(name, null) { }

        public ViewBinding() { }

        public void Release()
        {
            if (released)
                return;

            released = true;

            foreach (var onRelease in _orderedHandlers)
                onRelease.Invoke();
        }

        public static ViewBinding FromBindings(params ViewBinding[] bindings)
        {
            ViewBinding result = new ViewBinding();
            foreach (var binding in bindings)
                result.onRelease += binding.Release;

            return result;
        }
    }
}