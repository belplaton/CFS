# ===========================================
# Frontend Dockerfile (Blazor WASM + BFF)
# ===========================================
# Multi-stage build:
# 1. Build BFF (ASP.NET Core)
# 2. Build Blazor WebAssembly
# 3. Publish BFF with Blazor static files
# 4. Runtime image
# ===========================================

# -------------------------------------------
# Stage 1: Build BFF
# -------------------------------------------
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build-bff
WORKDIR /src

# Copy solution file
COPY ["CFS.sln", "./"]

# Copy project files
COPY ["bff/Cfs.Bff.csproj", "bff/"]
COPY ["contracts/Cfs.Contracts.csproj", "contracts/"]
COPY ["app/Cfs.Frontend.csproj", "app/"]

# Restore dependencies
RUN dotnet restore "bff/Cfs.Bff.csproj"

# Copy source code
COPY . .

# Build BFF
WORKDIR "/src/bff"
RUN dotnet build "Cfs.Bff.csproj" -c Release -o /app/build

# -------------------------------------------
# Stage 2: Build Blazor WebAssembly
# -------------------------------------------
FROM build-bff AS build-blazor
WORKDIR "/src/app"

# Publish Blazor WASM
RUN dotnet publish "Cfs.Frontend.csproj" -c Release -o /app/blazor

# -------------------------------------------
# Stage 3: Publish BFF with Blazor files
# -------------------------------------------
FROM build-bff AS publish
WORKDIR "/app"

# Copy published BFF
COPY --from=build-bff /app/build ./

# Copy Blazor static files to wwwroot
COPY --from=build-blazor /app/blazor/wwwroot ./wwwroot

# -------------------------------------------
# Stage 4: Runtime
# -------------------------------------------
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS runtime
WORKDIR /app

# Copy published files
COPY --from=publish /app .

# Expose port
EXPOSE 5180

# Set environment variables
ENV ASPNETCORE_URLS=http://+:5180
ENV ASPNETCORE_ENVIRONMENT=Production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5180/api/health || exit 1

# Entry point
ENTRYPOINT ["dotnet", "Cfs.Bff.dll"]
