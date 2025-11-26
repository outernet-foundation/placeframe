
using System;
using System.Linq;
using System.Reflection;
using SimpleJSON;

namespace FofX.Stateful
{
    public class ObservableObject : ObservableNode
    {
        public override bool isDefault =>
            children.All(x => x.isDefault);

        protected override void InitializeInternal()
        {
            var type = GetType();
            while (type != typeof(ObservableObject))
            {
                // certain platforms require that binding flags be set explicitly, or all inherited
                // properties will be returned with each type up the inheritance chain
                var properties = type
                    .GetProperties(BindingFlags.DeclaredOnly | BindingFlags.Instance | BindingFlags.Public)
                    .Where(x => x.SetMethod != null &&
                        typeof(IObservableNode).IsAssignableFrom(x.PropertyType) &&
                        x.Name != nameof(parent) &&
                        x.Name != nameof(root)
                    );

                foreach (var property in properties)
                {
                    ObservableNode state = (ObservableNode)(property.GetValue(this) ?? Activator.CreateInstance(property.PropertyType));
                    property.SetValue(this, state);
                    AddChildInternal(property.Name, state, property.GetCustomAttributes().ToArray());
                }

                type = type.BaseType;
            }
        }

        public override void ApplyChange(NodeChangeData change)
        {
            if (change.changeType == ChangeType.Dispose)
                return;

            throw new Exception($"{nameof(ObservableObject)} does not support change type {change.changeType}");
        }

        public override void CopyTo(IObservableNode copyTo)
        {
            if (copyTo is not ObservableObject copyToObject)
                throw new Exception($"{copyTo.nodePath} is not a {nameof(ObservableObject)}");

            foreach (var child in children)
            {
                var destChild = copyToObject.GetChild(child.nodeName);

                if (destChild.isDerived)
                    continue;

                child.CopyTo(destChild);
            }
        }

        public override void Reset()
        {
            foreach (ObservableNode child in children.Where(x => !x.isDerived))
                child.Reset();
        }

        public override JSONNode ToJSON(Func<IObservableNode, bool> filter)
        {
            JSONObject obj = new JSONObject();

            foreach (var child in children.Where(filter))
                obj.Add(child.nodeName, child.ToJSON(filter));

            return obj;
        }

        public override void FromJSON(JSONNode json)
        {
            if (json == null)
            {
                Reset();
                return;
            }

            foreach (var child in children)
                child.FromJSON(json[child.nodeName]);
        }
    }
}
