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

class Helpers {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Helpers(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Helpers(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  public: template <typename T>
  static ::DotNet::System::String ToString(const T& value);
  private: static void* (*CallToString__8pn__Nas4aiRxhf1NkpeKg)(::std::uint32_t value, void** reinteropException);
};

} // namespace DotNet::CesiumForUnity


