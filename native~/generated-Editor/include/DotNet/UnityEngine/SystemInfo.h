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
namespace DotNet::UnityEngine::Experimental::Rendering {
enum class GraphicsFormat;
}
namespace DotNet::UnityEngine::Experimental::Rendering {
enum class FormatUsage;
}

namespace DotNet::UnityEngine {

class SystemInfo {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit SystemInfo(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: SystemInfo(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*CallIsFormatSupported_DuaX37kfZJZ9DeCzoZGKPA)(::std::uint32_t format, ::std::uint32_t usage, void** reinteropException);
  public: static bool IsFormatSupported(::DotNet::UnityEngine::Experimental::Rendering::GraphicsFormat format, ::DotNet::UnityEngine::Experimental::Rendering::FormatUsage usage);
};

} // namespace DotNet::UnityEngine


