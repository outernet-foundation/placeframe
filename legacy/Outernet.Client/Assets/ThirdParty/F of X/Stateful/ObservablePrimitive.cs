using System;
using System.Linq;
using FofX.Serialization;
using SimpleJSON;

namespace FofX.Stateful
{
    public interface IObservablePrimitive : IObservableNode
    {
        Type primitiveType { get; }
        object GetValue();
        void SetValue(object value);
    }

    public sealed class ObservablePrimitive<T> : ObservableNode, IObservablePrimitive
    {
        private T _value;
        public T value
        {
            get => _value;
            set
            {
                if (!object.Equals(_value, value))
                {
                    var prev = _value;
                    _value = value;
                    context.RegisterNodeChange(this, ChangeType.Set, currentValue: value, previousValue: prev);
                }
            }
        }

        Type IObservablePrimitive.primitiveType => typeof(T);
        public override bool isDefault => Equals(value, default(T));

        public ObservablePrimitive() { }

        public ObservablePrimitive(T value)
        {
            _value = value;
        }

        public override void ApplyChange(NodeChangeData change)
        {
            if (change.changeType == ChangeType.Dispose)
                return;

            if (change.changeType == ChangeType.Set)
            {
                value = (T)change.currentValue;
            }
            else
            {
                throw new Exception($"{nameof(ObservablePrimitive<T>)} does not support change type {change.changeType}");
            }
        }

        public override void CopyTo(IObservableNode copyTo)
        {
            if (copyTo is not ObservablePrimitive<T> copyToPrimitive)
                throw new Exception($"{copyTo.nodePath} is not a {nameof(ObservablePrimitive<T>)}");

            copyToPrimitive.value = value;
        }

        public override void Reset()
        {
            value = default;
        }

        object IObservablePrimitive.GetValue()
        {
            return value;
        }

        void IObservablePrimitive.SetValue(object value)
        {
            this.value = (T)value;
        }

        public override JSONNode ToJSON(Func<IObservableNode, bool> filter)
        {
            return JSONSerialization.ToJSON(value);
        }

        public override void FromJSON(JSONNode json)
        {
            if (json == null)
            {
                Reset();
                return;
            }

            value = JSONSerialization.FromJSON<T>(json);
        }
    }
}
