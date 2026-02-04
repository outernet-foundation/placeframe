using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace Placeframe.MapRegistrationTool
{
    public static class LoggingTests
    {
        public static void Test(int i)
        {
            // // Test simple log message
            // Log.Info(LogGroup.LoggingTests, "TEST: This is a test log message");

            // // Test properties
            // Log.Info(LogGroup.LoggingTests, "TEST: message with properties: {testProperty}", "PropertyValue");

            // // Test renderings
            // Log.Info(LogGroup.LoggingTests, "TEST: Rendering {renderingValue:0000}", 42);

            // // Test error log message
            // Log.Error(LogGroup.LoggingTests, "TEST: This is an error log message");

            // // Test destructuring (StructureValue)
            // Log.Info(LogGroup.LoggingTests, "TEST: The god of the day is {@God}", new
            // {
            //     Name = "Odin",
            //     Realm = "Asgard",
            //     Power = "Wisdom"
            // });

            // // Test destructuring (DictionaryValue)
            // Log.Info(LogGroup.LoggingTests, "TEST: God attributes: {@GodAttributes}", new Dictionary<string, string>
            // {
            //     { "Name", "Odin" },
            //     { "Realm", "Asgard" },
            //     { "Power", "Wisdom" }
            // });

            // // Test destructuring (SequenceValue)
            // Log.Info(LogGroup.LoggingTests, "TEST: God powers: {@Powers}", new List<string> { "Wisdom", "Strength", "Foresight" });

            // // Test inner exceptions
            // try
            // {
            //     ThrowInnerException();
            // }
            // catch (Exception exception)
            // {
            //     Log.Error(LogGroup.LoggingTests, exception, "TEST: Caught an inner exception");
            // }

            // // Test aggregate exceptions
            // try
            // {
            //     ThrowAggregateException();
            // }
            // catch (Exception exception)
            // {
            //     Log.Error(LogGroup.LoggingTests, exception, "TEST:  Caught an aggregate exception");
            // }

            // // Test logging from different threads
            // UniTask.RunOnThreadPool(() => LogFromDifferentThread()).Forget();

            // // Test logging from with UnityEngine.Debug
            // UnityEngine.Debug.Log("TEST: UnityEngine.Log");
            // UnityEngine.Debug.LogWarning("TEST: UnityEngine.LogWarning");
            // UnityEngine.Debug.LogError("TEST: UnityEngine.LogError");

            // try
            // {
            //     ThrowAggregateException();
            // }
            // catch (Exception exception)
            // {
            //     UnityEngine.Debug.LogException(exception);
            // }

            // // Test logging from with UnityEngine.Debug from different threads
            // UniTask.RunOnThreadPool(() => UnityEngineLogFromDifferentThread()).Forget();

            // Test logging from native code by assigning a Vector3 with NaN values to a transform's position, which logs an error from native code
            new GameObject().transform.position = new Vector3(float.NaN, float.NaN, float.NaN);
        }

        private static void LogFromDifferentThread()
        {
            Log.Info(LogGroup.LoggingTests, "TEST: Log.Info from a non-main thread");
            Log.Warn(LogGroup.LoggingTests, "TEST: Log.Warn from a non-main thread");
            Log.Error(LogGroup.LoggingTests, "TEST: Log.Error from a non-main thread");

            try
            {
                ThrowAggregateException();
            }
            catch (Exception exception)
            {
                Log.Error(LogGroup.LoggingTests, exception, "TEST: Caught an inner exception on a different thread");
            }
        }

        private static void UnityEngineLogFromDifferentThread()
        {
            UnityEngine.Debug.Log("TEST: UnityEngine.Log from a non-main thread");
            UnityEngine.Debug.LogWarning("TEST: UnityEngine.LogWarning from a non-main thread");
            UnityEngine.Debug.LogError("TEST: UnityEngine.LogError from a non-main thread");

            try
            {
                ThrowAggregateException();
            }
            catch (Exception exception)
            {
                UnityEngine.Debug.LogException(exception);
            }
        }

        private static void ThrowInnerException()
        {
            try
            {
                ThrowException();
            }
            catch (Exception exception)
            {
                throw new InvalidOperationException("TEST: outer exception", exception);
            }
        }

        private static void ThrowException()
        {
            throw new InvalidOperationException("TEST: inner exception");
        }

        private static void ThrowAggregateException()
        {
            var exceptions = new List<Exception>();

            try
            {
                ThrowFirstInnerException();
            }
            catch (Exception exception)
            {
                exceptions.Add(exception);
            }

            try
            {
                ThrowSecondInnerException();
            }
            catch (Exception exception)
            {
                exceptions.Add(exception);
            }

            throw new AggregateException("TEST: aggregate exception", exceptions);
        }

        private static void ThrowFirstInnerException()
        {
            throw new InvalidOperationException("TEST: first inner exception");
        }

        private static void ThrowSecondInnerException()
        {
            throw new ArgumentException("TEST: second inner exception");
        }
    }
}
