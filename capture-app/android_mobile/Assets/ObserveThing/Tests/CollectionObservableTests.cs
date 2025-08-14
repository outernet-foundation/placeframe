using System;
using System.Collections.Generic;
using System.Linq;
using NUnit.Framework;

namespace ObserveThing.Tests
{
    public class ManualCollectionObservable<T> : ICollectionObservable<T>
    {
        private List<T> _mostRecentCollection = new List<T>();
        private CollectionEventArgs<T> _args = new CollectionEventArgs<T>();
        private List<Instance> _instances = new List<Instance>();
        private bool _disposing;

        public ManualCollectionObservable() { }
        public ManualCollectionObservable(IEnumerable<T> values)
        {
            _mostRecentCollection.AddRange(values);
        }

        public void OnAdd(T added)
        {
            _mostRecentCollection.Add(added);
            _args.element = added;
            _args.operationType = OpType.Add;
            foreach (var instance in _instances)
                instance.OnNext(_args);
        }

        public void OnRemove(T removed)
        {
            _mostRecentCollection.Remove(removed);
            _args.element = removed;
            _args.operationType = OpType.Remove;
            foreach (var instance in _instances)
                instance.OnNext(_args);
        }

        public void OnError(Exception exception)
        {
            foreach (var instance in _instances)
                instance.OnError(exception);
        }

        public void DisposeAll()
        {
            _disposing = true;

            foreach (var instance in _instances)
                instance.Dispose();

            _instances.Clear();

            _disposing = false;
        }

        public IDisposable Subscribe(IObserver<ICollectionEventArgs<T>> observer)
        {
            var instance = new Instance(observer, x =>
            {
                if (!_disposing)
                    _instances.Remove(x);
            });

            _instances.Add(instance);

            foreach (var kvp in _mostRecentCollection)
            {
                _args.element = kvp;
                _args.operationType = OpType.Add;
                instance.OnNext(_args);
            }

            return instance;
        }

        private class Instance : IDisposable
        {
            private IObserver<ICollectionEventArgs<T>> _observer;
            private Action<Instance> _onDispose;

            public Instance(IObserver<ICollectionEventArgs<T>> observer, Action<Instance> onDispose)
            {
                _observer = observer;
                _onDispose = onDispose;
            }

            public void OnNext(ICollectionEventArgs<T> args)
            {
                _observer?.OnNext(args);
            }

            public void OnError(Exception error)
            {
                _observer?.OnError(error);
            }

            public void Dispose()
            {
                if (_observer == null)
                    throw new Exception("ALREADY DISPOSED");

                _observer.OnDispose();
                _observer = null;

                _onDispose(this);
            }
        }
    }

    public class CollectionObservableTests
    {
        private T Peek<T>(IValueObservable<T> observable)
        {
            T result = default;
            var observer = observable.Subscribe(x => result = x.currentValue);
            observer.Dispose();
            return result;
        }

        private List<T> Peek<T>(IListObservable<T> observable)
        {
            List<T> result = new List<T>();
            var observer = observable.Subscribe(x => result.Add(x.element));
            observer.Dispose();
            return result;
        }

        private void AreEqual<T>(T expected, IValueObservable<T> observable)
            => Assert.AreEqual(expected, Peek(observable));

        private void AreEqual<T>(IEnumerable<T> expected, IEnumerable<IValueObservable<T>> actual)
            => Assert.AreEqual(expected, actual.Select(x => Peek(x)));

        private void AreEqual<T>(IEnumerable<T> expected, IListObservable<T> observable)
            => Assert.AreEqual(expected, observable);

        [Test]
        public void TestOrderBy()
        {
            int callCount = 0;
            List<int> results = new List<int>();
            Exception exception = default;
            bool disposed = false;

            var rootObservable = new ManualCollectionObservable<int>();
            var orderByObservable = rootObservable.OrderByDynamic(x => x).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Insert(x.index, x.element);
                    }
                    else
                    {
                        results.RemoveAt(x.index);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            rootObservable.OnAdd(1);
            rootObservable.OnAdd(2);
            rootObservable.OnAdd(13);
            rootObservable.OnAdd(2);
            rootObservable.OnAdd(4);

            Assert.AreEqual(5, callCount);
            Assert.AreEqual(new int[] { 1, 2, 2, 4, 13 }, results);

            rootObservable.OnRemove(2);

            Assert.AreEqual(6, callCount);
            Assert.AreEqual(new int[] { 1, 2, 4, 13 }, results);

            rootObservable.OnRemove(22);

            Assert.AreEqual(6, callCount);
            Assert.AreEqual(new int[] { 1, 2, 4, 13 }, results);

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            orderByObservable.Dispose();
            Assert.IsTrue(disposed);

            rootObservable.OnRemove(4);

            Assert.AreEqual(6, callCount);
            Assert.AreEqual(new int[] { 1, 2, 4, 13 }, results);
        }

        [Test]
        public void TestOrderByReactive()
        {
            int callCount = 0;
            List<ManualValueObservable<int>> results = new List<ManualValueObservable<int>>();
            Exception exception = default;
            bool disposed = false;

            var rootObservable = new ManualCollectionObservable<ManualValueObservable<int>>();
            var orderByObservable = rootObservable.OrderByDynamic(x => x.AsObservable()).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Insert(x.index, x.element);
                    }
                    else
                    {
                        results.RemoveAt(x.index);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            rootObservable.OnAdd(new ManualValueObservable<int>(1));
            rootObservable.OnAdd(new ManualValueObservable<int>(2));
            rootObservable.OnAdd(new ManualValueObservable<int>(13));
            rootObservable.OnAdd(new ManualValueObservable<int>(2));
            rootObservable.OnAdd(new ManualValueObservable<int>(4));

            Assert.AreEqual(5, callCount);
            AreEqual(new int[] { 1, 2, 2, 4, 13 }, results);

            rootObservable.OnRemove(results[1]);

            Assert.AreEqual(6, callCount);
            AreEqual(new int[] { 1, 2, 4, 13 }, results);

            results[1].OnNext(22);

            Assert.AreEqual(8, callCount);
            AreEqual(new int[] { 1, 4, 13, 22 }, results);

            results[2].OnNext(-33);

            Assert.AreEqual(10, callCount);
            AreEqual(new int[] { -33, 1, 4, 22 }, results);

            var multiAdd = new ManualValueObservable<int>(3);

            rootObservable.OnAdd(multiAdd);
            rootObservable.OnAdd(multiAdd);
            rootObservable.OnAdd(multiAdd);
            rootObservable.OnAdd(multiAdd);
            rootObservable.OnAdd(multiAdd);

            Assert.AreEqual(15, callCount);
            AreEqual(new int[] { -33, 1, 3, 3, 3, 3, 3, 4, 22 }, results);

            multiAdd.OnNext(10);

            Assert.AreEqual(25, callCount);
            AreEqual(new int[] { -33, 1, 4, 10, 10, 10, 10, 10, 22 }, results);

            rootObservable.OnRemove(multiAdd);
            rootObservable.OnRemove(multiAdd);

            Assert.AreEqual(27, callCount);
            AreEqual(new int[] { -33, 1, 4, 10, 10, 10, 22 }, results);

            multiAdd.OnNext(1);

            Assert.AreEqual(33, callCount);
            AreEqual(new int[] { -33, 1, 1, 1, 1, 4, 22 }, results);

            multiAdd.OnNext(5);

            Assert.AreEqual(39, callCount);
            AreEqual(new int[] { -33, 1, 4, 5, 5, 5, 22 }, results);

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            orderByObservable.Dispose();
            Assert.IsTrue(disposed);

            rootObservable.OnRemove(results[1]);

            AreEqual(new int[] { -33, 1, 4, 5, 5, 5, 22 }, results);
        }

        [Test]
        public void TestWhere()
        {
            int callCount = 0;
            List<int> results = new List<int>();
            Exception exception = default;
            bool disposed = false;

            var rootObservable = new ManualCollectionObservable<int>();
            var whereObservable = rootObservable.WhereDynamic(x => x % 2 == 0).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Add(x.element);
                    }
                    else
                    {
                        results.Remove(x.element);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            rootObservable.OnAdd(1);
            rootObservable.OnAdd(6);
            rootObservable.OnAdd(13);
            rootObservable.OnAdd(2);
            rootObservable.OnAdd(4);

            Assert.AreEqual(3, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 2, 4 }));

            rootObservable.OnRemove(2);

            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 4 }));

            rootObservable.OnRemove(22);

            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 4 }));

            rootObservable.OnRemove(13);

            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 4 }));

            rootObservable.OnAdd(13);

            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 4 }));

            rootObservable.OnAdd(8);

            Assert.AreEqual(5, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 4, 8 }));

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            whereObservable.Dispose();
            Assert.IsTrue(disposed);

            rootObservable.OnRemove(4);

            Assert.AreEqual(5, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 4, 8 }));
        }

        [Test]
        public void TestWhereReactive()
        {
            int callCount = 0;
            List<ManualValueObservable<int>> results = new List<ManualValueObservable<int>>();
            Exception exception = default;
            bool disposed = false;

            var rootObservable = new ManualCollectionObservable<ManualValueObservable<int>>();
            var whereObservable = rootObservable.WhereDynamic(x => x.SelectDynamic(x => x % 2 == 0)).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Add(x.element);
                    }
                    else
                    {
                        results.Remove(x.element);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            var v1 = new ManualValueObservable<int>(1);
            var v2 = new ManualValueObservable<int>(6);
            var v3 = new ManualValueObservable<int>(13);
            var v4 = new ManualValueObservable<int>(2);
            var v5 = new ManualValueObservable<int>(4);

            rootObservable.OnAdd(v1);
            rootObservable.OnAdd(v2);
            rootObservable.OnAdd(v3);
            rootObservable.OnAdd(v4);
            rootObservable.OnAdd(v5);

            Assert.AreEqual(3, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v4, v5 }));

            rootObservable.OnRemove(v4);

            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));

            rootObservable.OnRemove(new ManualValueObservable<int>(22));

            Assert.IsNotNull(exception);
            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));

            exception = null;
            rootObservable.OnRemove(new ManualValueObservable<int>(6));

            Assert.IsNotNull(exception);
            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));

            rootObservable.OnRemove(v3);

            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));

            rootObservable.OnAdd(v3);

            Assert.AreEqual(4, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));

            var v6 = new ManualValueObservable<int>(8);

            rootObservable.OnAdd(v6);

            Assert.AreEqual(5, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5, v6 }));

            v6.OnNext(7);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));

            v2.OnNext(8);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            whereObservable.Dispose();
            Assert.IsTrue(disposed);

            rootObservable.OnRemove(v2);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new[] { v2, v5 }));
        }

        [Test]
        public void TestDistinct()
        {
            int callCount = 0;
            List<int> results = new List<int>();
            Exception exception = default;
            bool disposed = false;

            var rootObservable = new ManualCollectionObservable<int>();
            var distinctObservable = rootObservable.DistinctDynamic().Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Add(x.element);
                    }
                    else
                    {
                        results.Remove(x.element);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            rootObservable.OnAdd(1);
            rootObservable.OnAdd(6);
            rootObservable.OnAdd(6);
            rootObservable.OnAdd(6);
            rootObservable.OnAdd(13);
            rootObservable.OnAdd(2);
            rootObservable.OnAdd(4);
            rootObservable.OnAdd(4);

            Assert.AreEqual(5, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 6, 2, 4, 13 }));

            rootObservable.OnRemove(4);

            Assert.AreEqual(5, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 6, 2, 4, 13 }));

            rootObservable.OnRemove(1);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 2, 4, 13 }));

            rootObservable.OnAdd(13);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 2, 4, 13 }));

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            distinctObservable.Dispose();
            Assert.IsTrue(disposed);

            rootObservable.OnAdd(100);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 6, 2, 4, 13 }));
        }

        [Test]
        public void TestConcat()
        {
            int callCount = 0;
            List<int> results = new List<int>();
            Exception exception = default;
            bool disposed = false;

            var rootObservable = new ManualCollectionObservable<int>();
            var concatObservable = rootObservable.ConcatDynamic(new int[] { 4, 5, 6 }).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Add(x.element);
                    }
                    else
                    {
                        results.Remove(x.element);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            rootObservable.OnAdd(1);
            rootObservable.OnAdd(2);
            rootObservable.OnAdd(3);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6 }));

            rootObservable.OnAdd(7);

            Assert.AreEqual(7, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 7 }));

            rootObservable.OnRemove(1);

            Assert.AreEqual(8, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 2, 3, 4, 5, 6, 7 }));

            rootObservable.OnAdd(4);

            Assert.AreEqual(9, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 2, 3, 4, 4, 5, 6, 7 }));

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            rootObservable.DisposeAll();
            Assert.IsTrue(disposed);

            rootObservable.OnAdd(100);

            Assert.AreEqual(9, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 2, 3, 4, 4, 5, 6, 7 }));
        }

        [Test]
        public void TestConcatReactive()
        {
            int callCount = 0;
            List<int> results = new List<int>();
            Exception exception = default;
            bool disposed = false;

            var observable1 = new ManualCollectionObservable<int>();
            var observable2 = new ManualCollectionObservable<int>();
            var concatObservable = observable1.ConcatDynamic(observable2).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Add(x.element);
                    }
                    else
                    {
                        results.Remove(x.element);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            observable1.OnAdd(1);
            observable1.OnAdd(2);
            observable1.OnAdd(3);

            observable2.OnAdd(4);
            observable2.OnAdd(5);
            observable2.OnAdd(6);

            Assert.AreEqual(6, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6 }));

            observable2.OnAdd(7);

            Assert.AreEqual(7, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 7 }));

            observable2.OnRemove(4);

            Assert.AreEqual(8, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 5, 6, 7 }));

            observable1.OnAdd(8);

            Assert.AreEqual(9, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 5, 6, 7, 8 }));

            observable1.OnRemove(3);

            Assert.AreEqual(10, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 5, 6, 7, 8 }));

            observable2.OnAdd(8);

            Assert.AreEqual(11, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 5, 6, 7, 8, 8 }));

            observable1.OnRemove(8);

            Assert.AreEqual(12, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 5, 6, 7, 8 }));

            var exc1 = new Exception();
            observable1.OnError(exc1);
            Assert.AreEqual(exc1, exception);

            observable1.DisposeAll();
            Assert.IsTrue(disposed);

            observable2.OnAdd(100);

            Assert.AreEqual(12, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 5, 6, 7, 8 }));
        }

        [Test]
        public void TestSelectMany()
        {
            int callCount = 0;
            List<int> results = new List<int>();
            Exception exception = default;
            bool disposed = false;

            var observableRoot = new ManualCollectionObservable<int[]>();
            var concatObservable = observableRoot.SelectManyDynamic(x => x).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Add(x.element);
                    }
                    else
                    {
                        results.Remove(x.element);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            var arr1 = new[] { 1, 2, 3 };
            var arr2 = new[] { 4, 5, 6 };
            var arr3 = new[] { 7, 8, 9 };

            observableRoot.OnAdd(arr1);
            observableRoot.OnAdd(arr2);
            observableRoot.OnAdd(arr3);

            Assert.AreEqual(9, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 7, 8, 9 }));

            observableRoot.OnRemove(arr2);

            Assert.AreEqual(12, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 7, 8, 9 }));

            observableRoot.OnAdd(arr2);
            observableRoot.OnAdd(arr2);

            Assert.AreEqual(18, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8, 9 }));

            var exc = new Exception();
            observableRoot.OnError(exc);
            Assert.AreEqual(exc, exception);

            observableRoot.DisposeAll();
            Assert.IsTrue(disposed);

            observableRoot.OnAdd(arr1);

            Assert.AreEqual(18, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8, 9 }));
        }

        [Test]
        public void TestSelectManyReactive()
        {
            int callCount = 0;
            List<int> results = new List<int>();
            Exception exception = default;
            bool disposed = false;

            var observableRoot = new ManualCollectionObservable<ManualCollectionObservable<int>>();
            var concatObservable = observableRoot.SelectManyDynamic(x => x).Subscribe(
                x =>
                {
                    callCount++;
                    if (x.operationType == OpType.Add)
                    {
                        results.Add(x.element);
                    }
                    else
                    {
                        results.Remove(x.element);
                    }
                },
                exc => exception = exc,
                () => disposed = true
            );

            var arr1 = new ManualCollectionObservable<int>(new[] { 1, 2, 3 });
            var arr2 = new ManualCollectionObservable<int>(new[] { 4, 5, 6 });
            var arr3 = new ManualCollectionObservable<int>(new[] { 7, 8, 9 });

            observableRoot.OnAdd(arr1);
            observableRoot.OnAdd(arr2);
            observableRoot.OnAdd(arr3);

            Assert.AreEqual(9, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 7, 8, 9 }));

            observableRoot.OnRemove(arr2);

            Assert.AreEqual(12, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 7, 8, 9 }));

            observableRoot.OnAdd(arr2);
            observableRoot.OnAdd(arr2);

            Assert.AreEqual(18, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8, 9 }));

            arr1.OnAdd(100);

            Assert.AreEqual(19, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8, 9, 100 }));

            arr3.OnRemove(9);

            Assert.AreEqual(20, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8, 100 }));

            arr2.OnRemove(5);

            Assert.AreEqual(22, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 6, 4, 6, 7, 8, 100 }));

            arr2.OnAdd(44);

            Assert.AreEqual(24, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 6, 4, 6, 7, 8, 100, 44, 44 }));

            var exc = new Exception();
            observableRoot.OnError(exc);
            Assert.AreEqual(exc, exception);

            observableRoot.DisposeAll();
            Assert.IsTrue(disposed);

            observableRoot.OnAdd(arr1);

            Assert.AreEqual(24, callCount);
            Assert.That(results, Is.EquivalentTo(new int[] { 1, 2, 3, 4, 6, 4, 6, 7, 8, 100, 44, 44 }));
        }
    }
}