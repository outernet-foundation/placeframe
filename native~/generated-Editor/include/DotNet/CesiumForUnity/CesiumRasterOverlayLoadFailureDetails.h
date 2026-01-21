#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::CesiumForUnity {
class CesiumRasterOverlay;
}
namespace DotNet::CesiumForUnity {
enum class CesiumRasterOverlayLoadType;
}
namespace DotNet::System {
class String;
}

namespace DotNet::CesiumForUnity {

struct CesiumRasterOverlayLoadFailureDetails {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumRasterOverlayLoadFailureDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumRasterOverlayLoadFailureDetails(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct___R__AqUOiZnUHIgxRnspXXw)(void* overlay, ::std::uint32_t type, ::std::int64_t httpStatusCode, void* message, void** reinteropException);
  public: CesiumRasterOverlayLoadFailureDetails(const ::DotNet::CesiumForUnity::CesiumRasterOverlay& overlay, ::DotNet::CesiumForUnity::CesiumRasterOverlayLoadType type, ::std::int64_t httpStatusCode, const ::DotNet::System::String& message);
};

} // namespace DotNet::CesiumForUnity


