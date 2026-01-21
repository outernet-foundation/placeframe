#include <DotNet/System/OperatingSystem.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::System {

OperatingSystem::OperatingSystem(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


OperatingSystem::OperatingSystem(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool OperatingSystem::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool OperatingSystem::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& OperatingSystem::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& OperatingSystem::GetHandle() {
    return this->_handle;
}


OperatingSystem::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::System::OperatingSystem::Property_get_VersionString)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String OperatingSystem::VersionString() const {
    void* reinteropException = nullptr;
    auto result = Property_get_VersionString((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::System


