using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace FofX.Stateful
{
    public class ObservableNodeContext : IObservableNodeContext
    {
        private static readonly int MAX_DELAYED_ACTION_DEPTH = 20;

        public bool executingActions { get; private set; }
        public bool notifyingObservers { get; private set; }
        public bool notifyingDerivedObservers { get; private set; }

        private ConcurrentQueue<IActionSet> _scheduledActions = new ConcurrentQueue<IActionSet>();

        private List<IActionSet> _delayedActions;
        private List<IActionSet> _delayedActions1 = new List<IActionSet>();
        private List<IActionSet> _delayedActions2 = new List<IActionSet>();

        private Dictionary<IObservableNode, List<ObserverData>> _observedNodes = new Dictionary<IObservableNode, List<ObserverData>>();
        private Dictionary<ObserverDelegate, ObserverData> _observersByMethod = new Dictionary<ObserverDelegate, ObserverData>();

        private ObservationFrame _observationFrame;
        private ObservationFrame _observationFrame1 = new ObservationFrame();
        private ObservationFrame _observationFrame2 = new ObservationFrame();

        private class ObservationFrame
        {
            public HashSet<ObserverData> pendingObservers = new HashSet<ObserverData>();
            public List<NodeChangeData> observedChanges = new List<NodeChangeData>();
            public HashSet<ObserverData> observersToDispose = new HashSet<ObserverData>();

            public void Reset()
            {
                pendingObservers.Clear();
                observedChanges.Clear();
                observersToDispose.Clear();
            }
        }

        private NodeChangeEventArgs _initArgs = new NodeChangeEventArgs() { initialize = true };
        private Queue<List<ObserverData>> _observerListPool = new Queue<List<ObserverData>>();
        private Queue<NodeChangeEventArgs> _eventArgsPool = new Queue<NodeChangeEventArgs>();
        private Queue<NodeChangeData> _nodeChangeDataPool = new Queue<NodeChangeData>();
        private Queue<List<NodeChangeData>> _changeListPool = new Queue<List<NodeChangeData>>();
        private Dictionary<Type, Queue<IActionSet>> _actionSetPools = new Dictionary<Type, Queue<IActionSet>>();

        private int _nextObserverPriority = 0;

        private Thread _mainThread;
        public ILogger logger { get; private set; }

        private class ObserverData
        {
            public ObserverDelegate method;
            public ObserverParameters parameters;
            public HashSet<IObservableNode> nodes = new HashSet<IObservableNode>();
            public int priority;

            public List<NodeChangeData> pendingChanges = new List<NodeChangeData>();
            public bool disposed;
        }

        public interface IActionSet
        {
            Type nodeType { get; }
            LogLevel logLevel { get; }
            public Action postObserverCallback { get; set; }
            void Execute();
            void Reset();
        }

        public class ActionSet<T> : IActionSet where T : IObservableNode
        {
            public Type nodeType => typeof(T);
            public T node;
            public LogLevel logLevel { get; set; }
            public Action postObserverCallback { get; set; }
            public ObservableNodeAction<T>[] actions;

            public void Execute()
            {
                foreach (var action in actions)
                    action.Execute(node);
            }

            public void Reset()
            {
                node = default;
                logLevel = default;
                postObserverCallback = default;
                actions = default;
            }

            public override string ToString()
            {
                return $"ActionSet<{typeof(T).Name}>[target={node?.nodePath ?? "NULL"} actions={string.Join(",", actions.Select(x => x.ToString()))}]";
            }
        }

        public ObservableNodeContext(ILogger logger)
        {
            _mainThread = Thread.CurrentThread;
            _delayedActions = _delayedActions1;
            _observationFrame = _observationFrame1;
            this.logger = logger;
        }

        private void ExecuteActions(IActionSet actions, bool delayIfNecessary, bool executeDelayedActions)
        {
            if (Thread.CurrentThread != _mainThread)
            {
                var exc = new Exception($"Cannot execute actions while not on the main thread.");
                logger.Error(exc);
                throw exc;
            }

            if (executingActions)
            {
                var exc = new Exception($"Cannot execute actions while already executing actions. Consider using {nameof(ExecuteActionOrDelay)} instead.");
                logger.Error(exc);
                throw exc;
            }

            if (notifyingObservers)
            {
                if (delayIfNecessary)
                {
                    if (logger.LevelEnabled(actions.logLevel))
                        logger.Generic(actions.logLevel, $"Delaying Actions: {actions}");

                    _delayedActions.Add(actions);
                    return;
                }
                else
                {
                    var exc = new Exception($"Cannot execute actions while notifying observers. Consider setting {nameof(delayIfNecessary)} to true.");
                    logger.Error(exc);
                    throw exc;
                }
            }

            try
            {
                executingActions = true;

                if (logger.LevelEnabled(actions.logLevel))
                    logger.Generic(actions.logLevel, $"Executing {actions}");

                actions.Execute();
            }
            catch (Exception exc)
            {
                logger.Error("Encountered an error while executing actions", exc);
            }
            finally
            {
                executingActions = false;
            }

            try
            {
                NotifyObserversAndReset(actions.logLevel);
            }
            catch (Exception exc)
            {
                logger.Error($"Encountered an error while notifying observers", exc);
            }

            actions.postObserverCallback?.Invoke();
            DeallocateActionSet(actions);

            if (executeDelayedActions)
                ExecuteDelayedActions();
        }

        private void ExecuteDelayedActions()
        {
            int delayedActionDepth = 0;

            while (_delayedActions.Count != 0 && delayedActionDepth < MAX_DELAYED_ACTION_DEPTH)
            {
                var toExecute = _delayedActions;
                _delayedActions = toExecute == _delayedActions1 ? _delayedActions2 : _delayedActions1;

                foreach (IActionSet action in toExecute)
                    ExecuteActions(action, false, false);

                toExecute.Clear();
                delayedActionDepth++;
            }
        }

        private void NotifyObserversAndReset(LogLevel logLevel)
        {
            var currentFrame = _observationFrame;
            _observationFrame = currentFrame == _observationFrame1 ? _observationFrame2 : _observationFrame1;

            if (logger.LevelEnabled(logLevel))
            {
                if (currentFrame.observedChanges.Count > 0)
                    logger.Generic(logLevel, $"Observed changes:\n{string.Join("\n", currentFrame.observedChanges.Select(x => $"    {x}"))}");

                if (currentFrame.pendingObservers.Where(x => !x.disposed).Count() > 0)
                    logger.Generic(logLevel, $"Notifying Observers:\n{string.Join("\n", currentFrame.pendingObservers.Where(x => !x.disposed).OrderBy(x => x.priority).Select(x => $"    - {x.method.Method.DeclaringType.Name}.{x.method.Method.Name}"))}");
            }

            var eventArgs = AllocateEventArgs(false, null);

            notifyingObservers = true;

            foreach (ObserverData observer in currentFrame.pendingObservers.OrderBy(x => x.priority))
            {
                if (observer.disposed)
                    continue;

                try
                {
                    eventArgs.changes = observer.pendingChanges;
                    observer.method.Invoke(eventArgs);
                }
                catch (Exception exc)
                {
                    logger.Error("Encountered an error while notifying observers", exc);
                }

                observer.pendingChanges.Clear();
            }

            notifyingObservers = false;

            DeallocateEventArgs(eventArgs);

            foreach (var change in currentFrame.observedChanges)
                DeallocateChangeData(change);

            foreach (ObserverData observer in currentFrame.observersToDispose)
                DisposeObserver(observer);

            currentFrame.Reset();

            if (_observationFrame.observedChanges.Count > 0)
                NotifyObserversAndReset(logLevel);
        }

        private void DisposeObserver(ObserverData observer)
        {
            _observersByMethod.Remove(observer.method);

            foreach (IObservableNode node in observer.nodes)
                RemoveObserverRecursive(observer, observer.parameters.scope, node);

            observer.disposed = true;
        }

        private void AddObserverRecursive(ObserverData observerData, ObservationScope scope, IObservableNode node)
        {
            if (!_observedNodes.TryGetValue(node, out var observers))
            {
                observers = new List<ObserverData>();
                _observedNodes.Add(node, observers);
            }

            bool observerInserted = false;

            for (int i = 0; i < observers.Count; i++)
            {
                if (observers[i].priority > observerData.priority)
                {
                    observers.Insert(i, observerData);
                    observerInserted = true;
                    break;
                }
            }

            if (!observerInserted)
                observers.Add(observerData);

            if (scope == ObservationScope.Self)
                return;

            scope = scope == ObservationScope.Children ? ObservationScope.Self : ObservationScope.All;

            foreach (var child in node.children)
                AddObserverRecursive(observerData, scope, child);
        }

        private void RemoveObserverRecursive(ObserverData observer, ObservationScope scope, IObservableNode node)
        {
            var observers = _observedNodes[node];
            observers.Remove(observer);

            if (observers.Count == 0)
                _observedNodes.Remove(node);

            if (scope == ObservationScope.Self)
                return;

            scope = scope == ObservationScope.Children ? ObservationScope.Self : ObservationScope.All;

            foreach (var child in node.children)
                RemoveObserverRecursive(observer, scope, child);
        }

        private NodeChangeData AllocateChangeData(IObservableNode source, ChangeType changeType, object currentValue, object previousValue, int? index, object key, IObservableNode child, object collectionElement)
        {
            NodeChangeData nodeChangeData = _nodeChangeDataPool.Count > 0 ? _nodeChangeDataPool.Dequeue() : new NodeChangeData();

            nodeChangeData.source = source;
            nodeChangeData.changeType = changeType;
            nodeChangeData.currentValue = currentValue;
            nodeChangeData.previousValue = previousValue;
            nodeChangeData.index = index;
            nodeChangeData.key = key;
            nodeChangeData.child = child;
            nodeChangeData.collectionElement = collectionElement;

            return nodeChangeData;
        }

        private void DeallocateChangeData(NodeChangeData changeData)
        {
            changeData.source = default;
            changeData.changeType = default;
            changeData.currentValue = default;
            changeData.previousValue = default;
            changeData.index = default;
            changeData.key = default;
            changeData.child = default;
            changeData.collectionElement = default;
            _nodeChangeDataPool.Enqueue(changeData);
        }

        private NodeChangeEventArgs AllocateEventArgs(bool initialize, List<NodeChangeData> changeList)
        {
            NodeChangeEventArgs eventArgs = _eventArgsPool.Count > 0 ? _eventArgsPool.Dequeue() : new NodeChangeEventArgs();

            eventArgs.initialize = initialize;
            eventArgs.changes = changeList;

            return eventArgs;
        }

        private void DeallocateEventArgs(NodeChangeEventArgs eventArgs)
        {
            eventArgs.initialize = default;
            eventArgs.changes = default;
            _eventArgsPool.Enqueue(eventArgs);
        }

        private List<ObserverData> AllocateObserverList(IEnumerable<ObserverData> observers)
        {
            var list = _observerListPool.Count > 0 ? _observerListPool.Dequeue() : new List<ObserverData>();
            list.AddRange(observers);
            return list;
        }

        private void DeallocateObserverList(List<ObserverData> list)
        {
            list.Clear();
            _observerListPool.Enqueue(list);
        }

        private List<NodeChangeData> AllocateChangeList()
            => _changeListPool.Count > 0 ? _changeListPool.Dequeue() : new List<NodeChangeData>();

        private void DeallocateChangeList(List<NodeChangeData> list)
        {
            if (list.Count > 0)
                list.Clear();

            _changeListPool.Enqueue(list);
        }

        private ActionSet<T> AllocateActionSet<T>(T node, LogLevel logLevel, Action postObserverCallback, ObservableNodeAction<T>[] actions)
            where T : IObservableNode
        {
            if (!_actionSetPools.TryGetValue(typeof(T), out var pool))
            {
                pool = new Queue<IActionSet>();
                _actionSetPools.Add(typeof(T), pool);
            }

            var set = pool.Count > 0 ? (ActionSet<T>)pool.Dequeue() : new ActionSet<T>();
            set.node = node;
            set.logLevel = logLevel;
            set.postObserverCallback = postObserverCallback;
            set.actions = actions;

            return set;
        }

        private void DeallocateActionSet(IActionSet set)
        {
            set.Reset();
            _actionSetPools[set.nodeType].Enqueue(set);
        }

        public void RegisterNodeChange(IObservableNode source, ChangeType changeType,
            object currentValue = default, object previousValue = default,
            int? index = default, object key = default, IObservableNode child = default, object collectionElement = default)
        {
            if (!source.isDerived && !executingActions)
                throw new Exception("Cannot edit nodes outside of actions.");

            if (source.isDerived && !notifyingDerivedObservers && changeType != ChangeType.Dispose)
                throw new Exception("Derived nodes cannot be edited directly.");

            if (changeType == ChangeType.Add &&
                child != null &&
                _observedNodes.TryGetValue(source, out var observersToInherit))
            {
                foreach (var observer in observersToInherit)
                {
                    if (observer.parameters.scope == ObservationScope.Self)
                        continue;

                    if (observer.parameters.scope == ObservationScope.All)
                    {
                        AddObserverRecursive(observer, ObservationScope.All, child);
                        continue;
                    }

                    if (observer.parameters.scope == ObservationScope.Children && observer.nodes.Contains(source))
                    {
                        AddObserverRecursive(observer, ObservationScope.Self, child);
                        continue;
                    }
                }
            }

            var changeData = AllocateChangeData(source, changeType, currentValue, previousValue, index, key, child, collectionElement);

            _observationFrame.observedChanges.Add(changeData);

            if (!_observedNodes.TryGetValue(source, out var observers))
                return;

            bool wasNotifyingDerivedObservers = notifyingDerivedObservers;
            notifyingDerivedObservers = true;

            var eventArgs = AllocateEventArgs(false, AllocateChangeList());
            eventArgs.changes.Add(changeData);

            var observerBuffer = AllocateObserverList(observers);

            foreach (var observer in observerBuffer)
            {
                if (observer.disposed)
                    continue;

                if (observer.pendingChanges.Count != 0 &&
                    observer.pendingChanges[observer.pendingChanges.Count - 1] == changeData)
                {
                    continue;
                }

                if (observer.parameters.isDerived)
                {
                    try
                    {
                        observer.method.Invoke(eventArgs);
                    }
                    catch (Exception exc)
                    {
                        logger.Error(exc);
                    }

                    continue;
                }

                observer.pendingChanges.Add(changeData);
                _observationFrame.pendingObservers.Add(observer);
            }

            DeallocateChangeList(eventArgs.changes);
            DeallocateEventArgs(eventArgs);
            DeallocateObserverList(observerBuffer);

            notifyingDerivedObservers = wasNotifyingDerivedObservers;

            // if this node was disposed, clean up observers that no longer have target nodes
            if (changeType == ChangeType.Dispose)
            {
                _observedNodes.Remove(source);

                foreach (var observer in observers)
                {
                    observer.nodes.Remove(source);
                    if (observer.nodes.Count == 0)
                    {
                        _observationFrame.pendingObservers.Remove(observer);
                        _observationFrame.observersToDispose.Add(observer); //wait to remove this observer so that client-code DeregisterObserver calls can take precedence
                    }
                }
            }
        }

        public void RegisterObserver(ObserverDelegate observer, ObserverParameters parameters, params IObservableNode[] nodes)
        {
            if (_observersByMethod.ContainsKey(observer))
                throw new Exception("Observers can only be registered once.");

            ObserverData observerData = new ObserverData()
            {
                method = observer,
                parameters = parameters,
                priority = _nextObserverPriority
            };

            _nextObserverPriority++;

            _observersByMethod.Add(observer, observerData);

            foreach (IObservableNode node in nodes)
            {
                observerData.nodes.Add(node);
                AddObserverRecursive(observerData, observerData.parameters.scope, node);
            }

            bool wasNotifyingDerivedObservers = notifyingDerivedObservers;
            notifyingDerivedObservers = true;
            observer.Invoke(_initArgs);
            notifyingDerivedObservers = wasNotifyingDerivedObservers;
        }

        public void DeregisterObserver(ObserverDelegate observer)
        {
            if (_observersByMethod.TryGetValue(observer, out var observerData))
                DisposeObserver(observerData);
        }

        public void ExecuteAction<T>(T node, LogLevel logLevel = LogLevel.Debug, Action postObserverCallback = null, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteActions(AllocateActionSet(node, logLevel, postObserverCallback, actions), false, true);

        public void ExecuteActionOrDelay<T>(T node, LogLevel logLevel = LogLevel.Debug, Action postObserverCallback = null, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteActions(AllocateActionSet(node, logLevel, postObserverCallback, actions), true, true);

        public void ScheduleAction<T>(T node, LogLevel logLevel = LogLevel.Debug, Action postObserverCallback = null, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => _scheduledActions.Enqueue(AllocateActionSet(node, logLevel, postObserverCallback, actions));

        public void ExecuteScheduledActions()
        {
            while (_scheduledActions.TryDequeue(out var scheduledActionSet))
                ExecuteActions(scheduledActionSet, false, true);
        }
    }

    public enum ObservationScope
    {
        All,
        Children,
        Self
    }

    public interface IObservableNodeContext
    {
        bool executingActions { get; }
        bool notifyingObservers { get; }
        ILogger logger { get; }

        void ExecuteScheduledActions();

        void ExecuteAction<T>(T node, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteAction(node, LogLevel.Debug, null, actions);

        void ExecuteAction<T>(T node, LogLevel logLevel, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteAction(node, logLevel, null, actions);

        void ExecuteAction<T>(T node, Action postObserverCallback, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteAction(node, LogLevel.Debug, postObserverCallback, actions);

        void ExecuteAction<T>(T node, LogLevel logLevel = LogLevel.Debug, Action postObserverCallback = null, params ObservableNodeAction<T>[] actions) where T : IObservableNode;


        void ExecuteActionOrDelay<T>(T node, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteActionOrDelay(node, LogLevel.Debug, null, actions);

        void ExecuteActionOrDelay<T>(T node, LogLevel logLevel, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteActionOrDelay(node, logLevel, null, actions);

        void ExecuteActionOrDelay<T>(T node, Action postObserverCallback, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ExecuteActionOrDelay(node, LogLevel.Debug, postObserverCallback, actions);

        void ExecuteActionOrDelay<T>(T node, LogLevel logLevel = LogLevel.Debug, Action postObserverCallback = null, params ObservableNodeAction<T>[] actions) where T : IObservableNode;


        void ScheduleAction<T>(T node, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ScheduleAction(node, LogLevel.Debug, null, actions);

        void ScheduleAction<T>(T node, LogLevel logLevel, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ScheduleAction(node, logLevel, null, actions);

        void ScheduleAction<T>(T node, Action postObserverCallback, params ObservableNodeAction<T>[] actions) where T : IObservableNode
            => ScheduleAction(node, LogLevel.Debug, postObserverCallback, actions);

        void ScheduleAction<T>(T node, LogLevel logLevel = LogLevel.Debug, Action postObserverCallback = null, params ObservableNodeAction<T>[] actions) where T : IObservableNode;

        void RegisterNodeChange(IObservableNode source, ChangeType changeType, object currentValue = default, object previousValue = default, int? index = default, object key = default, IObservableNode child = default, object collectionElement = default);

        void RegisterObserver(ObserverDelegate observer, params IObservableNode[] nodes)
            => RegisterObserver(observer, default, nodes);

        void RegisterObserver(ObserverDelegate observer, ObserverParameters parameters, params IObservableNode[] nodes);

        void DeregisterObserver(ObserverDelegate observer);
    }

    public struct ObserverParameters
    {
        public ObservationScope scope;
        public bool isDerived;
    }

    public class NodeChangeEventArgs
    {
        public bool initialize;
        public List<NodeChangeData> changes;
    }

    public delegate void ObserverDelegate(NodeChangeEventArgs args);

    public enum ChangeType
    {
        None,
        Set,
        Add,
        Remove,
        Dispose
    }
}
