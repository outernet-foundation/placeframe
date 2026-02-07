using System;

using UnityEngine;

using TMPro;

namespace Placeframe.MapRegistrationTool
{
    public class ValueControl<T> : ValueControl
    {
        public T value
        {
            get => _value;
            set
            {
                if (Equals(value, _value))
                    return;

                _value = value;
                OnValueChangedInternal();
                RaiseOnValueChanged();
            }
        }

        public override object valueAsObject { get => value; set => this.value = (T)value; }

        private T _value;

        protected virtual void OnValueChangedInternal() { }
    }

    public abstract class ValueControl : ViewBase
    {
        public abstract object valueAsObject { get; set; }
        public event Action onValueChanged;

        public virtual void ApplyStyleAttributes(Attribute[] attributes) { }

        protected void RaiseOnValueChanged()
        {
            onValueChanged?.Invoke();
        }
    }
}