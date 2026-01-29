using System.Collections;
using System.Collections.Generic;

namespace FofX.Stateful
{
    public interface IObservableCollection : IObservableNode, IEnumerable
    {
        int count { get; }
        bool Contains(object value);
    }

    public interface IObservableCollection<T> : IObservableCollection, IEnumerable<T>
    {
        bool Contains(T value);
    }
}
