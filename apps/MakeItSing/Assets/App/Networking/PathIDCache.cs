using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FofX.Stateful;

namespace Plerion.MakeItSing
{
    public class PathIDCache<T> where T : class, IStateNode, new()
    {
        private PathIDManifest<T> _pathManifest;
        private Dictionary<string, string> _pathToSignatureCache = new Dictionary<string, string>();
        private Dictionary<int, IStateNode> _resultCache = new Dictionary<int, IStateNode>();
        private List<object> _keyBuffer = new List<object>();

        public PathIDCache()
        {
            _pathManifest = new PathIDManifest<T>();
        }

        public void WritePath(IStateNode state, T relativeTo, BinaryWriter writer)
        {
            if (!_pathToSignatureCache.TryGetValue(state.nodePath, out var signature))
            {
                signature = PathIDManifest<T>.GetPathSignature(state, relativeTo);
                _pathToSignatureCache.Add(state.nodePath, signature);
            }

            var data = _pathManifest.GetPathData(signature);
            writer.Write(data.id);

            try
            {
                var currUpstream = state;

                while (currUpstream != null)
                {
                    if (currUpstream.parent == null)
                        break;

                    if (currUpstream.parent is IStateDictionary dict)
                    {
                        var key = dict.GetKey(currUpstream);
                        _keyBuffer.Add(key);
                    }
                    else if (currUpstream.parent is IStateList list)
                    {
                        var index = list.IndexOf(currUpstream);
                        _keyBuffer.Add(index);
                    }

                    currUpstream = currUpstream.parent;
                }

                for (int i = 0; i < _keyBuffer.Count; i++)
                {
                    // reverse keybuffer order because we wrote it backwards
                    data.keySerializers[i].Serialize(writer, _keyBuffer[_keyBuffer.Count - (i + 1)], false);
                }
            }
            finally
            {
                _keyBuffer.Clear();
            }
        }

        public bool TryReadPath(T root, BinaryReader reader, out IStateNode result)
        {
            var pathID = reader.ReadUInt32();

            if (!_pathManifest.TryGetPathData(pathID, out var data))
            {
                result = default;
                return false;
            }

            var currDownstream = (IStateNode)root;

            _keyBuffer.Add(pathID);
            _keyBuffer.AddRange(data.keySerializers.Select(x => x.Deserialize(reader, false)));

            var hash = new HashCode();

            foreach (var key in _keyBuffer)
                hash.Add(key);

            var hashValue = hash.ToHashCode();

            if (_resultCache.TryGetValue(hashValue, out var cachedResult))
            {
                if (cachedResult.disposed)
                {
                    _resultCache.Remove(hashValue);
                }
                else
                {
                    _keyBuffer.Clear();
                    result = cachedResult;
                    return true;
                }
            }

            try
            {
                int keyIndex = 1; //skip the ID we added for hashing

                for (int i = 0; i < data.pathSegments.Length; i++) // start at index 1 to skip root
                {
                    var nextNodeName = data.pathSegments[i];
                    if (nextNodeName != "*")
                    {
                        if (currDownstream.TryFindChild(nextNodeName, out var child))
                        {
                            currDownstream = child;
                            continue;
                        }
                        else
                        {
                            result = default;
                            return false;
                        }
                    }

                    var key = _keyBuffer[keyIndex];
                    keyIndex++;

                    if (currDownstream is IStateDictionary dict)
                    {
                        if (dict.TryGetValue(key, out var value))
                        {
                            currDownstream = value;
                        }
                        else
                        {
                            result = default;
                            return false;
                        }
                    }
                    else if (currDownstream is IStateList list)
                    {
                        var index = (int)key;
                        if (index > 0 && list.Count > index)
                        {
                            currDownstream = list[index];
                        }
                        else
                        {
                            result = default;
                            return false;
                        }
                    }
                    else
                    {
                        throw new Exception($"Attempted to use key type {data.keySerializers[i].type} with state type {currDownstream.GetType().Name}");
                    }
                }

                _resultCache.Add(hashValue, currDownstream);
                result = currDownstream;
                return true;
            }
            finally
            {
                _keyBuffer.Clear();
            }
        }

        public IStateNode ReadPath(T root, BinaryReader reader)
        {
            var pathID = reader.ReadUInt32();
            var data = _pathManifest.GetPathData(pathID);

            var currDownstream = (IStateNode)root;

            _keyBuffer.Add(pathID);
            _keyBuffer.AddRange(data.keySerializers.Select(x => x.Deserialize(reader, false)));

            var hash = new HashCode();

            foreach (var key in _keyBuffer)
                hash.Add(key);

            var hashValue = hash.ToHashCode();

            if (_resultCache.TryGetValue(hashValue, out var cachedResult))
            {
                if (cachedResult.disposed)
                {
                    _resultCache.Remove(hashValue);
                }
                else
                {
                    _keyBuffer.Clear();
                    return cachedResult;
                }
            }

            try
            {
                int keyIndex = 1; //skip ID we added for hashing purposes

                for (int i = 0; i < data.pathSegments.Length; i++) // start at index 1 to skip root
                {
                    var nextNodeName = data.pathSegments[i];
                    if (nextNodeName != "*")
                    {
                        currDownstream = currDownstream.GetChild(nextNodeName);
                        continue;
                    }

                    var key = _keyBuffer[keyIndex];
                    keyIndex++;

                    if (currDownstream is IStateDictionary dict)
                    {
                        currDownstream = dict[key];
                    }
                    else if (currDownstream is IStateList list)
                    {
                        currDownstream = list[(int)key];
                    }
                    else
                    {
                        throw new Exception($"Attempted to use key type {data.keySerializers[i].type} with state type {currDownstream.GetType().Name}");
                    }
                }

                _resultCache.Add(hashValue, currDownstream);
                return currDownstream;
            }
            finally
            {
                _keyBuffer.Clear();
            }
        }

        public void ClearCaches()
        {
            _resultCache.Clear();
            _pathToSignatureCache.Clear();
        }
    }
}