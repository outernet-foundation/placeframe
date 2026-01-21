#include <DotNet/UnityEngine/Resources.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/UnityEngine/Material.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/GameObject.h>



namespace DotNet::UnityEngine {

Resources::Resources(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Resources::Resources(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Resources::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Resources::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Resources::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Resources::GetHandle() {
    return this->_handle;
}


Resources::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::UnityEngine::Resources::CallLoad_rsjQbSk78vk9BZ1CvfZ2fw)(void* path, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::Material Resources::Load<::DotNet::UnityEngine::Material>(const ::DotNet::System::String& path) {
    void* reinteropException = nullptr;
    auto result = CallLoad_rsjQbSk78vk9BZ1CvfZ2fw(path.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Material(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Resources::CallLoad_Sx8S__RAskKFDmQvk60XduA)(void* path, void** reinteropException) = nullptr;


template <> ::DotNet::UnityEngine::GameObject Resources::Load<::DotNet::UnityEngine::GameObject>(const ::DotNet::System::String& path) {
    void* reinteropException = nullptr;
    auto result = CallLoad_Sx8S__RAskKFDmQvk60XduA(path.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::UnityEngine


