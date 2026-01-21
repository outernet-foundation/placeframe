#include <DotNet/UnityEngine/SystemInfo.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Experimental/Rendering/GraphicsFormat.h>
#include <DotNet/UnityEngine/Experimental/Rendering/FormatUsage.h>



namespace DotNet::UnityEngine {

SystemInfo::SystemInfo(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


SystemInfo::SystemInfo(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool SystemInfo::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool SystemInfo::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& SystemInfo::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& SystemInfo::GetHandle() {
    return this->_handle;
}


SystemInfo::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::UnityEngine::SystemInfo::CallIsFormatSupported_DuaX37kfZJZ9DeCzoZGKPA)(::std::uint32_t format, ::std::uint32_t usage, void** reinteropException) = nullptr;


bool SystemInfo::IsFormatSupported(::DotNet::UnityEngine::Experimental::Rendering::GraphicsFormat format, ::DotNet::UnityEngine::Experimental::Rendering::FormatUsage usage) {
    void* reinteropException = nullptr;
    auto result = CallIsFormatSupported_DuaX37kfZJZ9DeCzoZGKPA(::std::uint32_t(format), ::std::uint32_t(usage), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


} // namespace DotNet::UnityEngine


