#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include "CesiumFeatureImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class String;
}
namespace DotNet::System {
template <typename T0> class Array1;
}

namespace DotNet::CesiumForUnity {

class CesiumFeature {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumFeature(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumFeature(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumFeature();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_className)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String className() const;
  private: static void (*Property_set_className)(void* thiz, void* value, void** reinteropException);
  public: void className(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_featureTableName)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String featureTableName() const;
  private: static void (*Property_set_featureTableName)(void* thiz, void* value, void** reinteropException);
  public: void featureTableName(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_properties)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Array1<::DotNet::System::String> properties() const;
  private: static void (*Property_set_properties)(void* thiz, void* value, void** reinteropException);
  public: void properties(const ::DotNet::System::Array1<::DotNet::System::String>& value) const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumFeatureImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


