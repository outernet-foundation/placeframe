using System;
using System.Collections.Generic;
using NUnit.Framework;

namespace ObserveThing.Tests
{
    public class ManualDictionaryObservable<TKey, TValue> : IDictionaryObservable<TKey, TValue>
    {
        private Dictionary<TKey, TValue> _mostRecentDictionary = new Dictionary<TKey, TValue>();
        private DictionaryEventArgs<TKey, TValue> _args = new DictionaryEventArgs<TKey, TValue>();
        private List<Instance> _instances = new List<Instance>();
        private bool _disposing;


        public void OnAdd(TKey key, TValue value)
        {
            _mostRecentDictionary.Add(key, value);
            _args.element = new KeyValuePair<TKey, TValue>(key, value);
            _args.operationType = OpType.Add;
            foreach (var instance in _instances)
                instance.OnNext(_args);
        }

        public void OnRemove(TKey key)
        {
            if (!_mostRecentDictionary.TryGetValue(key, out var value))
                return;

            _mostRecentDictionary.Remove(key);

            _args.element = new KeyValuePair<TKey, TValue>(key, value);
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

        public IDisposable Subscribe(IObserver<IDictionaryEventArgs<TKey, TValue>> observer)
        {
            var instance = new Instance(observer, x =>
            {
                if (!_disposing)
                    _instances.Remove(x);
            });

            _instances.Add(instance);

            foreach (var kvp in _mostRecentDictionary)
            {
                _args.element = kvp;
                _args.operationType = OpType.Add;
                instance.OnNext(_args);
            }

            return instance;
        }

        private class Instance : IDisposable
        {
            private IObserver<IDictionaryEventArgs<TKey, TValue>> _observer;
            private Action<Instance> _onDispose;

            public Instance(IObserver<IDictionaryEventArgs<TKey, TValue>> observer, Action<Instance> onDispose)
            {
                _observer = observer;
                _onDispose = onDispose;
            }

            public void OnNext(IDictionaryEventArgs<TKey, TValue> args)
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

    public class DictionaryObservableTests
    {
        [Test]
        public void TestTrack()
        {
            int callCount = 0;
            (bool keyPresent, string value) value = default;
            (bool keyPresent, string value) previousValue = default;
            Exception exception = default;
            bool disposed = false;

            ManualDictionaryObservable<int, string> rootObservable = new ManualDictionaryObservable<int, string>();

            rootObservable.TrackDynamic(4).Subscribe(
                x =>
                {
                    callCount++;
                    value = x.currentValue;
                    previousValue = x.previousValue;
                },
                exc => exception = exc,
                () => disposed = true
            );

            Assert.AreEqual(0, callCount);
            Assert.AreEqual(false, value.keyPresent);
            Assert.AreEqual(default, value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            rootObservable.OnAdd(2, "cat");

            Assert.AreEqual(0, callCount);
            Assert.AreEqual(false, value.keyPresent);
            Assert.AreEqual(default, value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            rootObservable.OnAdd(4, "dog");

            Assert.AreEqual(1, callCount);
            Assert.AreEqual(true, value.keyPresent);
            Assert.AreEqual("dog", value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            rootObservable.OnRemove(2);

            Assert.AreEqual(1, callCount);
            Assert.AreEqual(true, value.keyPresent);
            Assert.AreEqual("dog", value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            rootObservable.OnRemove(40);

            Assert.AreEqual(1, callCount);
            Assert.AreEqual(true, value.keyPresent);
            Assert.AreEqual("dog", value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            rootObservable.OnRemove(4);

            Assert.AreEqual(2, callCount);
            Assert.AreEqual(false, value.keyPresent);
            Assert.AreEqual(default, value.value);
            Assert.AreEqual(true, previousValue.keyPresent);
            Assert.AreEqual("dog", previousValue.value);

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            rootObservable.DisposeAll();
            Assert.IsTrue(disposed);
        }

        [Test]
        public void TestTrackReactive()
        {
            int callCount = 0;
            (bool keyPresent, string value) value = default;
            (bool keyPresent, string value) previousValue = default;
            Exception exception = default;
            bool disposed = false;

            ManualDictionaryObservable<int, string> rootObservable = new ManualDictionaryObservable<int, string>();
            ManualValueObservable<int> keyProvider = new ManualValueObservable<int>();

            rootObservable.TrackDynamic(keyProvider).Subscribe(
                x =>
                {
                    callCount++;
                    value = x.currentValue;
                    previousValue = x.previousValue;
                },
                exc => exception = exc,
                () => disposed = true
            );

            Assert.AreEqual(0, callCount);
            Assert.AreEqual(false, value.keyPresent);
            Assert.AreEqual(default, value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            rootObservable.OnAdd(2, "cat");

            Assert.AreEqual(0, callCount);
            Assert.AreEqual(false, value.keyPresent);
            Assert.AreEqual(default, value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            keyProvider.OnNext(2);

            Assert.AreEqual(1, callCount);
            Assert.AreEqual(true, value.keyPresent);
            Assert.AreEqual("cat", value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            rootObservable.OnRemove(2);

            Assert.AreEqual(2, callCount);
            Assert.AreEqual(false, value.keyPresent);
            Assert.AreEqual(default, value.value);
            Assert.AreEqual(true, previousValue.keyPresent);
            Assert.AreEqual("cat", previousValue.value);

            rootObservable.OnRemove(40);

            Assert.AreEqual(2, callCount);
            Assert.AreEqual(false, value.keyPresent);
            Assert.AreEqual(default, value.value);
            Assert.AreEqual(true, previousValue.keyPresent);
            Assert.AreEqual("cat", previousValue.value);

            rootObservable.OnAdd(2, "dog");

            Assert.AreEqual(3, callCount);
            Assert.AreEqual(true, value.keyPresent);
            Assert.AreEqual("dog", value.value);
            Assert.AreEqual(false, previousValue.keyPresent);
            Assert.AreEqual(default, previousValue.value);

            var exc = new Exception();
            rootObservable.OnError(exc);
            Assert.AreEqual(exc, exception);

            var keyProviderExc = new Exception();
            rootObservable.OnError(keyProviderExc);
            Assert.AreEqual(keyProviderExc, exception);

            rootObservable.DisposeAll();
            Assert.IsTrue(disposed);
        }
    }
}