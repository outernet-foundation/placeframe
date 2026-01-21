#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/Rendering/MeshUpdateFlags.h>
#include <flags/flags.hpp>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine::Rendering {
struct VertexAttributeDescriptor;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::UnityEngine::Rendering {
enum class IndexFormat;
}
namespace DotNet::UnityEngine::Rendering {
struct SubMeshDescriptor;
}
namespace DotNet::UnityEngine::Rendering {
enum class MeshUpdateFlags : uint32_t;
}
namespace DotNet::Unity::Collections {
template <typename T0> struct NativeArray1;
}

namespace DotNet::UnityEngine {

struct MeshData {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit MeshData(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: MeshData(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static ::std::int32_t (*Property_get_subMeshCount)(void* thiz, void** reinteropException);
  public: ::std::int32_t subMeshCount() const;
  private: static void (*Property_set_subMeshCount)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void subMeshCount(::std::int32_t value) const;
  private: static void (*CallSetVertexBufferParams_rY4e33oFKB7g68Q__VYd3ZA)(void* thiz, ::std::int32_t vertexCount, void* attributes, void** reinteropException);
  public: void SetVertexBufferParams(::std::int32_t vertexCount, const ::DotNet::System::Array1<::DotNet::UnityEngine::Rendering::VertexAttributeDescriptor>& attributes) const;
  private: static void (*CallSetIndexBufferParams_33DrxW_6gBzitFJX1cCsNw)(void* thiz, ::std::int32_t indexCount, ::std::uint32_t format, void** reinteropException);
  public: void SetIndexBufferParams(::std::int32_t indexCount, ::DotNet::UnityEngine::Rendering::IndexFormat format) const;
  private: static void (*CallSetSubMesh_UefU0znm5VK66Qs__Aa2BMQ)(void* thiz, ::std::int32_t index, const ::DotNet::UnityEngine::Rendering::SubMeshDescriptor* desc, ::std::uint32_t flags, void** reinteropException);
  public: void SetSubMesh(::std::int32_t index, const ::DotNet::UnityEngine::Rendering::SubMeshDescriptor& desc, ::flags::flags<::DotNet::UnityEngine::Rendering::MeshUpdateFlags> flags) const;
  public: template <typename T>
  ::DotNet::Unity::Collections::NativeArray1<T> GetVertexData(::std::int32_t stream) const;
  private: static void* (*CallGetVertexData__7GtY91GOoYBBL6__e7IK3g)(void* thiz, ::std::int32_t stream, void** reinteropException);
  private: static void* (*CallGetVertexData_dyQZuDnE0veN17wSKpECqg)(void* thiz, ::std::int32_t stream, void** reinteropException);
  private: static void* (*CallGetVertexData_5pXb_vZ42FUJBb__NBZAGDQ)(void* thiz, ::std::int32_t stream, void** reinteropException);
  public: template <typename T>
  ::DotNet::Unity::Collections::NativeArray1<T> GetIndexData() const;
  private: static void* (*CallGetIndexData_YAIddHPxvLNUfgMxRDxChw)(void* thiz, void** reinteropException);
  private: static void* (*CallGetIndexData_Ce46szGfJ6vmevqnTM9T9A)(void* thiz, void** reinteropException);
};

} // namespace DotNet::UnityEngine


