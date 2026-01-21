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
namespace DotNet::System {
class String;
}

namespace DotNet::CesiumForUnity {

class HeaderEntry {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit HeaderEntry(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: HeaderEntry(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Field_get_Name)(void* thiz, void** reinteropException);
  private: static void (*Field_set_Name)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String Name() const;
  public: void Name(const ::DotNet::System::String& value) const;
  private: static void* (*Field_get_Value)(void* thiz, void** reinteropException);
  private: static void (*Field_set_Value)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String Value() const;
  public: void Value(const ::DotNet::System::String& value) const;
};

} // namespace DotNet::CesiumForUnity


