using System;
using System.Collections.Generic;
using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
#endif

namespace Placeframe.MapRegistrationTool
{
    public static class PlayerPrefsEx
    {
        public static bool GetBool(string key, bool defaultValue)
            => PlayerPrefs.GetInt(key, defaultValue ? 1 : 0) == 0 ? false : true;

        public static void SetBool(string key, bool value)
            => PlayerPrefs.SetInt(key, value ? 1 : 0);

        public static T GetEnum<T>(string key, T defaultValue) where T : Enum
            => Enum.TryParse(typeof(T), PlayerPrefs.GetString(key, ""), false, out object value) ? (T)value : defaultValue;

        public static void SetEnum<T>(string key, T value) where T : Enum
            => PlayerPrefs.SetString(key, value.ToString());

#if UNITY_EDITOR
        public static T GetAssetReference<T>(string key, T defaultValue) where T : UnityEngine.Object
        {
            string currentGUID = PlayerPrefs.GetString(key, null);
            return currentGUID == null ? defaultValue : AssetDatabase.LoadAssetAtPath<T>(AssetDatabase.GUIDToAssetPath(currentGUID));
        }

        public static void SetAssetReference<T>(string key, T value) where T : UnityEngine.Object
            => PlayerPrefs.SetString(key, value == null ? null : AssetDatabase.GUIDFromAssetPath(AssetDatabase.GetAssetPath(value)).ToString());
#endif
    }
}