#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include "CesiumPropertyTablePropertyImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
enum class CesiumPropertyTablePropertyStatus;
}
namespace DotNet::CesiumForUnity {
class CesiumMetadataValue;
}
namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}

namespace DotNet::CesiumForUnity {

class CesiumPropertyTableProperty {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumPropertyTableProperty(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumPropertyTableProperty(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumPropertyTableProperty();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint32_t (*Property_get_status)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumPropertyTablePropertyStatus status() const;
  private: static void (*Property_set_status)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void status(::DotNet::CesiumForUnity::CesiumPropertyTablePropertyStatus value) const;
  private: static ::std::int64_t (*Property_get_size)(void* thiz, void** reinteropException);
  public: ::std::int64_t size() const;
  private: static void (*Property_set_size)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void size(::std::int64_t value) const;
  private: static ::std::int64_t (*Property_get_arraySize)(void* thiz, void** reinteropException);
  public: ::std::int64_t arraySize() const;
  private: static void (*Property_set_arraySize)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void arraySize(::std::int64_t value) const;
  private: static ::std::uint8_t (*Property_get_isNormalized)(void* thiz, void** reinteropException);
  public: bool isNormalized() const;
  private: static void (*Property_set_isNormalized)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void isNormalized(bool value) const;
  private: static void* (*Property_get_offset)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValue offset() const;
  private: static void (*Property_set_offset)(void* thiz, void* value, void** reinteropException);
  public: void offset(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const;
  private: static void* (*Property_get_scale)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValue scale() const;
  private: static void (*Property_set_scale)(void* thiz, void* value, void** reinteropException);
  public: void scale(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const;
  private: static void* (*Property_get_min)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValue min() const;
  private: static void (*Property_set_min)(void* thiz, void* value, void** reinteropException);
  public: void min(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const;
  private: static void* (*Property_get_max)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValue max() const;
  private: static void (*Property_set_max)(void* thiz, void* value, void** reinteropException);
  public: void max(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const;
  private: static void* (*Property_get_noData)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValue noData() const;
  private: static void (*Property_set_noData)(void* thiz, void* value, void** reinteropException);
  public: void noData(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const;
  private: static void* (*Property_get_defaultValue)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValue defaultValue() const;
  private: static void (*Property_set_defaultValue)(void* thiz, void* value, void** reinteropException);
  public: void defaultValue(const ::DotNet::CesiumForUnity::CesiumMetadataValue& value) const;
  private: static void (*Property_get_valueType)(void* thiz, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValueType valueType() const;
  private: static void (*Property_set_valueType)(void* thiz, const ::DotNet::CesiumForUnity::CesiumMetadataValueType* value, void** reinteropException);
  public: void valueType(const ::DotNet::CesiumForUnity::CesiumMetadataValueType& value) const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumPropertyTablePropertyImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


