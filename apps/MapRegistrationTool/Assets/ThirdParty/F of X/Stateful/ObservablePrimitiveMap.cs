using System;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using SimpleJSON;

using FofX.Serialization;

namespace FofX.Stateful
{
    public interface IObservablePrimitiveMap : IObservableNode, IObservableCollection
    {
        Type leftType { get; }
        Type rightType { get; }

        object GetLeft(object right);
        object GetRight(object left);
        bool TryGetLeft(object right, out object left);
        bool TryGetRight(object left, out object right);
        bool Remove(object entry);
        bool Remove(object left, object right);
        bool RemoveLeft(object left);
        bool RemoveRight(object right);
        void Add(object entry);
        void Add(object left, object right);
        void Clear();
    }

    public interface IPrimitiveMapPair
    {
        object left { get; }
        object right { get; }
    }

    public struct PrimitiveMapPair<TLeft, TRight> : IPrimitiveMapPair
    {
        public TLeft left { get; private set; }
        public TRight right { get; private set; }

        object IPrimitiveMapPair.left => left;
        object IPrimitiveMapPair.right => right;

        public PrimitiveMapPair(TLeft left, TRight right)
        {
            this.left = left;
            this.right = right;
        }

        public override string ToString()
        {
            return $"({left}, {right})";
        }
    }

    public class ObservablePrimitiveMap<TLeft, TRight> : ObservableNode, IObservableCollection<PrimitiveMapPair<TLeft, TRight>>, IObservablePrimitiveMap
    {
        private Dictionary<TLeft, TRight> _leftToRight = new Dictionary<TLeft, TRight>();
        private Dictionary<TRight, TLeft> _rightToLeft = new Dictionary<TRight, TLeft>();

        public override bool isDefault => _leftToRight.Count == 0 && _rightToLeft.Count == 0;
        public int count => _leftToRight.Count;

        public Type leftType => typeof(TLeft);
        public Type rightType => typeof(TRight);

        public IEnumerator<PrimitiveMapPair<TLeft, TRight>> GetEnumerator()
        {
            foreach (var kvp in _leftToRight)
                yield return new PrimitiveMapPair<TLeft, TRight>(kvp.Key, kvp.Value);
        }

        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();

        public ObservablePrimitiveMap() : base() { }

        public ObservablePrimitiveMap(params PrimitiveMapPair<TLeft, TRight>[] values)
            : this((IEnumerable<PrimitiveMapPair<TLeft, TRight>>)values) { }

        public ObservablePrimitiveMap(IEnumerable<PrimitiveMapPair<TLeft, TRight>> values) : base()
        {
            if (values == null)
                return;

            foreach (var pair in values)
            {
                _leftToRight.Add(pair.left, pair.right);
                _rightToLeft.Add(pair.right, pair.left);
            }
        }

        public void Add(PrimitiveMapPair<TLeft, TRight> pair)
        {
            if (_leftToRight.ContainsKey(pair.left))
                throw new Exception($"{this} already contains left value {pair.left}");

            if (_rightToLeft.ContainsKey(pair.right))
                throw new Exception($"{this} already contains right value {pair.right}");

            _leftToRight.Add(pair.left, pair.right);
            _rightToLeft.Add(pair.right, pair.left);
            context.RegisterNodeChange(this, ChangeType.Add, collectionElement: pair);
        }

        public void Add(TLeft left, TRight right)
            => Add(new PrimitiveMapPair<TLeft, TRight>(left, right));

        public bool RemoveRight(TRight right)
        {
            if (_rightToLeft.TryGetValue(right, out var left))
            {
                _rightToLeft.Remove(right);
                _leftToRight.Remove(left);
                context.RegisterNodeChange(this, ChangeType.Remove, collectionElement: new PrimitiveMapPair<TLeft, TRight>(left, right));
                return true;
            }

            return false;
        }

        public bool RemoveLeft(TLeft left)
        {
            if (_leftToRight.TryGetValue(left, out var right))
            {
                _leftToRight.Remove(left);
                _rightToLeft.Remove(right);
                context.RegisterNodeChange(this, ChangeType.Remove, collectionElement: new PrimitiveMapPair<TLeft, TRight>(left, right));
                return true;
            }

            return false;
        }

        public bool Remove(TLeft left, TRight right)
            => Remove(new PrimitiveMapPair<TLeft, TRight>(left, right));

        public bool Remove(PrimitiveMapPair<TLeft, TRight> toRemove)
        {
            if (_leftToRight.TryGetValue(toRemove.left, out var right) && Equals(right, toRemove.right))
            {
                _leftToRight.Remove(toRemove.left);
                _rightToLeft.Remove(toRemove.right);
                context.RegisterNodeChange(this, ChangeType.Remove, collectionElement: toRemove);
                return true;
            }

            return false;
        }

        public TRight GetRight(TLeft left)
            => _leftToRight[left];

        public TLeft GetLeft(TRight right)
            => _rightToLeft[right];

        public bool TryGetLeft(TRight right, out TLeft left)
            => _rightToLeft.TryGetValue(right, out left);

        public bool TryGetRight(TLeft left, out TRight right)
            => _leftToRight.TryGetValue(left, out right);

        public void Clear()
        {
            foreach (var left in _leftToRight.Keys.ToArray())
                RemoveLeft(left);
        }

        public override void Reset()
        {
            Clear();
        }

        public override void ApplyChange(NodeChangeData change)
        {
            if (change.changeType == ChangeType.Dispose)
                return;


            if (change.changeType == ChangeType.Add)
            {
                var pair = (IPrimitiveMapPair)change.collectionElement;
                Add((TLeft)pair.left, (TRight)pair.right);
            }
            else if (change.changeType == ChangeType.Remove)
            {
                var pair = (IPrimitiveMapPair)change.collectionElement;
                if (!Equals(_leftToRight[(TLeft)pair.left], (TRight)pair.right))
                    throw new Exception($"{nodePath} does not contain ({pair.left}, {pair.right})");

                RemoveLeft((TLeft)pair.left);
            }
            else
            {
                throw new Exception($"{nameof(ObservablePrimitiveMap<TLeft, TRight>)} does not support change type {change.changeType}");
            }
        }

        public override void CopyTo(IObservableNode copyTo)
        {
            var dest = (ObservablePrimitiveMap<TLeft, TRight>)copyTo;
            var added = this.Where(x => !dest.TryGetRight(x.left, out var right) || !Equals(x.right, right)).ToArray();
            var removed = dest.Where(x => !this.TryGetRight(x.left, out var right) || !Equals(x.right, right)).ToArray();

            foreach (var toAdd in added)
            {
                dest.RemoveLeft(toAdd.left);
                dest.Add(toAdd.left, toAdd.right);
            }

            foreach (var toRemove in removed)
                dest.RemoveLeft(toRemove.left);
        }

        public override void FromJSON(JSONNode json)
        {
            Clear();

            if (json == null)
                return;

            var leftSerializer = JSONSerialization.GetSerializer<TLeft>();
            var rightSerializer = JSONSerialization.GetSerializer<TRight>();

            var array = (JSONArray)json;

            foreach (var pairJSON in array)
            {
                var pair = (JSONArray)pairJSON;
                Add(leftSerializer.fromJSON(pair[0]), rightSerializer.fromJSON(pair[0]));
            }
        }

        public override JSONNode ToJSON(Func<IObservableNode, bool> filter)
        {
            var leftSerializer = JSONSerialization.GetSerializer<TLeft>();
            var rightSerializer = JSONSerialization.GetSerializer<TRight>();

            var array = new JSONArray();

            foreach (var kvp in _leftToRight)
            {
                var pair = new JSONArray();
                pair.Add(leftSerializer.toJSON(kvp.Key));
                pair.Add(rightSerializer.toJSON(kvp.Value));
                array.Add(pair);
            }

            return array;
        }

        object IObservablePrimitiveMap.GetLeft(object right)
            => GetLeft((TRight)right);

        object IObservablePrimitiveMap.GetRight(object left)
            => GetRight((TLeft)left);

        void IObservablePrimitiveMap.Add(object entry)
            => Add((PrimitiveMapPair<TLeft, TRight>)entry);

        void IObservablePrimitiveMap.Add(object left, object right)
            => Add((TLeft)left, (TRight)right);

        bool IObservablePrimitiveMap.RemoveLeft(object left)
            => RemoveLeft((TLeft)left);

        bool IObservablePrimitiveMap.RemoveRight(object right)
            => RemoveRight((TRight)right);

        bool IObservablePrimitiveMap.Remove(object entry)
            => Remove((PrimitiveMapPair<TLeft, TRight>)entry);

        bool IObservablePrimitiveMap.Remove(object left, object right)
            => Remove((TLeft)left, (TRight)right);

        bool IObservablePrimitiveMap.TryGetLeft(object right, out object left)
        {
            if (TryGetLeft((TRight)right, out var l))
            {
                left = l;
                return true;
            }

            left = default(TLeft);
            return false;
        }

        bool IObservablePrimitiveMap.TryGetRight(object left, out object right)
        {
            if (TryGetRight((TLeft)left, out var r))
            {
                right = r;
                return true;
            }

            right = default(TRight);
            return false;
        }

        bool IObservableCollection<PrimitiveMapPair<TLeft, TRight>>.Contains(PrimitiveMapPair<TLeft, TRight> value)
            => TryGetRight(value.left, out var right) && Equals(value.right, right);

        public bool Contains(object value)
        {
            var pair = (PrimitiveMapPair<TLeft, TRight>)value;
            return TryGetRight(pair.left, out var right) && Equals(pair.right, right);
        }
    }
}