#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::UnityEngine {
class Mesh;
}
namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::CesiumForUnity {

template <typename T0>
class CesiumObjectPool1;

template <> class CesiumObjectPool1<::DotNet::UnityEngine::Mesh> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumObjectPool1(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumObjectPool1(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallGet_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Mesh Get() const;
  private: static void (*CallRelease_BN9YLS5wYv1kZRcsGBjgEg)(void* thiz, void* element, void** reinteropException);
  public: void Release(const ::DotNet::UnityEngine::Mesh& element) const;
};

} // namespace DotNet::CesiumForUnity


