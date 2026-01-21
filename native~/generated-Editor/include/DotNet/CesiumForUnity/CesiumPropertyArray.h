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
namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}
namespace DotNet::CesiumForUnity {
class CesiumMetadataValue;
}
namespace DotNet::System {
template <typename T0> class Array1;
}

namespace DotNet::CesiumForUnity {

class CesiumPropertyArray {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumPropertyArray(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumPropertyArray(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumPropertyArray();
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_elementValueType)(void* thiz, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValueType elementValueType() const;
  private: static void (*Property_set_elementValueType)(void* thiz, const ::DotNet::CesiumForUnity::CesiumMetadataValueType* value, void** reinteropException);
  public: void elementValueType(const ::DotNet::CesiumForUnity::CesiumMetadataValueType& value) const;
  private: static void* (*Property_get_values)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue> values() const;
  private: static void (*Property_set_values)(void* thiz, void* value, void** reinteropException);
  public: void values(const ::DotNet::System::Array1<::DotNet::CesiumForUnity::CesiumMetadataValue>& value) const;
};

} // namespace DotNet::CesiumForUnity


