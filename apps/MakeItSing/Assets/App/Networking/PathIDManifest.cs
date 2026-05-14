using System;
using System.Collections.Generic;
using System.Linq;
using FofX.Stateful;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class PathData
    {
        public uint id { get; }
        public string signature { get; }
        public string[] pathSegments { get; }
        public Serializer[] keySerializers { get; }

        public PathData(uint id, string signature, Serializer[] keySerializers)
        {
            this.id = id;
            this.signature = signature;
            this.pathSegments = signature.Split('/').ToArray();
            this.keySerializers = keySerializers;
        }
    }

    public class PathIDManifest<T> where T : class, IStateNode, new()
    {
        private static List<string> _signatureBuilder = new List<string>();
        private static Dictionary<Type, Func<object>> _defaultInstanceConstructors = new Dictionary<Type, Func<object>>()
        {
            { typeof(string), () => "DEFAULT" },
        };

        private Dictionary<uint, PathData> _pathDataById = new Dictionary<uint, PathData>();
        private Dictionary<string, PathData> _pathDataBySignature = new Dictionary<string, PathData>();

        private uint _nextPathID = 0;
        private List<Serializer> _keySerializerBuffer = new List<Serializer>();
        private List<string> _pathSegmentBuffer = new List<string>();

        public PathIDManifest()
        {
            var root = new T();
            root.Initialize(new ObserveThing.ObservationContext(), new FofX.DefaultLogger() { logLevel = FofX.LogLevel.None });
            PopulatePathData(root, root);
        }

        private void PopulatePathData(IStateNode node, T relativeTo)
        {
            if (node.derived)
                return;

            if (!(node is StateObject) && node != relativeTo)
            {
                var pathData = PathDataFromState(node, relativeTo);
                _pathDataById.Add(pathData.id, pathData);
                _pathDataBySignature.Add(pathData.signature, pathData);
            }

            if (node is IStateList list)
            {
                var element = list.Add();
                PopulatePathData(element, relativeTo);
            }
            else if (node is IStateDictionary dict)
            {
                object key = null;

                if (dict.keyType.IsValueType)
                {
                    key = Activator.CreateInstance(dict.keyType);
                }
                else if (_defaultInstanceConstructors.TryGetValue(dict.keyType, out var constructor))
                {
                    key = constructor();
                }
                else
                {
                    key = Activator.CreateInstance(dict.keyType);
                }

                var element = dict.Add(key);
                PopulatePathData(element, relativeTo);
            }
            else
            {
                foreach (var child in node.children.OrderBy(x => x.nodeName))
                    PopulatePathData(child, relativeTo);
            }
        }

        private PathData PathDataFromState(IStateNode state, T relativeTo)
        {
            var id = _nextPathID;
            _nextPathID++;

            var currUpstream = state;

            while (currUpstream != relativeTo)
            {
                if (currUpstream.parent != null)
                {
                    if (currUpstream.parent is IStateList)
                    {
                        _keySerializerBuffer.Add(PhotonSerialization.GetSerializer(typeof(int)));
                        _pathSegmentBuffer.Add("*");
                        currUpstream = currUpstream.parent;
                        continue;
                    }
                    else if (currUpstream.parent is IStateDictionary dictionary)
                    {
                        _keySerializerBuffer.Add(PhotonSerialization.GetSerializer(dictionary.keyType));
                        _pathSegmentBuffer.Add("*");
                        currUpstream = currUpstream.parent;
                        continue;
                    }
                }

                _pathSegmentBuffer.Add(currUpstream.nodeName);
                currUpstream = currUpstream.parent;
            }

            _keySerializerBuffer.Reverse();
            _pathSegmentBuffer.Reverse();

            var result = new PathData(id, string.Join("/", _pathSegmentBuffer), _keySerializerBuffer.ToArray());

            _pathSegmentBuffer.Clear();
            _keySerializerBuffer.Clear();

            return result;
        }

        public PathData GetPathData(uint id)
            => _pathDataById[id];

        public PathData GetPathData(string pathSignature)
            => _pathDataBySignature[pathSignature];

        public bool TryGetPathData(uint id, out PathData pathData)
            => _pathDataById.TryGetValue(id, out pathData);

        public bool TryGetPathData(string pathSignature, out PathData pathData)
            => _pathDataBySignature.TryGetValue(pathSignature, out pathData);

        public static string GetPathSignature(IStateNode node, T relativeTo)
        {
            var currUpstream = node;

            try
            {
                while (currUpstream != relativeTo)
                {
                    if (currUpstream.parent is IStateList || currUpstream.parent is IStateDictionary)
                    {
                        _signatureBuilder.Add("*");
                    }
                    else
                    {
                        _signatureBuilder.Add(currUpstream.nodeName);
                    }

                    currUpstream = currUpstream.parent;
                }

                _signatureBuilder.Reverse();
                var result = string.Join("/", _signatureBuilder);
                return result;
            }
            finally
            {
                _signatureBuilder.Clear();
            }
        }
    }
}