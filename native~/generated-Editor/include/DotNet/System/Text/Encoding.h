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
namespace DotNet::System::Text {
class Encoding;
}
namespace DotNet::System {
class String;
}

namespace DotNet::System::Text {

class Encoding {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Encoding(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Encoding(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_UTF8)(void** reinteropException);
  public: static ::DotNet::System::Text::Encoding UTF8();
  private: static void* (*CallGetString_J_gIxYGOW0ecDuybXJZsCw)(void* thiz, ::std::uint8_t* bytes, ::std::int32_t byteCount, void** reinteropException);
  public: ::DotNet::System::String GetString(::std::uint8_t* bytes, ::std::int32_t byteCount) const;
};

} // namespace DotNet::System::Text


