# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy project files and local packages
COPY ["legacy/Outernet.Server/Outernet.Server.csproj", "legacy/Outernet.Server/"]
COPY ["legacy/Outernet.Shared/Outernet.Shared.csproj", "legacy/Outernet.Shared/"]
COPY ["packages/generated/csharp/api-client/", "packages/generated/csharp/api-client/"]

RUN dotnet restore "legacy/Outernet.Server/Outernet.Server.csproj"

# Copy source
COPY ["legacy/Outernet.Server/", "legacy/Outernet.Server/"]
COPY ["legacy/Outernet.Shared/", "legacy/Outernet.Shared/"]

# Publish in DEBUG mode for full symbol support
WORKDIR "/src/legacy/Outernet.Server"
RUN dotnet publish "Outernet.Server.csproj" -c Debug -o /app/publish /p:UseAppHost=false

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
EXPOSE 8080

# Switch to root to install debugger
USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://aka.ms/getvsdbgsh | bash /dev/stdin -v latest -l /app/vsdbg \
    && chown -R app:app /app/vsdbg

# Switch to the non-root user for execution
USER app
COPY --from=build /app/publish .

# The binary name must match your project output
ENTRYPOINT ["dotnet", "Outernet.Server.dll"]