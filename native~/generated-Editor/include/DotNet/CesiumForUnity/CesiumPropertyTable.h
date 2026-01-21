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
enum class CesiumPropertyTableStatus;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumPropertyTableProperty;
}
namespace DotNet::System::Collections::Generic {
template <typename T0, typename T1> class Dictionary2;
}

namespace DotNet::CesiumForUnity {

class CesiumPropertyTable {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumPropertyTable(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumPropertyTable(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumPropertyTable();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint32_t (*Property_get_status)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumPropertyTableStatus status() const;
  private: static void (*Property_set_status)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void status(::DotNet::CesiumForUnity::CesiumPropertyTableStatus value) const;
  private: static void* (*Property_get_name)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String name() const;
  private: static void (*Property_set_name)(void* thiz, void* value, void** reinteropException);
  public: void name(const ::DotNet::System::String& value) const;
  private: static ::std::int64_t (*Property_get_count)(void* thiz, void** reinteropException);
  public: ::std::int64_t count() const;
  private: static void (*Property_set_count)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void count(::std::int64_t value) const;
  private: static void* (*Property_get_properties)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty> properties() const;
  private: static void (*Property_set_properties)(void* thiz, void* value, void** reinteropException);
  public: void properties(const ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty>& value) const;
  private: static void (*CallDisposeProperties_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void DisposeProperties() const;
};

} // namespace DotNet::CesiumForUnity


