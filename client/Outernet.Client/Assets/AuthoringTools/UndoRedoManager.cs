using System.Collections.Generic;
using System.Linq;

using UnityEngine;

using FofX.Stateful;

namespace Outernet.Client.AuthoringTools
{
    public class UndoRedoManager : MonoBehaviour
    {
        private static Queue<NodeChangeData> _nodeChangeDataPool = new Queue<NodeChangeData>();

        private bool _hasUndo => _undos.Count != 0;
        private bool _hasRedo => _redos.Count != 0;

        private string _nextUndoDescription => _hasUndo ? _undos[_undos.Count - 1].description : null;
        private string _nextRedoDescription => _hasRedo ? _redos[0].description : null;

        private static bool _applyingUndoOrRedo = false;
        private static List<UndoData> _undos = new List<UndoData>();
        private static List<UndoData> _redos = new List<UndoData>();

        private class UndoData
        {
            public string description;
            public List<NodeChangeData> changes = new List<NodeChangeData>();
        }

        private void Awake()
        {
            SystemMenu.AddMenuItem(
                "Edit/Undo",
                Undo,
                getName: () => $"Undo {_nextUndoDescription}",
                validate: () => _hasUndo,
                commandKeys: new UnityEngine.InputSystem.Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    UnityEngine.InputSystem.Key.Z
                }
            );

            SystemMenu.AddMenuItem(
                "Edit/Redo",
                Redo,
                getName: () => $"Redo {_nextRedoDescription}",
                validate: () => _hasRedo,
                commandKeys: new UnityEngine.InputSystem.Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    UnityEngine.InputSystem.Key.LeftShift,
                    UnityEngine.InputSystem.Key.Z
                }
            );

            App.RegisterObserver(HandleContentLoadedChanged, App.state.authoringTools.locationContentLoaded);
            App.RegisterObserver(
                HandleAuthoringToolStateChanged,
                App.state.nodes,
                App.state.maps,
                App.state.transforms,
                App.state.authoringTools.selectedObjects
            );
        }

        private void HandleContentLoadedChanged(NodeChangeEventArgs args)
        {
            _undos.Clear();
        }

        private void HandleAuthoringToolStateChanged(NodeChangeEventArgs args)
        {
            if (args.initialize || _applyingUndoOrRedo)
                return;

            _redos.Clear();

            if (_undos.Count == 0)
                return;

            _undos[_undos.Count - 1].changes.AddRange(args.changes.Where(x => !x.source.isDerived).Select(x => AllocateCopy(x)));
        }

        public static void RegisterUndo(string description)
        {
            _undos.Add(new UndoData() { description = description });
        }

        public static void Undo()
        {
            if (_undos.Count == 0)
                return;

            var toUndo = _undos[_undos.Count - 1];
            _undos.RemoveAt(_undos.Count - 1);
            _redos.Insert(0, toUndo);

            _applyingUndoOrRedo = true;
            App.ExecuteAction(new UndoNodeChangesAction(toUndo.changes.ToArray()));
            _applyingUndoOrRedo = false;

            foreach (var change in toUndo.changes)
                DeallocateCopy(change);
        }

        public static void Redo()
        {
            if (_redos.Count == 0)
                return;

            var toRedo = _redos[0];
            _redos.RemoveAt(0);
            _undos.Add(toRedo);

            _applyingUndoOrRedo = true;
            App.ExecuteAction(new RedoNodeChangesAction(toRedo.changes.ToArray()));
            _applyingUndoOrRedo = false;
        }

        private static NodeChangeData AllocateCopy(NodeChangeData toCopy)
        {
            var copy = _nodeChangeDataPool.Count > 0 ? _nodeChangeDataPool.Dequeue() : new NodeChangeData();
            copy.source = toCopy.source;
            copy.changeType = toCopy.changeType;
            copy.currentValue = toCopy.currentValue;
            copy.previousValue = toCopy.previousValue;
            copy.index = toCopy.index;
            copy.key = toCopy.key;
            copy.child = toCopy.child;
            copy.collectionElement = toCopy.collectionElement;
            return copy;
        }

        private static void DeallocateCopy(NodeChangeData copy)
        {
            copy.source = default;
            copy.changeType = default;
            copy.currentValue = default;
            copy.previousValue = default;
            copy.index = default;
            copy.key = default;
            copy.child = default;
            copy.collectionElement = default;
            _nodeChangeDataPool.Enqueue(copy);
        }

        private class UndoNodeChangesAction : ObservableNodeAction<ClientState>
        {
            private NodeChangeData[] _toUndo;

            public UndoNodeChangesAction(NodeChangeData[] toUndo)
            {
                _toUndo = toUndo;
            }

            public override void Execute(ClientState target)
            {
                for (int i = _toUndo.Length - 1; i >= 0; i--)
                {
                    var change = _toUndo[i];

                    if (change.changeType == ChangeType.Dispose)
                        continue;

                    var targetState = target.GetChild(change.source.nodePath);

                    if (targetState.isDerived)
                        continue;

                    ApplyUndo(change, targetState);
                }
            }

            private void ApplyUndo(NodeChangeData change, IObservableNode target)
            {
                if (target is IObservablePrimitive prim)
                {
                    prim.SetValue(change.previousValue);
                }
                else if (target is IObservablePrimitiveArray array)
                {
                    array.SetValue(change.collectionElement);
                }
                else if (target is IObservableDictionary dict)
                {
                    if (change.changeType == ChangeType.Add)
                    {
                        dict.Remove(change.key);
                    }
                    else if (change.changeType == ChangeType.Remove)
                    {
                        change.child.CopyTo(dict.Add(change.key));
                    }
                }
                else if (target is IObservableList list)
                {
                    if (change.changeType == ChangeType.Add)
                    {
                        list.RemoveAt(change.index.Value);
                    }
                    else if (change.changeType == ChangeType.Remove)
                    {
                        change.child.CopyTo(list.Insert(change.index.Value));
                    }
                }
                else if (target is IObservableSet set)
                {
                    if (change.changeType == ChangeType.Add)
                    {
                        set.Remove(change.collectionElement);
                    }
                    else if (change.changeType == ChangeType.Remove)
                    {
                        set.Add(change.collectionElement);
                    }
                }
                else if (target is IObservablePrimitiveMap map)
                {
                    if (change.changeType == ChangeType.Add)
                    {
                        map.Remove(change.collectionElement);
                    }
                    else if (change.changeType == ChangeType.Remove)
                    {
                        map.Add(change.collectionElement);
                    }
                }
                else
                {
                    throw new System.Exception($"Unhandled undo target {target.GetType().Name}");
                }
            }
        }

        private class RedoNodeChangesAction : ObservableNodeAction<ClientState>
        {
            private NodeChangeData[] _toRedo;

            public RedoNodeChangesAction(NodeChangeData[] toRedo)
            {
                _toRedo = toRedo;
            }

            public override void Execute(ClientState target)
            {
                for (int i = 0; i < _toRedo.Length; i++)
                {
                    var change = _toRedo[i];

                    if (change.changeType == ChangeType.Dispose)
                        continue;

                    target.GetChild(change.source.nodePath).ApplyChange(change);
                }
            }
        }
    }
}