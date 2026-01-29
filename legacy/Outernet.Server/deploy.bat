@echo off
REM Check if stack name is provided
if "%1"=="" (
    echo Usage: deploy.bat [stack-name]
    exit /b 1
)

set STACK_NAME=%1
set EC2_USER=ec2-user
set PEM_FILE=%USERPROFILE%\my-key-pair.pem
set LOCAL_BUILD_PATH=bin\Release\net8.0\publish
set REMOTE_PATH=/home/ec2-user/synced-state-server
set BINARY_NAME=Outernet.Server.dll
set INFRA_PATH=..\..\infrastructure

REM Get EC2 Public IP for the specified stack
pushd %INFRA_PATH% 
for /f "tokens=*" %%i in ('pulumi stack output PublicIp --stack %STACK_NAME%') do set EC2_IP=%%i
popd

REM Check if the EC2_IP was retrieved successfully
if "%EC2_IP%"=="" (
    echo Error: Failed to retrieve PublicIp for stack "%STACK_NAME%". Ensure the stack exists and has an output named "PublicIp".
    exit /b 1
)

echo EC2 Public IP: %EC2_IP%

REM Build the project
echo Building the project...
dotnet publish -c Release

REM Stop the running server on EC2
echo Stopping the running server on EC2...
ssh -i %PEM_FILE% %EC2_USER%@%EC2_IP% "pkill dotnet || true"

REM Deploy new binaries to the EC2 instance
echo Deploying new binaries to the EC2 instance...
ssh -i %PEM_FILE% %EC2_USER%@%EC2_IP% "mkdir -p %REMOTE_PATH%"
scp -i %PEM_FILE% -r %LOCAL_BUILD_PATH%/* %EC2_USER%@%EC2_IP%:%REMOTE_PATH%

REM Start the server
echo Starting the server...
ssh -i %PEM_FILE% %EC2_USER%@%EC2_IP% "nohup dotnet %REMOTE_PATH%/%BINARY_NAME% > %REMOTE_PATH%/server.log 2>&1 & exit"

echo Deployment complete!
