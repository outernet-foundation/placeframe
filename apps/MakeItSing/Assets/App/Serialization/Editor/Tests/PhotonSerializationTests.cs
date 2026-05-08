using System.IO;
using NUnit.Framework;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class PhotonSerializationTests
    {
        [Test]
        public void TestSerializeDeserialize()
        {
            bool boolVar = true;
            int intVar = 22;
            float floatVar = 0.33f;
            string stringVar = "cat";
            byte byteVar = 2;
            Vector2 vector2Var = new Vector2(1, -2);
            Vector3 vector3Var = new Vector3(1, 0, -2);
            Vector4 vector4Var = new Vector4(1, -2, 0, 0.3f);
            Quaternion quaternionVar = Quaternion.Euler(90f, 30f, 15f);
            Color colorVar = new Color(1, 2, 0, 0.33f);

            byte[] data = null;

            using (var serializationStream = new MemoryStream())
            using (var writer = new BinaryWriter(serializationStream))
            {
                PhotonSerialization.GetSerializer(typeof(bool)).Serialize(writer, boolVar, false);
                PhotonSerialization.GetSerializer(typeof(int)).Serialize(writer, intVar, false);
                PhotonSerialization.GetSerializer(typeof(float)).Serialize(writer, floatVar, false);
                PhotonSerialization.GetSerializer(typeof(string)).Serialize(writer, stringVar, false);
                PhotonSerialization.GetSerializer(typeof(byte)).Serialize(writer, byteVar, false);
                PhotonSerialization.GetSerializer(typeof(Vector2)).Serialize(writer, vector2Var, false);
                PhotonSerialization.GetSerializer(typeof(Vector3)).Serialize(writer, vector3Var, false);
                PhotonSerialization.GetSerializer(typeof(Vector4)).Serialize(writer, vector4Var, false);
                PhotonSerialization.GetSerializer(typeof(Quaternion)).Serialize(writer, quaternionVar, false);
                PhotonSerialization.GetSerializer(typeof(Color)).Serialize(writer, colorVar, false);
                data = serializationStream.ToArray();
            }

            using (var deserializationStream = new MemoryStream(data))
            using (var reader = new BinaryReader(deserializationStream))
            {
                Assert.AreEqual(boolVar, PhotonSerialization.GetSerializer(typeof(bool)).Deserialize(reader, false));
                Assert.AreEqual(intVar, PhotonSerialization.GetSerializer(typeof(int)).Deserialize(reader, false));
                Assert.AreEqual(floatVar, PhotonSerialization.GetSerializer(typeof(float)).Deserialize(reader, false));
                Assert.AreEqual(stringVar, PhotonSerialization.GetSerializer(typeof(string)).Deserialize(reader, false));
                Assert.AreEqual(byteVar, PhotonSerialization.GetSerializer(typeof(byte)).Deserialize(reader, false));
                Assert.AreEqual(vector2Var, PhotonSerialization.GetSerializer(typeof(Vector2)).Deserialize(reader, false));
                Assert.AreEqual(vector3Var, PhotonSerialization.GetSerializer(typeof(Vector3)).Deserialize(reader, false));
                Assert.AreEqual(vector4Var, PhotonSerialization.GetSerializer(typeof(Vector4)).Deserialize(reader, false));
                Assert.AreEqual(quaternionVar, PhotonSerialization.GetSerializer(typeof(Quaternion)).Deserialize(reader, false));
                Assert.AreEqual(colorVar, PhotonSerialization.GetSerializer(typeof(Color)).Deserialize(reader, false));
            }
        }

        [Test]
        public void TestSerializeDeserializeArray()
        {
            bool[] boolVar = new bool[] { true, false, true, true, true, false };
            int[] intVar = new int[] { 22, -12, 12, 0, 2 };
            float[] floatVar = new float[] { 0.33f, 1f, 1.00001f, Mathf.Epsilon };
            string[] stringVar = new string[] { "cat", "dog", "frog", null, "me", "you" };
            byte[] byteVar = new byte[] { 2, 64, 100, 0, 2 };
            Vector2[] vector2Var = new Vector2[] { new Vector2(1, -2), new Vector2(0, 0), new Vector2(-0.5f, .44f) };
            Vector3[] vector3Var = new Vector3[] { new Vector3(1, 0, -2), new Vector3(0, 0, 0), new Vector3(0.33f, 0.33f, 0.66f) };
            Vector4[] vector4Var = new Vector4[] { new Vector4(1, -2, 0, 0.3f), new Vector4(0, 0, 0, 0), new Vector4(1, 0, 0, 0) };
            Quaternion[] quaternionVar = new Quaternion[] { Quaternion.Euler(90f, 30f, 15f), Quaternion.Euler(90f, 15f, 30f), Quaternion.Euler(0, 0, 0), Quaternion.Euler(90f, 0f, 14f) };
            Color[] colorVar = new Color[] { new Color(1, 2, 0, 0.33f), new Color(0, 3, 5, 0.33f), new Color(0, 0, 0, 0) };

            byte[] data = null;

            using (var serializationStream = new MemoryStream())
            using (var writer = new BinaryWriter(serializationStream))
            {
                PhotonSerialization.GetSerializer(typeof(bool)).Serialize(writer, boolVar, true);
                PhotonSerialization.GetSerializer(typeof(int)).Serialize(writer, intVar, true);
                PhotonSerialization.GetSerializer(typeof(float)).Serialize(writer, floatVar, true);
                PhotonSerialization.GetSerializer(typeof(string)).Serialize(writer, stringVar, true);
                PhotonSerialization.GetSerializer(typeof(byte)).Serialize(writer, byteVar, true);
                PhotonSerialization.GetSerializer(typeof(Vector2)).Serialize(writer, vector2Var, true);
                PhotonSerialization.GetSerializer(typeof(Vector3)).Serialize(writer, vector3Var, true);
                PhotonSerialization.GetSerializer(typeof(Vector4)).Serialize(writer, vector4Var, true);
                PhotonSerialization.GetSerializer(typeof(Quaternion)).Serialize(writer, quaternionVar, true);
                PhotonSerialization.GetSerializer(typeof(Color)).Serialize(writer, colorVar, true);
                data = serializationStream.ToArray();
            }

            using (var deserializationStream = new MemoryStream(data))
            using (var reader = new BinaryReader(deserializationStream))
            {
                Assert.AreEqual(boolVar, PhotonSerialization.GetSerializer(typeof(bool)).Deserialize(reader, true));
                Assert.AreEqual(intVar, PhotonSerialization.GetSerializer(typeof(int)).Deserialize(reader, true));
                Assert.AreEqual(floatVar, PhotonSerialization.GetSerializer(typeof(float)).Deserialize(reader, true));
                Assert.AreEqual(stringVar, PhotonSerialization.GetSerializer(typeof(string)).Deserialize(reader, true));
                Assert.AreEqual(byteVar, PhotonSerialization.GetSerializer(typeof(byte)).Deserialize(reader, true));
                Assert.AreEqual(vector2Var, PhotonSerialization.GetSerializer(typeof(Vector2)).Deserialize(reader, true));
                Assert.AreEqual(vector3Var, PhotonSerialization.GetSerializer(typeof(Vector3)).Deserialize(reader, true));
                Assert.AreEqual(vector4Var, PhotonSerialization.GetSerializer(typeof(Vector4)).Deserialize(reader, true));
                Assert.AreEqual(quaternionVar, PhotonSerialization.GetSerializer(typeof(Quaternion)).Deserialize(reader, true));
                Assert.AreEqual(colorVar, PhotonSerialization.GetSerializer(typeof(Color)).Deserialize(reader, true));
            }
        }
    }
}