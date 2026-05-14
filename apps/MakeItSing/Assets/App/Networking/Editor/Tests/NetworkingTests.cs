using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FofX;
using FofX.Stateful;
using NUnit.Framework;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class NetworkingTests
    {
        public class TestState : StateObject
        {
            public StateValue<string> value { get; private set; }
            public StateDictionary<int, StateValue<string>> valueDict { get; private set; }
            public StateList<StateValue<string>> valueList { get; private set; }
            public StateValueSet<string> set { get; private set; }

            public StateDictionary<string, NestedTestState> stateDict { get; private set; }
            public StateList<NestedTestState> stateList { get; private set; }

            public NestedTestState nestedState { get; private set; }
        }

        public class NestedTestState : StateObject
        {
            public StateValue<string> value { get; private set; }
            public StateDictionary<int, StateValue<string>> valueDict { get; private set; }
            public StateList<StateValue<string>> valueList { get; private set; }
            public StateValueSet<string> set { get; private set; }

            public StateDictionary<Vector3, DoubleNestedState> stateDict { get; private set; }
            public StateList<DoubleNestedState> stateList { get; private set; }

            public DoubleNestedState nestedState { get; private set; }
        }

        public class DoubleNestedState : StateObject
        {
            public StateValue<string> value { get; private set; }
            public StateDictionary<int, StateValue<string>> valueDict { get; private set; }
            public StateList<StateValue<string>> valueList { get; private set; }
            public StateValueSet<string> set { get; private set; }
        }

        [Test]
        public void TestPathCacheGeneration()
        {
            var idCache = new PathIDCache<TestState>();
            var state = new TestState();
            state.Initialize(new ObserveThing.ObservationContext(), new DefaultLogger() { logLevel = LogLevel.None });
            PopulateCollections(state);

            using (var stream = new MemoryStream())
            {
                using (var writer = new BinaryWriter(stream, encoding: System.Text.Encoding.UTF8, leaveOpen: true))
                    WriteStatePathsRecursive(idCache, state, state, writer);

                stream.Position = 0;

                using (var reader = new BinaryReader(stream, encoding: System.Text.Encoding.UTF8, leaveOpen: true))
                    ReadStatePathsRecursive(idCache, state, state, reader);

                stream.Position = 0;

                using (var reader = new BinaryReader(stream, encoding: System.Text.Encoding.UTF8, leaveOpen: true))
                    TryReadStatePathsRecursive(idCache, state, state, reader);

                idCache.ClearCaches();

                stream.Position = 0;

                using (var reader = new BinaryReader(stream, encoding: System.Text.Encoding.UTF8, leaveOpen: true))
                    TryReadStatePathsRecursive(idCache, state, state, reader);

                stream.Position = 0;

                using (var reader = new BinaryReader(stream, encoding: System.Text.Encoding.UTF8, leaveOpen: true))
                    ReadStatePathsRecursive(idCache, state, state, reader);
            }
        }

        private void PopulateCollections(IStateNode stateNode)
        {
            if (stateNode is IStateList list)
            {
                list.Add();
            }
            else if (stateNode is IStateDictionary dictionary)
            {
                if (dictionary.keyType == typeof(string))
                {
                    dictionary.Add("DEFAULT");
                }
                else
                {
                    dictionary.Add(Activator.CreateInstance(dictionary.keyType));
                }
            }

            foreach (var child in stateNode.children)
                PopulateCollections(child);
        }

        private void WriteStatePathsRecursive<T>(PathIDCache<T> idCache, IStateNode state, T relativeTo, BinaryWriter writer) where T : class, IStateNode, new()
        {
            if (!(state is StateObject))
                idCache.WritePath(state, relativeTo, writer);

            foreach (var child in state.children.OrderBy(x => x.nodeName))
                WriteStatePathsRecursive(idCache, child, relativeTo, writer);
        }

        private void ReadStatePathsRecursive<T>(PathIDCache<T> idCache, T root, IStateNode state, BinaryReader reader) where T : class, IStateNode, new()
        {
            if (!(state is StateObject))
            {
                var result = idCache.ReadPath(root, reader);
                Assert.AreEqual(state, result);
            }

            foreach (var child in state.children.OrderBy(x => x.nodeName))
                ReadStatePathsRecursive(idCache, root, child, reader);
        }

        private void TryReadStatePathsRecursive<T>(PathIDCache<T> idCache, T root, IStateNode state, BinaryReader reader) where T : class, IStateNode, new()
        {
            if (!(state is StateObject))
            {
                var found = idCache.TryReadPath(root, reader, out var result);
                Assert.IsTrue(found);
                Assert.AreEqual(state, result);
            }

            foreach (var child in state.children.OrderBy(x => x.nodeName))
                ReadStatePathsRecursive(idCache, root, child, reader);
        }
    }
}