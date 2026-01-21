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

namespace DotNet::System::Collections::Generic {

template <typename T0, typename T1>
struct KeyValuePair2;

template <> struct KeyValuePair2<::DotNet::System::String, ::DotNet::System::String> {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit KeyValuePair2(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: KeyValuePair2(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Property_get_Key)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String Key() const;
  private: static void* (*Property_get_Value)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String Value() const;
};

} // namespace DotNet::System::Collections::Generic


