#include <DotNet/UnityEngine/MeshData.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Rendering/VertexAttributeDescriptor.h>
#include <DotNet/System/Array1.h>
#include <DotNet/UnityEngine/Rendering/IndexFormat.h>
#include <DotNet/UnityEngine/Rendering/SubMeshDescriptor.h>
#include <DotNet/UnityEngine/Rendering/MeshUpdateFlags.h>
#include <flags/flags.hpp>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/Unity/Collections/NativeArray1.h>
#include <DotNet/UnityEngine/Vector2.h>

namespace DotNet::UnityEngine::Rendering {
struct SubMeshDescriptor;
}

namespace DotNet::UnityEngine {

MeshData::MeshData(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


MeshData::MeshData(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool MeshData::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool MeshData::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& MeshData::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& MeshData::GetHandle() {
    return this->_handle;
}


::std::int32_t (*DotNet::UnityEngine::MeshData::Property_get_subMeshCount)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t MeshData::subMeshCount() const {
    void* reinteropException = nullptr;
    auto result = Property_get_subMeshCount((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::MeshData::Property_set_subMeshCount)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void MeshData::subMeshCount(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_subMeshCount((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::MeshData::CallSetVertexBufferParams_rY4e33oFKB7g68Q__VYd3ZA)(void* thiz, ::std::int32_t vertexCount, void* attributes, void** reinteropException) = nullptr;


void MeshData::SetVertexBufferParams(::std::int32_t vertexCount, const ::DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>& attributes) const {
    void* reinteropException = nullptr;
    CallSetVertexBufferParams_rY4e33oFKB7g68Q__VYd3ZA((*this).GetHandle().GetRaw(), vertexCount, attributes.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::MeshData::CallSetIndexBufferParams_33DrxW_6gBzitFJX1cCsNw)(void* thiz, ::std::int32_t indexCount, ::std::uint32_t format, void** reinteropException) = nullptr;


void MeshData::SetIndexBufferParams(::std::int32_t indexCount, ::DotNet::UnityEngine::Rendering::IndexFormat format) const {
    void* reinteropException = nullptr;
    CallSetIndexBufferParams_33DrxW_6gBzitFJX1cCsNw((*this).GetHandle().GetRaw(), indexCount, ::std::uint32_t(format), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::MeshData::CallSetSubMesh_UefU0znm5VK66Qs__Aa2BMQ)(void* thiz, ::std::int32_t index, const ::DotNet::UnityEngine::Rendering::SubMeshDescriptor* desc, ::std::uint32_t flags, void** reinteropException) = nullptr;


void MeshData::SetSubMesh(::std::int32_t index, const ::DotNet::UnityEngine::Rendering::SubMeshDescriptor& desc, ::flags::flags<::DotNet::UnityEngine::Rendering::MeshUpdateFlags> flags) const {
    void* reinteropException = nullptr;
    CallSetSubMesh_UefU0znm5VK66Qs__Aa2BMQ((*this).GetHandle().GetRaw(), index, &desc, flags.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::MeshData::CallGetVertexData__7GtY91GOoYBBL6__e7IK3g)(void* thiz, ::std::int32_t stream, void** reinteropException) = nullptr;


template <> ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3> MeshData::GetVertexData<::DotNet::UnityEngine::Vector3>(::std::int32_t stream) const {
    void* reinteropException = nullptr;
    auto result = CallGetVertexData__7GtY91GOoYBBL6__e7IK3g((*this).GetHandle().GetRaw(), stream, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::MeshData::CallGetVertexData_dyQZuDnE0veN17wSKpECqg)(void* thiz, ::std::int32_t stream, void** reinteropException) = nullptr;


template <> ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2> MeshData::GetVertexData<::DotNet::UnityEngine::Vector2>(::std::int32_t stream) const {
    void* reinteropException = nullptr;
    auto result = CallGetVertexData_dyQZuDnE0veN17wSKpECqg((*this).GetHandle().GetRaw(), stream, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::MeshData::CallGetVertexData_5pXb_vZ42FUJBb__NBZAGDQ)(void* thiz, ::std::int32_t stream, void** reinteropException) = nullptr;


template <> ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t> MeshData::GetVertexData<::std::uint8_t>(::std::int32_t stream) const {
    void* reinteropException = nullptr;
    auto result = CallGetVertexData_5pXb_vZ42FUJBb__NBZAGDQ((*this).GetHandle().GetRaw(), stream, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::MeshData::CallGetIndexData_YAIddHPxvLNUfgMxRDxChw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t> MeshData::GetIndexData<::std::uint16_t>() const {
    void* reinteropException = nullptr;
    auto result = CallGetIndexData_YAIddHPxvLNUfgMxRDxChw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::MeshData::CallGetIndexData_Ce46szGfJ6vmevqnTM9T9A)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t> MeshData::GetIndexData<::std::uint32_t>() const {
    void* reinteropException = nullptr;
    auto result = CallGetIndexData_Ce46szGfJ6vmevqnTM9T9A((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::UnityEngine


