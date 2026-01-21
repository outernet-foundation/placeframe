#include <DotNet/CesiumForUnity/CesiumObjectPools.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/UnityEngine/Mesh.h>
#include <DotNet/CesiumForUnity/CesiumObjectPool1.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::CesiumForUnity {

CesiumObjectPools::CesiumObjectPools(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumObjectPools::CesiumObjectPools(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumObjectPools::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumObjectPools::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumObjectPools::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumObjectPools::GetHandle() {
    return this->_handle;
}


CesiumObjectPools::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumObjectPools::Property_get_MeshPool)(void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumObjectPool1<::DotNet::UnityEngine::Mesh> CesiumObjectPools::MeshPool() {
    void* reinteropException = nullptr;
    auto result = Property_get_MeshPool(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumObjectPool1<::DotNet::UnityEngine::Mesh>(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::CesiumForUnity


