using System;
using System.Collections.Concurrent;
using UnityEngine;

using FofX.Stateful;

namespace FofX
{
    public abstract class AppBase<T> : MonoBehaviour where T : IObservableNode, new()
    {
        public static T state { get; private set; }
        private static AppBase<T> _instance;

        private abstract class ScheduledActionData
        {
            public abstract void ExecuteActions();
        }

        protected virtual void Awake()
        {
            if (_instance != null)
            {
                Destroy(this);
                throw new Exception($"There can only be one instance of {nameof(AppBase<T>)} in the scene at a time.");
            }

            _instance = this;
            state = new T();
            InitializeState(state);
        }

        protected abstract void InitializeState(T state);

        protected virtual void Update()
        {
            state.context.ExecuteScheduledActions();
        }

        public static void ExecuteAction(params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteAction(state, actions);

        public static void ExecuteAction(LogLevel logLevel, params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteAction(state, logLevel: logLevel, actions);

        public static void ExecuteAction(Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteAction(state, postObserverCallback: postObserverCallback, actions);

        public static void ExecuteAction(LogLevel logLevel, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteAction(state, logLevel, postObserverCallback, actions);

        public static void ExecuteActionOrDelay(params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteActionOrDelay(state, actions);

        public static void ExecuteActionOrDelay(LogLevel logLevel, params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteActionOrDelay(state, logLevel: logLevel, actions);

        public static void ExecuteActionOrDelay(Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteActionOrDelay(state, postObserverCallback: postObserverCallback, actions);

        public static void ExecuteActionOrDelay(LogLevel logLevel, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            => state.context.ExecuteActionOrDelay(state, logLevel, postObserverCallback, actions);

        public static void ScheduleAction(params ObservableNodeAction<T>[] actions)
            => state.context.ScheduleAction(state, actions);

        public static void ScheduleAction(LogLevel logLevel, params ObservableNodeAction<T>[] actions)
            => state.context.ScheduleAction(state, logLevel, actions);

        public static void ScheduleAction(Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            => state.context.ScheduleAction(state, postObserverCallback, actions);

        public static void ScheduleAction(LogLevel logLevel, Action postObserverCallback, params ObservableNodeAction<T>[] actions)
            => state.context.ScheduleAction(state, logLevel, postObserverCallback, actions);

        public static void RegisterObserver(ObserverDelegate observer, params IObservableNode[] nodes)
            => state.context.RegisterObserver(observer, nodes);

        public static void DeregisterObserver(ObserverDelegate observer)
            => state.context.DeregisterObserver(observer);
    }
}
