#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::System {
class String;
}
namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System::Collections::Generic {
struct Enumerator0;
}
namespace DotNet::CesiumForUnity {
class CesiumPropertyTableProperty;
}

namespace DotNet::System::Collections::Generic {

template <typename T0, typename T1>
class Dictionary2;

template <> class Dictionary2<::DotNet::System::String, ::DotNet::System::String> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Dictionary2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Dictionary2(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallGetEnumerator_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::Enumerator0 GetEnumerator() const;
};

template <typename T0, typename T1>
class Dictionary2;

template <> class Dictionary2<::DotNet::System::String, ::DotNet::CesiumForUnity::CesiumPropertyTableProperty> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Dictionary2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Dictionary2(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_WGe5Irde9C7cSq7hDUfI5Q)(::std::int32_t capacity, void** reinteropException);
  public: Dictionary2(::std::int32_t capacity);
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallAdd_zclURTnfSFbfrVxWQq_LWQ)(void* thiz, void* key, void* value, void** reinteropException);
  public: void Add(const ::DotNet::System::String& key, const ::DotNet::CesiumForUnity::CesiumPropertyTableProperty& value) const;
};

} // namespace DotNet::System::Collections::Generic


