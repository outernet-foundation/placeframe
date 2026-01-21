#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include "CesiumSimplePlanarEllipsoidCurveImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::CesiumForUnity {
class CesiumSimplePlanarEllipsoidCurve;
}
namespace DotNet::CesiumForUnity {
class CesiumEllipsoid;
}

namespace DotNet::CesiumForUnity {

class CesiumSimplePlanarEllipsoidCurve {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumSimplePlanarEllipsoidCurve(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumSimplePlanarEllipsoidCurve(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallFromCenteredFixedCoordinates_Xlu0WX31sapbYyKKJDYoaw)(void* ellipsoid, const ::DotNet::Unity::Mathematics::double3* sourceEcef, const ::DotNet::Unity::Mathematics::double3* destinationEcef, void** reinteropException);
  public: static ::DotNet::CesiumForUnity::CesiumSimplePlanarEllipsoidCurve FromCenteredFixedCoordinates(const ::DotNet::CesiumForUnity::CesiumEllipsoid& ellipsoid, const ::DotNet::Unity::Mathematics::double3& sourceEcef, const ::DotNet::Unity::Mathematics::double3& destinationEcef);
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumSimplePlanarEllipsoidCurveImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


