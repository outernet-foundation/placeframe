#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include "CesiumFeatureIdAttributeImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::CesiumForUnity {
class CesiumFeatureIdSet;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
enum class CesiumFeatureIdAttributeStatus;
}
namespace DotNet::System {
class String;
}

namespace DotNet::CesiumForUnity {

class CesiumFeatureIdAttribute {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumFeatureIdAttribute(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumFeatureIdAttribute(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumFeatureIdAttribute();
  public: operator ::DotNet::CesiumForUnity::CesiumFeatureIdSet() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint32_t (*Property_get_status)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumFeatureIdAttributeStatus status() const;
  private: static void (*Property_set_status)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void status(::DotNet::CesiumForUnity::CesiumFeatureIdAttributeStatus value) const;
  private: static ::std::int64_t (*Property_get_featureCount)(void* thiz, void** reinteropException);
  public: ::std::int64_t featureCount() const;
  private: static void (*Property_set_featureCount)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void featureCount(::std::int64_t value) const;
  private: static void* (*Property_get_label)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String label() const;
  private: static void (*Property_set_label)(void* thiz, void* value, void** reinteropException);
  public: void label(const ::DotNet::System::String& value) const;
  private: static ::std::int64_t (*Property_get_nullFeatureId)(void* thiz, void** reinteropException);
  public: ::std::int64_t nullFeatureId() const;
  private: static void (*Property_set_nullFeatureId)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void nullFeatureId(::std::int64_t value) const;
  private: static ::std::int64_t (*Property_get_propertyTableIndex)(void* thiz, void** reinteropException);
  public: ::std::int64_t propertyTableIndex() const;
  private: static void (*Property_set_propertyTableIndex)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void propertyTableIndex(::std::int64_t value) const;
  private: static void (*CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Dispose() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumFeatureIdAttributeImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


