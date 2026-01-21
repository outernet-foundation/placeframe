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
namespace DotNet::System {
class Exception;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::Reinterop {

class ReinteropException {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit ReinteropException(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: ReinteropException(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_XwA9a8yCTL1RNh1m2OT3bA)(void* message, void** reinteropException);
  public: ReinteropException(const ::DotNet::System::String& message);
  public: operator ::DotNet::System::Exception() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_Message)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String Message() const;
};

} // namespace DotNet::Reinterop


