using System.Diagnostics;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.Extensions.DependencyInjection;

namespace Outernet.Server
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Contains("--wait-for-debugger"))
            {
                Console.WriteLine("Waiting for debugger");
                while (!Debugger.IsAttached)
                    Thread.Sleep(100);
                Console.WriteLine("Debugger attached");
            }

            Logger.Initialize();
            Log.enabledLogGroups = ~LogGroup.None;
            Log.logLevel = LogLevel.Info;
            Log.stackTraceLevel = LogLevel.Warn;

            Log.Info("Starting server");

            var builder = WebApplication.CreateBuilder(args);

            builder.WebHost.ConfigureKestrel(options =>
            {
                options.ConfigureEndpointDefaults(endpointOptions =>
                {
                    endpointOptions.Protocols = HttpProtocols.Http2;
                });
            });

            builder.Services.AddGrpc();
            builder.Services.AddMagicOnion();
            builder.Services.AddHostedService<SyncedStateService>();
            builder.Services.AddHttpClient<TokenManager>();
            builder.Services.AddSingleton<TokenManager>();
            builder.Services.AddSingleton<PlerionAPI>();

            var app = builder.Build();

            app.MapMagicOnionService();
            app.Run("http://0.0.0.0:5000");
        }
    }
}
