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
class Delegate;
}

namespace DotNet::System {

class Delegate {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Delegate(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Delegate(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2);
  public: bool operator==(const ::DotNet::System::Delegate& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2);
  public: bool operator!=(const ::DotNet::System::Delegate& rhs) const;
};

} // namespace DotNet::System


