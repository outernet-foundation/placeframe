#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::UnityEngine {
class Mesh;
}
namespace DotNet::CesiumForUnity {
template <typename T0> class CesiumObjectPool1;
}

namespace DotNet::CesiumForUnity {

class CesiumObjectPools {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumObjectPools(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumObjectPools(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_MeshPool)(void** reinteropException);
  public: static ::DotNet::CesiumForUnity::CesiumObjectPool1<::DotNet::UnityEngine::Mesh> MeshPool();
};

} // namespace DotNet::CesiumForUnity


