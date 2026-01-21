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
namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::System {
class String;
}

namespace DotNet::CesiumForUnity {

class CesiumSampleHeightResult {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumSampleHeightResult(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumSampleHeightResult(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumSampleHeightResult();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_longitudeLatitudeHeightPositions)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3> longitudeLatitudeHeightPositions() const;
  private: static void (*Property_set_longitudeLatitudeHeightPositions)(void* thiz, void* value, void** reinteropException);
  public: void longitudeLatitudeHeightPositions(const ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>& value) const;
  private: static void* (*Property_get_sampleSuccess)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<bool> sampleSuccess() const;
  private: static void (*Property_set_sampleSuccess)(void* thiz, void* value, void** reinteropException);
  public: void sampleSuccess(const ::DotNet::System::Array1<bool>& value) const;
  private: static void* (*Property_get_warnings)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::System::String> warnings() const;
  private: static void (*Property_set_warnings)(void* thiz, void* value, void** reinteropException);
  public: void warnings(const ::DotNet::System::Array1<::DotNet::System::String>& value) const;
};

} // namespace DotNet::CesiumForUnity


