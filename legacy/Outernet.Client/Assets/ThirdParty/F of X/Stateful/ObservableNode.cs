using System;
using System.Collections.Generic;
using SimpleJSON;

namespace FofX.Stateful
{
    public interface IObservableNode
    {
        string nodeName { get; }
        string nodePath { get; }
        IObservableNode parent { get; }
        IObservableNodeContext context { get; }
        IObservableNode root { get; }
        IEnumerable<IObservableNode> children { get; }
        IEnumerable<Attribute> attributes { get; }
        bool initialized { get; }
        bool isDerived { get; }
        bool isDefault { get; }
        bool disposed { get; }
        void Initialize(string name, IObservableNode parent, params Attribute[] attributes);
        void Initialize(string name, IObservableNodeContext context, params Attribute[] attributes);
        void PostInitialize();
        void RegisterDerived(ObserverDelegate observer, ObservationScope scope, params IObservableNode[] sourceNodes);
        void DeregisterDerived();
        void SetDerived(bool derived);
        bool TryFindChild(string path, out IObservableNode child);
        IObservableNode GetChild(string path);
        void ApplyChange(NodeChangeData change);
        void CopyTo(IObservableNode copyTo);
        void Dispose();
        void Reset();
        void Rename(string newName);
        JSONNode ToJSON(Func<IObservableNode, bool> filter);
        void FromJSON(JSONNode json);
    }

    public class NodeChangeData
    {
        public IObservableNode source;
        public ChangeType changeType;
        public object currentValue;
        public object previousValue;
        public int? index;
        public object key;
        public IObservableNode child;
        public object collectionElement;

        public override string ToString()
            => $"[{string.Join(", ", EnumerateEvaluatedArgs())}]";

        private IEnumerable<string> EnumerateEvaluatedArgs()
        {
            yield return $"source={source?.nodePath}";
            yield return $"type={changeType}";

            if (currentValue != null)
                yield return $"currentValue={currentValue}";

            if (previousValue != null)
                yield return $"previousValue={previousValue}";

            if (index != null)
                yield return $"index={index}";

            if (key != null)
                yield return $"key={key}";

            if (child != null)
                yield return $"child={child.nodeName}";

            if (collectionElement != null)
                yield return $"collectionElement={collectionElement}";
        }
    }

    public abstract class ObservableNode : IObservableNode
    {
        public string nodeName { get; private set; }
        public string nodePath { get; private set; }
        public bool isRoot { get; private set; }

        public IObservableNode parent { get; private set; }
        public IObservableNode root { get; private set; }
        public IObservableNodeContext context { get; private set; }
        public IEnumerable<IObservableNode> children => _children.Values;
        public IEnumerable<Attribute> attributes => _attributes;

        public bool initialized { get; private set; }
        public bool isDerived { get; private set; }
        public bool disposed { get; private set; }
        public abstract bool isDefault { get; }

        private Dictionary<string, IObservableNode> _children = new Dictionary<string, IObservableNode>();
        private ObserverDelegate _deriveObserver;
        private Attribute[] _attributes;

        public ObservableNode() { }

        public void Initialize(string name, IObservableNodeContext context, params Attribute[] attributes)
        {
            if (context == null)
                throw new ArgumentNullException(nameof(context));

            if (initialized)
                throw new Exception($"{nodePath} has already been initialized");

            this.context = context;

            nodeName = name ?? "root";
            nodePath = nodeName;
            isRoot = true;
            root = this;

            _attributes = attributes;

            InitializeInternal();
            this.initialized = true;

            PostInitialize();
        }

        public void Initialize(string nodeName, IObservableNode parent, params Attribute[] attributes)
        {
            if (nodeName == null)
                throw new System.ArgumentNullException(nameof(nodeName));

            if (initialized)
                throw new Exception($"{nodePath} has already been initialized");

            this.parent = parent;
            this.context = parent.context;
            this.root = parent.root;
            this.nodeName = nodeName;
            this.isDerived = parent.isDerived;

            nodePath = $"{parent.nodePath}/{nodeName}";
            isRoot = false;

            _attributes = attributes;

            InitializeInternal();
            initialized = true;
        }

        public void PostInitialize()
        {
            PostInitializeInternal();

            foreach (var child in _children.Values)
                child.PostInitialize();
        }

        protected void AddChildInternal(string name, IObservableNode child, params Attribute[] attributes)
        {
            if (_children.ContainsKey(name))
                throw new Exception($"{nodePath} already contains a child named {name}");

            _children.Add(name, child);
            child.Initialize(name, this, attributes);

            // If we've already completed our initialization step, we need to post-initialize this new child
            if (initialized)
                child.PostInitialize();
        }

        protected void RemoveChildInternal(IObservableNode child)
        {
            if (_children.Remove(child.nodeName))
                child.Dispose();
        }

        protected void RenameChild(string previousName, string newName)
        {
            var child = _children[previousName];
            _children.Remove(previousName);
            _children.Add(newName, child);
            child.Rename(newName);
        }

        protected virtual void InitializeInternal() { }
        protected virtual void PostInitializeInternal() { }
        protected virtual void DisposeInternal() { }

        public void RegisterDerived(ObserverDelegate observer, ObservationScope scope, params IObservableNode[] sourceNodes)
        {
            if (_deriveObserver != null)
                throw new Exception($"{nodePath} already has a derive observer defined");

            _deriveObserver = observer;
            ((IObservableNode)this).SetDerived(true);
            context.RegisterObserver(observer, new ObserverParameters() { scope = scope, isDerived = true }, sourceNodes);
        }

        public void DeregisterDerived()
        {
            if (_deriveObserver == null)
                return;

            context.DeregisterObserver(_deriveObserver);
            _deriveObserver = null;

            if (!parent.isDerived)
                ((IObservableNode)this).SetDerived(false);
        }

        void IObservableNode.SetDerived(bool derived)
        {
            this.isDerived = derived;
            foreach (var child in children)
                child.SetDerived(derived);
        }

        public bool TryFindChild(string path, out IObservableNode child)
        {
            if (!path.Contains('/'))
                return _children.TryGetValue(path, out child);

            string[] pathSegments = path.Split('/', StringSplitOptions.RemoveEmptyEntries);
            IObservableNode currDownstream = this;

            for (int i = 0; i < pathSegments.Length; i++)
            {
                if (i == 0 && pathSegments[i] == nodeName)
                    continue;

                if (!currDownstream.TryFindChild(pathSegments[i], out currDownstream))
                {
                    child = default;
                    return false;
                }
            }

            child = currDownstream;
            return true;
        }

        public IObservableNode GetChild(string path)
        {
            if (string.IsNullOrEmpty(path))
                return this;

            if (!path.Contains('/'))
                return _children[path];

            string[] pathSegments = path.Split('/', StringSplitOptions.RemoveEmptyEntries);
            IObservableNode currDownstream = this;

            for (int i = 0; i < pathSegments.Length; i++)
            {
                if (i == 0 && isRoot && pathSegments[i] == nodeName)
                    continue;

                currDownstream = currDownstream.GetChild(pathSegments[i]);
            }

            return currDownstream;
        }

        public abstract void ApplyChange(NodeChangeData change);
        public abstract void CopyTo(IObservableNode copyTo);

        public void Dispose()
        {
            disposed = true;
            DisposeInternal();

            if (_deriveObserver != null)
                context.DeregisterObserver(_deriveObserver);

            foreach (IObservableNode child in children)
                child.Dispose();

            context.RegisterNodeChange(this, ChangeType.Dispose);
        }

        public abstract void Reset();

        void IObservableNode.Rename(string newName)
        {
            nodeName = newName;
            nodePath = parent == null ? newName : $"{parent.nodePath}/{newName}";
        }

        public abstract JSONNode ToJSON(Func<IObservableNode, bool> filter);
        public abstract void FromJSON(JSONNode json);
    }

    public interface IKeyedObservableNode<T> : IObservableNode
    {
        void AssignKey(T key);
    }
}
