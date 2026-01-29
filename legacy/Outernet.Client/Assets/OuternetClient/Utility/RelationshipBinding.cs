using System;
using System.Collections.Generic;
using System.Linq;
using FofX.Stateful;

namespace Outernet.Client
{
    public class RelationshipBinding : IDisposable
    {
        private static Queue<NodeChangeEventArgs> _nodeChangeEventArgsPool = new Queue<NodeChangeEventArgs>();
        private static Queue<NodeChangeData> _nodeChangeDataPool = new Queue<NodeChangeData>();

        private IObservableNodeContext _context;

        private ObserverDelegate _observer1;
        private ObserverDelegate _observer2;

        private bool _applyingChangesToNodes1 => _pendingActions1.Count > 0;
        private bool _applyingChangesToNodes2 => _pendingActions2.Count > 0;

        private HashSet<ApplyChangesAction> _pendingActions1 = new HashSet<ApplyChangesAction>();
        private HashSet<ApplyChangesAction> _pendingActions2 = new HashSet<ApplyChangesAction>();

        public RelationshipBinding(
            IObservableNodeContext context,
            ObserverDelegate observer1, ObservationScope scope1, IObservableNode[] nodes1,
            ObserverDelegate observer2, ObservationScope scope2, IObservableNode[] nodes2
        )
        {
            _context = context;

            _observer1 = observer1;
            _observer2 = observer2;

            context.RegisterObserver(HandleNodes1Changed, new ObserverParameters() { scope = scope1 }, nodes1);
            context.RegisterObserver(HandleNodes2Changed, new ObserverParameters() { scope = scope2 }, nodes2);
        }

        public void Dispose()
        {
            _context.DeregisterObserver(HandleNodes1Changed);
            _context.DeregisterObserver(HandleNodes2Changed);
        }

        private void HandleNodes1Changed(NodeChangeEventArgs args)
        {
            if (_applyingChangesToNodes1)
                return;

            var argsCopy = AllocateCopy(args);
            var action = new ApplyChangesAction(_observer1, argsCopy);
            _pendingActions2.Add(action);
            _context.ExecuteActionOrDelay(
                node: null,
                logLevel: FofX.LogLevel.Trace,
                postObserverCallback: () =>
                {
                    _pendingActions2.Remove(action);
                    DeallocateCopy(argsCopy);
                },
                actions: action
            );
        }

        private void HandleNodes2Changed(NodeChangeEventArgs args)
        {
            if (_applyingChangesToNodes2)
                return;

            var argsCopy = AllocateCopy(args);
            var action = new ApplyChangesAction(_observer2, argsCopy);
            _pendingActions1.Add(action);
            _context.ExecuteActionOrDelay(
                node: null,
                logLevel: FofX.LogLevel.Trace,
                postObserverCallback: () =>
                {
                    _pendingActions1.Remove(action);
                    DeallocateCopy(argsCopy);
                },
                actions: action
            );
        }

        private static NodeChangeEventArgs AllocateCopy(NodeChangeEventArgs toCopy)
        {
            var copy = _nodeChangeEventArgsPool.Count > 0 ? _nodeChangeEventArgsPool.Dequeue() : new NodeChangeEventArgs() { changes = new List<NodeChangeData>() };
            copy.initialize = toCopy.initialize;

            if (toCopy.changes != null && toCopy.changes.Count > 0)
            {
                copy.changes.AddRange(toCopy.changes.Select(x =>
                {
                    var changeCopy = _nodeChangeDataPool.Count > 0 ? _nodeChangeDataPool.Dequeue() : new NodeChangeData();
                    changeCopy.source = x.source;
                    changeCopy.changeType = x.changeType;
                    changeCopy.currentValue = x.currentValue;
                    changeCopy.previousValue = x.previousValue;
                    changeCopy.index = x.index;
                    changeCopy.key = x.key;
                    changeCopy.child = x.child;
                    changeCopy.collectionElement = x.collectionElement;
                    return changeCopy;
                }));
            }

            return copy;
        }

        private static void DeallocateCopy(NodeChangeEventArgs copy)
        {
            foreach (var changeCopy in copy.changes)
            {
                changeCopy.source = default;
                changeCopy.changeType = default;
                changeCopy.currentValue = default;
                changeCopy.previousValue = default;
                changeCopy.index = default;
                changeCopy.key = default;
                changeCopy.child = default;
                changeCopy.collectionElement = default;
                _nodeChangeDataPool.Enqueue(changeCopy);
            }

            copy.changes.Clear();
            copy.initialize = default;
            _nodeChangeEventArgsPool.Enqueue(copy);
        }

        private class ApplyChangesAction : ObservableNodeAction<IObservableNode>
        {
            private ObserverDelegate _observer;
            private NodeChangeEventArgs _args;

            public ApplyChangesAction(ObserverDelegate observer, NodeChangeEventArgs args)
            {
                _observer = observer;
                _args = args;
            }

            public override void Execute(IObservableNode target)
            {
                _observer(_args);
            }
        }
    }
}