# Vibe code: Gemini 3
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /

# Copy csproj files first to leverage Docker caching for restore
# We assume the build context is the repository root
COPY ["client/Outernet.Server/Outernet.Server.csproj", "client/Outernet.Server/"]
COPY ["client/Outernet.Shared/Outernet.Shared.csproj", "client/Outernet.Shared/"]
COPY ["packages/generated/csharp/api-client", "packages/generated/csharp/api-client"]

# Restore dependencies
RUN dotnet restore "client/Outernet.Server/Outernet.Server.csproj"

# Copy the rest of the source code
COPY ["client/Outernet.Server/", "client/Outernet.Server/"]
COPY ["client/Outernet.Shared/", "client/Outernet.Shared/"]

# Build and Publish
WORKDIR "/client/Outernet.Server"
RUN dotnet publish "Outernet.Server.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

# Create a non-root user for security (optional but recommended)
USER app

COPY --from=build /app/publish .

ENTRYPOINT ["dotnet", "Outernet.Server.dll"]