#include <DotNet/UnityEngine/MeshDataArray.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/MeshData.h>



namespace DotNet::UnityEngine {

MeshDataArray::MeshDataArray(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


MeshDataArray::MeshDataArray(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool MeshDataArray::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool MeshDataArray::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& MeshDataArray::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& MeshDataArray::GetHandle() {
    return this->_handle;
}


::std::int32_t (*DotNet::UnityEngine::MeshDataArray::Property_get_Length)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t MeshDataArray::Length() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Length((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::UnityEngine::MeshDataArray::Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::DotNet::UnityEngine::MeshData MeshDataArray::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item((*this).GetHandle().GetRaw(), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::MeshData(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::MeshDataArray::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void MeshDataArray::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine


