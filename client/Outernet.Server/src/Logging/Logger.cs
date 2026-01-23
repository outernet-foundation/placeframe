using R3;
using Serilog;

namespace Outernet.Server
{
    static class Logger
    {
        public static Serilog.Core.Logger logger { get; private set; }
        private static IDisposable subscriptions;

        public static void Initialize()
        {
            logger = new LoggerConfiguration()
                .MinimumLevel.Verbose()
                .Enrich.With<Enricher>()
                .WriteTo.Loki()
                .WriteTo.Console()
                .CreateLogger();

            // If serilog itself throws an exception, log it to the console
            global::Serilog.Debugging.SelfLog.Enable(Console.WriteLine);

            subscriptions = Disposable.Combine(

                // Log uncaught exceptions thrown by Tasks
                Observable
                    .FromEventHandler<UnobservedTaskExceptionEventArgs>(
                        handler => TaskScheduler.UnobservedTaskException += handler,
                        handler => TaskScheduler.UnobservedTaskException -= handler)
                    .Subscribe(args => Log.Error(LogGroup.UncaughtException, args.e.Exception, "TaskScheduler UnobservedTaskException: sender {0}", args.sender))
            );

            // Log uncaught exceptions thrown by R3 subscriptions
            ObservableSystem.RegisterUnhandledExceptionHandler(exception => Log.Error(LogGroup.UncaughtException, exception, "R3 subscription unhandled exception"));
        }

        public static void Terminate()
        {
            subscriptions.Dispose();
            logger.Dispose();
        }

        public static void Serilog(LogLevel level, LogGroup group, Exception exception, string messageTemplate, params object[] propertyValues)
        {
            var loggerWithContext = logger.ForContext("logGroup", group.ToString());

            switch (level)
            {
                case LogLevel.Trace:
                    loggerWithContext.Verbose(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Debug:
                    loggerWithContext.Debug(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Info:
                    loggerWithContext.Information(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Warn:
                    loggerWithContext.Warning(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Error:
                    loggerWithContext.Error(exception, messageTemplate, propertyValues);
                    break;
                case LogLevel.Fatal:
                    loggerWithContext.Fatal(exception, messageTemplate, propertyValues);
                    break;
            }
        }
    }
}