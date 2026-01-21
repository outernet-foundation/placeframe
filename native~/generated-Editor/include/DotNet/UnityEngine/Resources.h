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

namespace DotNet::UnityEngine {

class Resources {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Resources(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Resources(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  public: template <typename T>
  static T Load(const ::DotNet::System::String& path);
  private: static void* (*CallLoad_rsjQbSk78vk9BZ1CvfZ2fw)(void* path, void** reinteropException);
  private: static void* (*CallLoad_Sx8S__RAskKFDmQvk60XduA)(void* path, void** reinteropException);
};

} // namespace DotNet::UnityEngine


