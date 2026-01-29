using System;
using System.Linq;
using System.Collections;
using System.Collections.Generic;

using SimpleJSON;

namespace FofX.Stateful
{
    public interface IObservableList : IObservableNode, IObservableCollection
    {
        Type itemType { get; }
        IObservableNode this[int index] { get; }
        IObservableNode Insert(int index);
        void RemoveAt(int index);
        IObservableNode Add();
        bool Remove(IObservableNode node);
        int IndexOf(IObservableNode node);
        void Clear();
    }

    public sealed class ObservableList<T> : ObservableNode, IObservableList, IObservableCollection<T> where T : IObservableNode, new()
    {
        public T this[int index] => _list[index];

        public int count => _list.Count;
        public override bool isDefault => _list.Count == 0;

        IEnumerator<T> IEnumerable<T>.GetEnumerator() => _list.GetEnumerator();
        IEnumerator IEnumerable.GetEnumerator() => _list.GetEnumerator();

        Type IObservableList.itemType => typeof(T);

        IObservableNode IObservableList.this[int index] => this[index];

        private List<T> _list = new List<T>();

        public ObservableList() : base() { }

        public ObservableList(params T[] values)
            : this((IEnumerable<T>)values) { }

        public ObservableList(IEnumerable<T> values) : base()
        {
            if (values == null)
                return;

            foreach (var element in values)
                _list.Add(element);
        }

        protected override void InitializeInternal()
        {
            base.InitializeInternal();

            for (int i = 0; i < _list.Count; i++)
                AddChildInternal(i.ToString(), _list[i]);
        }

        public T Insert(int index)
        {
            for (int i = _list.Count - 1; i >= index; i--)
                RenameChild(i.ToString(), (i + 1).ToString());

            T item = new T();
            _list.Insert(index, item);
            AddChildInternal(index.ToString(), item);

            context.RegisterNodeChange(this, ChangeType.Add, index: index, child: item, collectionElement: item);
            return item;
        }

        public void RemoveAt(int index)
        {
            T item = _list[index];
            _list.RemoveAt(index);
            RemoveChildInternal(item);

            for (int i = index; i < _list.Count; i++)
                RenameChild((i + 1).ToString(), i.ToString());

            context.RegisterNodeChange(this, ChangeType.Remove, index: index, child: item, collectionElement: item);
        }

        public T Add()
        {
            return Insert(_list.Count);
        }

        public bool Remove(T item)
        {
            int index = _list.IndexOf(item);
            if (index == -1)
                return false;

            RemoveAt(index);

            return true;
        }

        public void Clear()
        {
            while (_list.Count > 0)
                RemoveAt(_list.Count - 1);
        }

        public bool Contains(T item)
        {
            return _list.Contains(item);
        }

        public int IndexOf(T item)
        {
            return _list.IndexOf(item);
        }

        public int FindIndex(Predicate<T> match)
        {
            return _list.FindIndex(match);
        }

        public override void ApplyChange(NodeChangeData change)
        {
            if (change.changeType == ChangeType.Dispose)
                return;

            if (change.changeType == ChangeType.Add)
            {
                Insert(change.index.Value);
            }
            else if (change.changeType == ChangeType.Remove)
            {
                RemoveAt(change.index.Value);
            }
            else
            {
                throw new Exception($"{nameof(ObservableList<T>)} does not support change type {change.changeType}");
            }
        }

        public override void CopyTo(IObservableNode copyTo)
        {
            if (copyTo is not ObservableList<T> copyToList)
                throw new Exception($"{copyTo.nodePath} is not a {nameof(ObservableList<T>)}");

            while (copyToList.count < count)
                copyToList.Add();

            while (copyToList.count > count)
                copyToList.RemoveAt(copyToList.count - 1);

            for (int i = 0; i < count; i++)
                _list[i].CopyTo(copyToList[i]);
        }

        public override void Reset()
        {
            Clear();
        }

        IObservableNode IObservableList.Insert(int index)
        {
            return Insert(index);
        }

        IObservableNode IObservableList.Add()
        {
            return Add();
        }

        bool IObservableList.Remove(IObservableNode node)
        {
            return Remove((T)node);
        }

        int IObservableList.IndexOf(IObservableNode node)
        {
            return IndexOf((T)node);
        }

        public override JSONNode ToJSON(Func<IObservableNode, bool> filter)
        {
            JSONArray array = new JSONArray();

            for (int i = 0; i < _list.Count; i++)
            {
                var item = _list[i];
                if (filter(item))
                    array.Add(item.ToJSON(filter));
            }

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

            while (count > array.Count)
                RemoveAt(count - 1);

            while (count < array.Count)
                Add();

            for (int i = 0; i < count; i++)
                _list[i].FromJSON(array[i]);
        }

        bool IObservableCollection.Contains(object value)
            => Contains((T)value);
    }
}