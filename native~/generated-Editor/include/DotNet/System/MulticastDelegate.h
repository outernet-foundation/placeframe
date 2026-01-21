#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Delegate;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class MulticastDelegate;
}

namespace DotNet::System {

class MulticastDelegate {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit MulticastDelegate(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: MulticastDelegate(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Delegate() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*Callop_Equality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2);
  public: bool operator==(const ::DotNet::System::MulticastDelegate& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality__iYzpyUo7S__gDd8L5jFzrg)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::System::MulticastDelegate& d1, const ::DotNet::System::MulticastDelegate& d2);
  public: bool operator!=(const ::DotNet::System::MulticastDelegate& rhs) const;
  private: static ::std::uint8_t (*Callop_Equality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2);
  public: bool operator==(const ::DotNet::System::Delegate& rhs) const;
  private: static ::std::uint8_t (*Callop_Inequality_a0RmOPC1vpOfulhhfnafBA)(void* d1, void* d2, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::System::Delegate& d1, const ::DotNet::System::Delegate& d2);
  public: bool operator!=(const ::DotNet::System::Delegate& rhs) const;
};

} // namespace DotNet::System


