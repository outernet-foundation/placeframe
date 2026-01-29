using System;
using System.Collections.Generic;
using System.Linq;
using FofX.Serialization;
using SimpleJSON;
using System.Collections;
using System.Collections.ObjectModel;

namespace FofX.Stateful
{
    public interface IObservablePrimitiveArray : IObservablePrimitive, IEnumerable
    {
        int count { get; }
        object this[int index] { get; }
    }

    public class ObservablePrimitiveArray<T> : ObservableNode, IObservablePrimitiveArray, IEnumerable<T>, IReadOnlyCollection<T>
    {
        Type IObservablePrimitive.primitiveType => typeof(T);

        public T this[int index] => _values[index];
        public int count => _values.Count;

        public override bool isDefault => _values.Count == 0;

        object IObservablePrimitiveArray.this[int index] => this[index];

        private List<T> _values = new List<T>();

        public IEnumerator<T> GetEnumerator() => _values.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();

        int IReadOnlyCollection<T>.Count => count;

        public ObservablePrimitiveArray() : base() { }

        public ObservablePrimitiveArray(params T[] values)
            : this((IEnumerable<T>)values) { }

        public ObservablePrimitiveArray(IEnumerable<T> values) : base()
        {
            _values.AddRange(values);
        }

        public void SetValue(IEnumerable<T> values)
        {
            var prevValue = _values.ToArray();
            _values.Clear();

            if (values != null)
                _values.AddRange(values);

            context.RegisterNodeChange(this, ChangeType.Set, currentValue: _values.AsReadOnly(), previousValue: prevValue);
        }

        object IObservablePrimitive.GetValue()
        {
            return _values.AsReadOnly();
        }

        void IObservablePrimitive.SetValue(object value)
        {
            if (value == null)
            {
                SetValue(null);
                return;
            }

            SetValue((IReadOnlyCollection<T>)value);
        }

        public override void ApplyChange(NodeChangeData change)
        {
            if (change.changeType == ChangeType.Dispose)
                return;

            if (change.changeType == ChangeType.Set)
            {
                SetValue((IReadOnlyCollection<T>)change.currentValue);
            }
            else
            {
                throw new Exception($"{nameof(ObservablePrimitive<T>)} does not support change type {change.changeType}");
            }
        }

        public override void CopyTo(IObservableNode copyTo)
        {
            ((ObservablePrimitiveArray<T>)copyTo).SetValue(_values);
        }

        public override void Reset()
        {
            SetValue(null);
        }

        public override JSONNode ToJSON(Func<IObservableNode, bool> filter)
        {
            JSONArray json = new JSONArray();
            var serializer = JSONSerialization.GetSerializer<T>();

            foreach (var item in _values)
                json.Add(serializer.toJSON(item));

            return json;
        }

        public override void FromJSON(JSONNode json)
        {
            var serializer = JSONSerialization.GetSerializer<T>();
            SetValue(((JSONArray)json).Linq.Select(x => serializer.fromJSON(x)).ToArray());
        }
    }
}
