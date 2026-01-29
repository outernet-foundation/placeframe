using System;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using SimpleJSON;
using FofX.Serialization;

namespace FofX.Stateful
{
    public interface IObservableSet : IObservableNode, IObservableCollection
    {
        Type itemType { get; }

        bool Add(object item);
        bool Remove(object item);
        void Clear();
    }

    public class ObservableSet<T> : ObservableNode, IObservableSet, IObservableCollection<T>
    {
        public int count => _hashSet.Count;
        public override bool isDefault => _hashSet.Count == 0;

        public IEnumerator<T> GetEnumerator() => _hashSet.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
        Type IObservableSet.itemType => typeof(T);

        private HashSet<T> _hashSet = new HashSet<T>();

        public ObservableSet() : base() { }

        public ObservableSet(params T[] values)
            : this((IEnumerable<T>)values) { }

        public ObservableSet(IEnumerable<T> values) : base()
        {
            foreach (var value in values)
                _hashSet.Add(value);
        }

        public bool Add(T item)
        {
            if (_hashSet.Add(item))
            {
                context.RegisterNodeChange(this, ChangeType.Add, collectionElement: item);
                return true;
            }

            return false;
        }

        public bool Remove(T item)
        {
            if (_hashSet.Remove(item))
            {
                context.RegisterNodeChange(this, ChangeType.Remove, collectionElement: item);
                return true;
            }

            return false;
        }

        public bool Contains(T item)
        {
            return _hashSet.Contains(item);
        }

        public void Clear()
        {
            foreach (T item in _hashSet.ToArray())
                Remove(item);
        }

        public override void ApplyChange(NodeChangeData change)
        {
            if (change.changeType == ChangeType.Dispose)
                return;

            if (change.changeType == ChangeType.Add)
            {
                Add((T)change.collectionElement);
            }
            else if (change.changeType == ChangeType.Remove)
            {
                Remove((T)change.collectionElement);
            }
            else
            {
                throw new Exception($"{nameof(ObservableSet<T>)} does not support change type {change.changeType}");
            }
        }

        public override void CopyTo(IObservableNode copyTo)
        {
            if (copyTo is not ObservableSet<T> copyToSet)
                throw new Exception($"{copyTo.nodePath} is not a {nameof(ObservableSet<T>)}");

            foreach (var toRemove in copyToSet.Except(_hashSet).ToArray())
                Remove(toRemove);

            foreach (var toAdd in _hashSet.Except(copyToSet).ToArray())
                Add(toAdd);
        }

        public override void Reset()
        {
            Clear();
        }

        bool IObservableSet.Add(object item)
        {
            return Add((T)item);
        }

        bool IObservableSet.Remove(object item)
        {
            return Remove((T)item);
        }

        public override JSONNode ToJSON(Func<IObservableNode, bool> filter)
        {
            JSONArray array = new JSONArray();
            SerializationPair<T> serializer = JSONSerialization.GetSerializer<T>();

            foreach (T value in _hashSet)
                array.Add(serializer.toJSON(value));

            return array;
        }

        public override void FromJSON(JSONNode json)
        {
            if (json == null)
            {
                Reset();
                return;
            }

            JSONArray array = (JSONArray)json;
            SerializationPair<T> serializer = JSONSerialization.GetSerializer<T>();

            Clear();

            foreach (var value in array.Values)
                Add(serializer.fromJSON(value));
        }

        bool IObservableCollection.Contains(object value)
            => Contains((T)value);
    }
}
