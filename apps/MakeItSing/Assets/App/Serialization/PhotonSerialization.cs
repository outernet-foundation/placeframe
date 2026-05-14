using UnityEngine;

using System;
using System.Collections.Generic;
using System.IO;

namespace Plerion.MakeItSing
{
    public class Serializer<T> : Serializer
    {
        public override Type type => typeof(T);
        private Action<BinaryWriter, T> _writeValue;
        private Func<BinaryReader, T> _readValue;

        public Serializer(Action<BinaryWriter, T> writeValue, Func<BinaryReader, T> readValue)
        {
            _writeValue = writeValue;
            _readValue = readValue;
        }

        private void Write(BinaryWriter writer, object value)
        {
            if (!typeof(T).IsValueType)
            {
                bool isNull = value == null;
                writer.Write(isNull);

                if (isNull)
                    return;
            }

            _writeValue(writer, (T)value);
        }

        private T Read(BinaryReader reader)
        {
            if (!typeof(T).IsValueType)
            {
                bool isNull = reader.ReadBoolean();

                if (isNull)
                    return default;
            }

            return _readValue(reader);
        }

        public override void Serialize(BinaryWriter writer, object value, bool isArray)
        {
            if (isArray)
            {
                bool isNull = value == null;
                writer.Write(isNull);

                if (isNull)
                    return;

                var array = (Array)value;
                writer.Write(array.Length);

                foreach (var element in array)
                    Write(writer, (T)element);

                return;
            }

            Write(writer, (T)value);
        }

        public override object Deserialize(BinaryReader reader, bool isArray)
        {
            if (isArray)
            {
                bool isNull = reader.ReadBoolean();

                if (isNull)
                    return null;

                var count = reader.ReadInt32();
                var result = new T[count];

                for (int i = 0; i < count; i++)
                    result[i] = Read(reader);

                return result;
            }

            return Read(reader);
        }
    }

    public abstract class Serializer
    {
        public abstract Type type { get; }
        public abstract void Serialize(BinaryWriter writer, object value, bool isArray);
        public abstract object Deserialize(BinaryReader reader, bool isArray);
    }

    public static class PhotonSerialization
    {
        private static Dictionary<Type, Serializer> _serializers = new Dictionary<Type, Serializer>()
        {
            { typeof(bool), new Serializer<bool>((writer, arg) => writer.Write(arg), reader => reader.ReadBoolean()) },
            { typeof(int), new Serializer<int>((writer, arg) => writer.Write(arg), reader => reader.ReadInt32()) },
            { typeof(float), new Serializer<float>((writer, arg) => writer.Write(arg), reader => reader.ReadSingle()) },
            { typeof(byte), new Serializer<byte>((writer, arg) => writer.Write(arg), reader => reader.ReadByte()) },
            { typeof(string), new Serializer<string>((writer, arg) => writer.Write(arg), reader => reader.ReadString()) },
            { typeof(Vector2), new Serializer<Vector2>(
                (writer, arg) =>
                {
                    writer.Write(arg.x);
                    writer.Write(arg.y);
                },
                reader => new Vector2(reader.ReadSingle(), reader.ReadSingle())
            ) },
            { typeof(Vector3), new Serializer<Vector3>(
                (writer, arg) =>
                {
                    writer.Write(arg.x);
                    writer.Write(arg.y);
                    writer.Write(arg.z);
                },
                reader => new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle())
            ) },
            { typeof(Vector4), new Serializer<Vector4>(
                (writer, arg) =>
                {
                    writer.Write(arg.x);
                    writer.Write(arg.y);
                    writer.Write(arg.z);
                    writer.Write(arg.w);
                },
                reader => new Vector4(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle())
            ) },
            { typeof(Quaternion), new Serializer<Quaternion>(
                (writer, arg) =>
                {
                    writer.Write(arg.x);
                    writer.Write(arg.y);
                    writer.Write(arg.z);
                    writer.Write(arg.w);
                },
                reader => new Quaternion(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle())
            ) },
            { typeof(Color), new Serializer<Color>(
                (writer, arg) =>
                {
                    writer.Write(arg.r);
                    writer.Write(arg.g);
                    writer.Write(arg.b);
                    writer.Write(arg.a);
                },
                reader => new Color(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle())
            ) }
        };

        public static void AddSerializer<T>(Serializer<T> serializer)
        {
            _serializers.Add(typeof(T), serializer);
        }

        public static Serializer GetSerializer(Type type)
        {
            if (type.IsArray)
                return _serializers[type.GetElementType()];

            return _serializers[type];
        }
    }
}