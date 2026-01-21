#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class String;
}
namespace DotNet::System::Collections::Generic {
template <typename T0, typename T1> struct KeyValuePair2;
}

namespace DotNet::System::Collections::Generic {

struct Enumerator0 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Enumerator0(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Enumerator0(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Property_get_Current)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::KeyValuePair2<::DotNet::System::String, ::DotNet::System::String> Current() const;
  private: static ::std::uint8_t (*CallMoveNext_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: bool MoveNext() const;
};

} // namespace DotNet::System::Collections::Generic


