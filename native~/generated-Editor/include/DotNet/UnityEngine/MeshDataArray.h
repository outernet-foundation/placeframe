#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine {
struct MeshData;
}

namespace DotNet::UnityEngine {

struct MeshDataArray {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit MeshDataArray(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: MeshDataArray(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static ::std::int32_t (*Property_get_Length)(void* thiz, void** reinteropException);
  public: ::std::int32_t Length() const;
  private: static void* (*Property_get_Item)(void* thiz, ::std::int32_t index, void** reinteropException);
  public: ::DotNet::UnityEngine::MeshData operator[](::std::int32_t index) const;
  private: static void (*CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Dispose() const;
};

} // namespace DotNet::UnityEngine


