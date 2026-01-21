#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/Rendering/MeshUpdateFlags.h>
#include <flags/flags.hpp>
#include <DotNet/UnityEngine/HideFlags.h>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::Unity::Collections {
template <typename T0> struct NativeArray1;
}
namespace DotNet::UnityEngine {
enum class MeshTopology;
}
namespace DotNet::UnityEngine {
struct MeshDataArray;
}
namespace DotNet::UnityEngine {
class Mesh;
}
namespace DotNet::UnityEngine::Rendering {
enum class MeshUpdateFlags : uint32_t;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::UnityEngine {

class Mesh {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Mesh(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Mesh(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: Mesh();
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_vertexCount)(void* thiz, void** reinteropException);
  public: ::std::int32_t vertexCount() const;
  private: static void* (*Property_get_vertices)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3> vertices() const;
  private: static void (*Property_set_vertices)(void* thiz, void* value, void** reinteropException);
  public: void vertices(const ::DotNet::System::Array1<::DotNet::UnityEngine::Vector3>& value) const;
  public: template <typename T>
  void SetVertices(const ::DotNet::Unity::Collections::NativeArray1<T>& inVertices) const;
  private: static void (*CallSetVertices_8SVQMDrqHKz8KuxxeLnZAw)(void* thiz, void* inVertices, void** reinteropException);
  public: template <typename T>
  void SetNormals(const ::DotNet::Unity::Collections::NativeArray1<T>& inNormals) const;
  private: static void (*CallSetNormals_Jwfug4VcNnAHDEO5Mr1VPQ)(void* thiz, void* inNormals, void** reinteropException);
  public: template <typename T>
  void SetUVs(::std::int32_t channel, const ::DotNet::Unity::Collections::NativeArray1<T>& uvs) const;
  private: static void (*CallSetUVs_xhGznZ6iubWLgUmOC8daog)(void* thiz, ::std::int32_t channel, void* uvs, void** reinteropException);
  public: template <typename T>
  void SetIndices(const ::DotNet::Unity::Collections::NativeArray1<T>& indices, ::DotNet::UnityEngine::MeshTopology topology, ::std::int32_t submesh, bool calculateBounds, ::std::int32_t baseVertex) const;
  private: static void (*CallSetIndices_ojn8dGiQbch02RdGWlLnpA)(void* thiz, void* indices, ::std::uint32_t topology, ::std::int32_t submesh, ::std::uint8_t calculateBounds, ::std::int32_t baseVertex, void** reinteropException);
  private: static void (*CallRecalculateBounds_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void RecalculateBounds() const;
  private: static void* (*CallAllocateWritableMeshData_a7RdxWIDVq3m4GTzSAxtDw)(::std::int32_t meshCount, void** reinteropException);
  public: static ::DotNet::UnityEngine::MeshDataArray AllocateWritableMeshData(::std::int32_t meshCount);
  private: static void (*CallApplyAndDisposeWritableMeshData_K7gsr9XXVwYV61pKjp0Flw)(void* data, void* meshes, ::std::uint32_t flags, void** reinteropException);
  public: static void ApplyAndDisposeWritableMeshData(const ::DotNet::UnityEngine::MeshDataArray& data, const ::DotNet::System::Array1<::DotNet::UnityEngine::Mesh>& meshes, ::flags::flags<::DotNet::UnityEngine::Rendering::MeshUpdateFlags> flags);
  private: static void* (*Property_get_name)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String name() const;
  private: static void (*Property_set_name)(void* thiz, void* value, void** reinteropException);
  public: void name(const ::DotNet::System::String& value) const;
  private: static ::std::uint32_t (*Property_get_hideFlags)(void* thiz, void** reinteropException);
  public: ::flags::flags<::DotNet::UnityEngine::HideFlags> hideFlags() const;
  private: static void (*Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const;
  private: static ::std::uint8_t (*Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator==(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator==(const Mesh& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const Mesh& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::UnityEngine


