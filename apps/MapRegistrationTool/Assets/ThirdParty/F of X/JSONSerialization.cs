using System;
using System.Collections.Generic;
using SimpleJSON;

namespace FofX.Serialization
{
    public abstract class SerializationPair
    {
        public abstract Type type { get; }

        public abstract object RawFromJSON(JSONNode json);
        public abstract JSONNode RawToJSON(object value);
    }

    public class SerializationPair<T> : SerializationPair
    {
        public override Type type => typeof(T);
        public Func<JSONNode, T> fromJSON { get; private set; }
        public Func<T, JSONNode> toJSON { get; private set; }

        public SerializationPair(Func<JSONNode, T> fromJSON, Func<T, JSONNode> toJSON)
        {
            this.fromJSON = fromJSON;
            this.toJSON = toJSON;
        }

        public override object RawFromJSON(JSONNode json)
        {
            return fromJSON(json);
        }

        public override JSONNode RawToJSON(object value)
        {
            return toJSON((T)value);
        }
    }

    public static class JSONSerialization
    {
        private static Dictionary<Type, SerializationPair> _serializers = new Dictionary<Type, SerializationPair>()
        {
            { typeof(byte), new SerializationPair<byte>(x => x.AsByte, x => (JSONNode)x) },
            { typeof(int), new SerializationPair<int>(x => x.AsInt, x => (JSONNode)x) },
            { typeof(bool), new SerializationPair<bool>(x => x.AsBool, x => (JSONNode)x) },
            { typeof(string), new SerializationPair<string>(x => x.Value, x => (JSONNode)x) },
            { typeof(float), new SerializationPair<float>(x => x.AsFloat, x => (JSONNode)x) },
            { typeof(double), new SerializationPair<double>(x => x.AsDouble, x => (JSONNode)x) },
            { typeof(Guid), new SerializationPair<Guid>(x => Guid.TryParse(x, out var guid) ? guid : Guid.Empty, x => x.ToString()) },
            { typeof(byte?), new SerializationPair<byte?>(x => x == null ? null : x.AsByte, x => x == null ? JSONNull.CreateOrGet() : (JSONNode)x) },
            { typeof(int?), new SerializationPair<int?>(x => x == null ? null : x.AsInt, x => x == null ? JSONNull.CreateOrGet() : (JSONNode)x) },
            { typeof(bool?), new SerializationPair<bool?>(x => x == null ? null : x.AsBool, x => x == null ? JSONNull.CreateOrGet() : (JSONNode)x) },
            { typeof(float?), new SerializationPair<float?>(x => x == null ? null : x.AsFloat, x => x == null ? JSONNull.CreateOrGet() : (JSONNode)x) },
            { typeof(double?), new SerializationPair<double?>(x => x == null ? null : x.AsDouble, x => x == null ? JSONNull.CreateOrGet() : (JSONNode)x) },
        };

        public static JSONNode ToJSON<T>(T value)
        {
            return GetSerializer<T>().toJSON(value);
        }

        public static T FromJSON<T>(JSONNode json)
        {
            return GetSerializer<T>().fromJSON(json);
        }

        public static void AddSerializer<T>(SerializationPair<T> serializer)
        {
            _serializers.Add(typeof(T), serializer);
        }

        public static void AddSerializer<T>(Func<JSONNode, T> fromJSON, Func<T, JSONNode> toJSON)
        {
            _serializers.Add(typeof(T), new SerializationPair<T>(fromJSON, toJSON));
        }

        public static SerializationPair GetSerializer(Type type)
        {
            return _serializers[type];
        }

        public static SerializationPair<T> GetSerializer<T>()
        {
            SerializationPair serializer = null;

            if (_serializers.TryGetValue(typeof(T), out serializer))
            {
                return (SerializationPair<T>)serializer;
            }
            else if (typeof(T).IsEnum)
            {
                serializer = new SerializationPair<T>(x => (T)Enum.ToObject(typeof(T), x.AsInt), x => Convert.ToInt32(x));
                _serializers.Add(typeof(T), serializer);
                return (SerializationPair<T>)serializer;
            }

            throw new Exception($"Attempted to get serializer for unhandled type {typeof(T).Name}");
        }
    }
}
