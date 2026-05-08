using SimpleJSON;
using Unity.Mathematics;
using UnityEngine;

namespace Plerion.MakeItSing
{
    public class JSONSerializers : MonoBehaviour
    {
        public static JSONNode ToJSON(double2 value)
        {
            var json = new JSONArray();
            json.Add(value.x);
            json.Add(value.y);
            return json;
        }

        public static double2 ToDouble2(JSONNode json)
        {
            return new double2(json[0].AsDouble, json[1].AsDouble);
        }

        public static JSONNode ToJSON(double3 value)
        {
            var json = new JSONArray();
            json.Add(value.x);
            json.Add(value.y);
            json.Add(value.z);
            return json;
        }

        public static double3 ToDouble3(JSONNode json)
        {
            return new double3(json[0].AsDouble, json[1].AsDouble, json[2].AsDouble);
        }

        public static JSONNode ToJSON(Vector2 value)
        {
            var json = new JSONArray();
            json.Add(value.x);
            json.Add(value.y);
            return json;
        }

        public static Vector2 ToVector2(JSONNode json)
        {
            return new Vector2(json[0].AsFloat, json[1].AsFloat);
        }

        public static JSONNode ToJSON(Vector3 value)
        {
            var json = new JSONArray();
            json.Add(value.x);
            json.Add(value.y);
            json.Add(value.z);
            return json;
        }

        public static Vector3 ToVector3(JSONNode json)
        {
            return new Vector3(json[0].AsFloat, json[1].AsFloat, json[2].AsFloat);
        }

        public static JSONNode ToJSON(Vector4 value)
        {
            var json = new JSONArray();
            json.Add(value.x);
            json.Add(value.y);
            json.Add(value.z);
            json.Add(value.w);
            return json;
        }

        public static Vector4 ToVector4(JSONNode json)
        {
            return new Vector4(json[0].AsFloat, json[1].AsFloat, json[2].AsFloat, json[3].AsFloat);
        }

        public static JSONNode ToJSON(Quaternion value)
        {
            var json = new JSONArray();
            json.Add(value.x);
            json.Add(value.y);
            json.Add(value.z);
            json.Add(value.w);
            return json;
        }

        public static Quaternion ToQuaternion(JSONNode json)
        {
            return new Quaternion(json[0].AsFloat, json[1].AsFloat, json[2].AsFloat, json[3].AsFloat);
        }

        public static JSONNode ToJSON(Color value)
        {
            var json = new JSONArray();
            json.Add(value.r);
            json.Add(value.g);
            json.Add(value.b);
            json.Add(value.a);
            return json;
        }

        public static Color ToColor(JSONNode json)
        {
            return new Color(json[0].AsFloat, json[1].AsFloat, json[2].AsFloat, json[3].AsFloat);
        }
    }
}