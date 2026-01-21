#include <DotNet/UnityEngine/Mesh.h>
#include <DotNet/CesiumForUnity/CesiumObjectPool1.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::CesiumForUnity {

CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::CesiumObjectPool1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::CesiumObjectPool1(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::GetHandle() {
    return this->_handle;
}


CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::CallGet_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Mesh CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::Get() const {
    void* reinteropException = nullptr;
    auto result = CallGet_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Mesh(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::CallRelease_BN9YLS5wYv1kZRcsGBjgEg)(void* thiz, void* element, void** reinteropException) = nullptr;


void CesiumObjectPool1<::DotNet::UnityEngine::Mesh>::Release(const ::DotNet::UnityEngine::Mesh& element) const {
    void* reinteropException = nullptr;
    CallRelease_BN9YLS5wYv1kZRcsGBjgEg((*this).GetHandle().GetRaw(), element.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity


