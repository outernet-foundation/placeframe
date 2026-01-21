#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::CesiumForUnity {
class Cesium3DTileset;
}
namespace DotNet::CesiumForUnity {
enum class Cesium3DTilesetLoadType;
}
namespace DotNet::System {
class String;
}

namespace DotNet::CesiumForUnity {

struct Cesium3DTilesetLoadFailureDetails {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Cesium3DTilesetLoadFailureDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Cesium3DTilesetLoadFailureDetails(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_lQ2_FlEU3TadAE4hjbl4Mw)(void* tileset, ::std::uint32_t type, ::std::int64_t httpStatusCode, void* message, void** reinteropException);
  public: Cesium3DTilesetLoadFailureDetails(const ::DotNet::CesiumForUnity::Cesium3DTileset& tileset, ::DotNet::CesiumForUnity::Cesium3DTilesetLoadType type, ::std::int64_t httpStatusCode, const ::DotNet::System::String& message);
};

} // namespace DotNet::CesiumForUnity


