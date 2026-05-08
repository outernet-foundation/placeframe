using System;
using System.Collections.Generic;
using System.Linq;
using ObserveThing;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public static class PlayerIdHelpers
    {
        public static PlayerIdHelper<SceneObjectId> SceneObjectIdHelper { get; private set; }
        public static PlayerIdHelper<HighFrequencyPrimitiveId> HighFrequencyPathIdHelper { get; private set; }

        private static IEnumerable<int> EnumeratePlayerIds(int startAt)
        {
            var playerId = Mathf.FloorToInt(startAt / 10000);
            var offset = playerId * 10000;
            var startId = startAt - offset;

            for (int i = startId; i < 10000; i++)
                yield return offset + i;

            for (int i = 0; i < startId; i++)
                yield return offset + i;
        }

        public static void Setup(int playerId, ICollectionObservable<SceneObjectId> sceneObjectIds, ICollectionObservable<HighFrequencyPrimitiveId> highFrequencyPathIds)
        {
            SceneObjectIdHelper = new PlayerIdHelper<SceneObjectId>(
                sceneObjectIds,
                new SceneObjectId(playerId * 10000),
                x => EnumeratePlayerIds(x.value).Select(x => new SceneObjectId(x))
            );

            HighFrequencyPathIdHelper = new PlayerIdHelper<HighFrequencyPrimitiveId>(
                highFrequencyPathIds,
                new HighFrequencyPrimitiveId(playerId * 10000),
                x => EnumeratePlayerIds(x.value).Select(x => new HighFrequencyPrimitiveId(x))
            );
        }

        public static void Reset()
        {
            SceneObjectIdHelper?.Dispose();
            HighFrequencyPathIdHelper?.Dispose();

            SceneObjectIdHelper = null;
            HighFrequencyPathIdHelper = null;
        }
    }

    public class PlayerIdHelper<T>
    {
        private IDisposable _activeIdsStream;
        private List<T> _activeIds = new List<T>();
        private HashSet<T> _pendingIds = new HashSet<T>();
        private Func<T, IEnumerable<T>> _getIdEnumerator;
        private T _nextId;

        public PlayerIdHelper(ICollectionObservable<T> activeIds, T firstId, Func<T, IEnumerable<T>> getIdEnumerator)
        {
            _nextId = firstId;
            _getIdEnumerator = getIdEnumerator;

            _activeIdsStream = activeIds.Subscribe(
                onAdd: x =>
                {
                    _activeIds.Add(x);
                    _pendingIds.Remove(x);
                },
                onRemove: x =>
                {
                    _activeIds.Remove(x);
                    _pendingIds.Remove(x);
                }
            );
        }

        public T AllocateID()
        {
            var enumerator = _getIdEnumerator(_nextId);
            var foundId = false;
            var result = default(T);

            foreach (var id in enumerator)
            {
                if (_pendingIds.Contains(id) || _activeIds.Contains(id))
                    continue;

                if (!foundId)
                {
                    //if we found a usable id, cache it and move to next
                    //so we have the nextId value for the next call
                    result = id;
                    foundId = true;
                    continue;
                }

                _nextId = id;
                break;
            }

            if (!foundId)
                throw new Exception("No more IDs available.");

            return result;
        }

        public void Dispose()
        {
            _pendingIds.Clear();
            _activeIdsStream.Dispose();
        }
    }
}