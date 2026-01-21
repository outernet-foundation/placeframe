#include <DotNet/UnityEngine/Application.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/UnityEngine/RuntimePlatform.h>



namespace DotNet::UnityEngine {

Application::Application(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Application::Application(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Application::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Application::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Application::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Application::GetHandle() {
    return this->_handle;
}


Application::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEngine::Application::Property_get_temporaryCachePath)(void** reinteropException) = nullptr;


::DotNet::System::String Application::temporaryCachePath() {
    void* reinteropException = nullptr;
    auto result = Property_get_temporaryCachePath(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Application::Property_get_version)(void** reinteropException) = nullptr;


::DotNet::System::String Application::version() {
    void* reinteropException = nullptr;
    auto result = Property_get_version(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Application::Property_get_unityVersion)(void** reinteropException) = nullptr;


::DotNet::System::String Application::unityVersion() {
    void* reinteropException = nullptr;
    auto result = Property_get_unityVersion(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint32_t (*DotNet::UnityEngine::Application::Property_get_platform)(void** reinteropException) = nullptr;


::DotNet::UnityEngine::RuntimePlatform Application::platform() {
    void* reinteropException = nullptr;
    auto result = Property_get_platform(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::RuntimePlatform(result);
}


void* (*DotNet::UnityEngine::Application::Property_get_productName)(void** reinteropException) = nullptr;


::DotNet::System::String Application::productName() {
    void* reinteropException = nullptr;
    auto result = Property_get_productName(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::UnityEngine::Application::Property_get_isEditor)(void** reinteropException) = nullptr;


bool Application::isEditor() {
    void* reinteropException = nullptr;
    auto result = Property_get_isEditor(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::UnityEngine::Application::CallOpenURL_i4__FgVIR5VYHO4KBzPBwNQ)(void* url, void** reinteropException) = nullptr;


void Application::OpenURL(const ::DotNet::System::String& url) {
    void* reinteropException = nullptr;
    CallOpenURL_i4__FgVIR5VYHO4KBzPBwNQ(url.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine


