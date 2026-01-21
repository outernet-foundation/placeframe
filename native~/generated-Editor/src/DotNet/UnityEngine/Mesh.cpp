#include <DotNet/UnityEngine/Mesh.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/System/Array1.h>
#include <DotNet/Unity/Collections/NativeArray1.h>
#include <DotNet/UnityEngine/Vector2.h>
#include <DotNet/UnityEngine/MeshTopology.h>
#include <DotNet/UnityEngine/MeshDataArray.h>
#include <DotNet/UnityEngine/Rendering/MeshUpdateFlags.h>
#include <flags/flags.hpp>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/HideFlags.h>



namespace DotNet::UnityEngine {

Mesh::Mesh(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Mesh::Mesh(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Mesh::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Mesh::GetHandle() {
    return this->_handle;
}


void* (*Mesh::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


Mesh::Mesh()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


Mesh::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Mesh::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::UnityEngine::Mesh::Property_get_vertexCount)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Mesh::vertexCount() const {
    void* reinteropException = nullptr;
    auto result = Property_get_vertexCount((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::UnityEngine::Mesh::Property_get_vertices)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Array1<::DotNet::UnityEngine::Vector3> Mesh::vertices() const {
    void* reinteropException = nullptr;
    auto result = Property_get_vertices((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Mesh::Property_set_vertices)(void* thiz, void* value, void** reinteropException) = nullptr;


void Mesh::vertices(const ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3>& value) const {
    void* reinteropException = nullptr;
    Property_set_vertices((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Mesh::CallSetVertices_8SVQMDrqHKz8KuxxeLnZAw)(void* thiz, void* inVertices, void** reinteropException) = nullptr;


template <> void Mesh::SetVertices<::DotNet::UnityEngine::Vector3>(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& inVertices) const {
    void* reinteropException = nullptr;
    CallSetVertices_8SVQMDrqHKz8KuxxeLnZAw((*this).GetHandle().GetRaw(), inVertices.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Mesh::CallSetNormals_Jwfug4VcNnAHDEO5Mr1VPQ)(void* thiz, void* inNormals, void** reinteropException) = nullptr;


template <> void Mesh::SetNormals<::DotNet::UnityEngine::Vector3>(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& inNormals) const {
    void* reinteropException = nullptr;
    CallSetNormals_Jwfug4VcNnAHDEO5Mr1VPQ((*this).GetHandle().GetRaw(), inNormals.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Mesh::CallSetUVs_xhGznZ6iubWLgUmOC8daog)(void* thiz, ::std::int32_t channel, void* uvs, void** reinteropException) = nullptr;


template <> void Mesh::SetUVs<::DotNet::UnityEngine::Vector2>(::std::int32_t channel, const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& uvs) const {
    void* reinteropException = nullptr;
    CallSetUVs_xhGznZ6iubWLgUmOC8daog((*this).GetHandle().GetRaw(), channel, uvs.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Mesh::CallSetIndices_ojn8dGiQbch02RdGWlLnpA)(void* thiz, void* indices, ::std::uint32_t topology, ::std::int32_t submesh, ::std::uint8_t calculateBounds, ::std::int32_t baseVertex, void** reinteropException) = nullptr;


template <> void Mesh::SetIndices<::std::int32_t>(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& indices, ::DotNet::UnityEngine::MeshTopology topology, ::std::int32_t submesh, bool calculateBounds, ::std::int32_t baseVertex) const {
    void* reinteropException = nullptr;
    CallSetIndices_ojn8dGiQbch02RdGWlLnpA((*this).GetHandle().GetRaw(), indices.GetHandle().GetRaw(), ::std::uint32_t(topology), submesh, calculateBounds ? 1 : 0, baseVertex, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Mesh::CallRecalculateBounds_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void Mesh::RecalculateBounds() const {
    void* reinteropException = nullptr;
    CallRecalculateBounds_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Mesh::CallAllocateWritableMeshData_a7RdxWIDVq3m4GTzSAxtDw)(::std::int32_t meshCount, void** reinteropException) = nullptr;


::DotNet::UnityEngine::MeshDataArray Mesh::AllocateWritableMeshData(::std::int32_t meshCount) {
    void* reinteropException = nullptr;
    auto result = CallAllocateWritableMeshData_a7RdxWIDVq3m4GTzSAxtDw(meshCount, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::MeshDataArray(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Mesh::CallApplyAndDisposeWritableMeshData_K7gsr9XXVwYV61pKjp0Flw)(void* data, void* meshes, ::std::uint32_t flags, void** reinteropException) = nullptr;


void Mesh::ApplyAndDisposeWritableMeshData(const ::DotNet::UnityEngine::MeshDataArray& data, const ::DotNet::System::Array1<::DotNet::UnityEngine::Mesh>& meshes, ::flags::flags<::DotNet::UnityEngine::Rendering::MeshUpdateFlags> flags) {
    void* reinteropException = nullptr;
    CallApplyAndDisposeWritableMeshData_K7gsr9XXVwYV61pKjp0Flw(data.GetHandle().GetRaw(), meshes.GetHandle().GetRaw(), flags.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Mesh::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Mesh::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Mesh::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void Mesh::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Mesh::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> Mesh::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::UnityEngine::Mesh::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Mesh::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEngine::Mesh::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Mesh::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool Mesh::operator==(const Mesh& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Mesh::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Mesh::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::UnityEngine::Mesh::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Mesh::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Mesh::operator!=(const Mesh& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Mesh::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Mesh::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::UnityEngine::Mesh::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Mesh::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


