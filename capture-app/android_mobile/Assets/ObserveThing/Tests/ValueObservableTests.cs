using System;
using System.Linq;
using System.Collections.Generic;
using NUnit.Framework;

namespace ObserveThing.Tests
{
    public class ManualValueObservable<T> : IValueObservable<T>
    {
        private T _mostRecentValue = default;
        private ValueEventArgs<T> _args = new ValueEventArgs<T>();
        private List<Instance> _instances = new List<Instance>();
        private bool _disposing;

        public ManualValueObservable() : this(default) { }
        public ManualValueObservable(T startValue)
        {
            _mostRecentValue = startValue;
        }

        public void OnNext(T value)
        {
            _args.currentValue = value;
            _args.previousValue = _mostRecentValue;

            _mostRecentValue = value;

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

        public IDisposable Subscribe(IObserver<IValueEventArgs<T>> observer)
        {
            var instance = new Instance(observer, x =>
            {
                if (!_disposing)
                    _instances.Remove(x);
            });

            _instances.Add(instance);

            _args.previousValue = default;
            _args.currentValue = _mostRecentValue;

            instance.OnNext(_args);
            return instance;
        }

        private class Instance : IDisposable
        {
            private IObserver<IValueEventArgs<T>> _observer;
            private Action<Instance> _onDispose;

            public Instance(IObserver<IValueEventArgs<T>> observer, Action<Instance> onDispose)
            {
                _observer = observer;
                _onDispose = onDispose;
            }

            public void OnNext(IValueEventArgs<T> args)
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

    public class ObserveThingTests
    {
        [Test]
        public void TestSelect()
        {
            int callCount = 0;
            int count = 0;
            int prevCount = 0;

            Exception exception = null;
            bool disposed = false;

            var rootObservable = new ManualValueObservable<string>();
            var selectObservable = rootObservable
                .SelectDynamic(x => x?.Count(x => x == 'a') ?? 0)
                .Subscribe(
                    x =>
                    {
                        callCount++;
                        count = x.currentValue;
                        prevCount = x.previousValue;
                    },
                    exc => exception = exc,
                    () => disposed = true
                );

            Assert.AreEqual(1, callCount); //init call

            rootObservable.OnNext("a");
            Assert.AreEqual(2, callCount);
            Assert.AreEqual(1, count);
            Assert.AreEqual(0, prevCount);

            rootObservable.OnNext("aa");
            Assert.AreEqual(3, callCount);
            Assert.AreEqual(2, count);
            Assert.AreEqual(1, prevCount);

            rootObservable.OnNext("aaa");
            Assert.AreEqual(4, callCount);
            Assert.AreEqual(3, count);
            Assert.AreEqual(2, prevCount);

            rootObservable.OnNext("aaaa");
            Assert.AreEqual(5, callCount);
            Assert.AreEqual(4, count);
            Assert.AreEqual(3, prevCount);

            rootObservable.OnNext("bbba");
            Assert.AreEqual(6, callCount);
            Assert.AreEqual(1, count);
            Assert.AreEqual(4, prevCount);

            rootObservable.OnNext("ccca");
            Assert.AreEqual(6, callCount);
            Assert.AreEqual(1, count);
            Assert.AreEqual(4, prevCount);

            var exc = new Exception("This is an exception");
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);
            Assert.IsFalse(disposed);

            rootObservable.OnNext("bcccb");
            Assert.AreEqual(7, callCount);
            Assert.AreEqual(0, count);
            Assert.AreEqual(1, prevCount);

            rootObservable.DisposeAll();
            Assert.IsTrue(disposed);
        }

        [Test]
        public void TestSelectReactive()
        {
            int callCount = 0;
            int result = 0;
            int prevResult = 0;

            Exception exception = null;
            bool disposed = false;

            var rootObservable = new ManualValueObservable<bool>();
            var intObservable1 = new ManualValueObservable<int>();
            var intObservable2 = new ManualValueObservable<int>();

            var selectObservable = rootObservable
                .SelectDynamic(x => x ? intObservable2.AsObservable() : intObservable1.AsObservable())
                .Subscribe(
                    x =>
                    {
                        callCount++;
                        result = x.currentValue;
                        prevResult = x.previousValue;
                    },
                    exc => exception = exc,
                    () => disposed = true
                );

            Assert.AreEqual(1, callCount); // init call

            intObservable1.OnNext(1);
            Assert.AreEqual(2, callCount);
            Assert.AreEqual(1, result);
            Assert.AreEqual(0, prevResult);

            intObservable2.OnNext(2);
            Assert.AreEqual(2, callCount);
            Assert.AreEqual(1, result);
            Assert.AreEqual(0, prevResult);

            rootObservable.OnNext(true);
            Assert.AreEqual(3, callCount);
            Assert.AreEqual(2, result);
            Assert.AreEqual(1, prevResult);

            intObservable2.OnNext(8);
            Assert.AreEqual(4, callCount);
            Assert.AreEqual(8, result);
            Assert.AreEqual(2, prevResult);

            intObservable1.OnError(new Exception());
            Assert.IsNull(exception);

            Exception exc2 = new Exception();
            intObservable2.OnError(exc2);
            Assert.AreEqual(exception, exc2);

            Exception excRoot = new Exception();
            rootObservable.OnError(excRoot);
            Assert.AreEqual(exception, excRoot);

            intObservable2.DisposeAll();
            Assert.IsFalse(disposed); //should not produce an OnDisposed call

            rootObservable.OnNext(false);
            Assert.AreEqual(5, callCount);
            Assert.AreEqual(1, result);
            Assert.AreEqual(8, prevResult);
        }

        [Test]
        public void TestWith()
        {
            int callCount = 0;
            (int value1, int value2) result = default;
            (int value1, int value2) prevResult = default;

            Exception exception = null;
            bool disposed = false;

            var intObservable1 = new ManualValueObservable<int>();
            var intObservable2 = new ManualValueObservable<int>();

            var selectObservable = intObservable1.WithDynamic(intObservable2)
                .Subscribe(
                    x =>
                    {
                        callCount++;
                        result = x.currentValue;
                        prevResult = x.previousValue;
                    },
                    exc => exception = exc,
                    () => disposed = true
                );

            Assert.AreEqual(1, callCount); // init call

            intObservable1.OnNext(1);
            Assert.AreEqual(2, callCount);
            Assert.AreEqual(1, result.value1);
            Assert.AreEqual(0, result.value2);
            Assert.AreEqual(0, prevResult.value1);
            Assert.AreEqual(0, prevResult.value2);

            intObservable2.OnNext(2);
            Assert.AreEqual(3, callCount);
            Assert.AreEqual(1, result.value1);
            Assert.AreEqual(2, result.value2);
            Assert.AreEqual(1, prevResult.value1);
            Assert.AreEqual(0, prevResult.value2);

            var exc1 = new Exception();
            intObservable1.OnError(exc1);
            Assert.AreEqual(exception, exc1);

            var exc2 = new Exception();
            intObservable2.OnError(exc2);
            Assert.AreEqual(exception, exc2);

            intObservable1.DisposeAll();
            Assert.IsTrue(disposed);

            disposed = false;

            intObservable2.DisposeAll();
            Assert.IsFalse(disposed); //should not produce dispose call
        }
    }
}