#include <DotNet/System/Environment.h>
#include <DotNet/System/OperatingSystem.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::System {

void* (*DotNet::System::Environment::Property_get_OSVersion)(void** reinteropException) = nullptr;


::DotNet::System::OperatingSystem Environment::OSVersion() {
    void* reinteropException = nullptr;
    auto result = Property_get_OSVersion(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::OperatingSystem(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::System


