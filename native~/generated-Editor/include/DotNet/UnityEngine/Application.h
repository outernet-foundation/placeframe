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
enum class RuntimePlatform;
}

namespace DotNet::UnityEngine {

class Application {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Application(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Application(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_temporaryCachePath)(void** reinteropException);
  public: static ::DotNet::System::String temporaryCachePath();
  private: static void* (*Property_get_version)(void** reinteropException);
  public: static ::DotNet::System::String version();
  private: static void* (*Property_get_unityVersion)(void** reinteropException);
  public: static ::DotNet::System::String unityVersion();
  private: static ::std::uint32_t (*Property_get_platform)(void** reinteropException);
  public: static ::DotNet::UnityEngine::RuntimePlatform platform();
  private: static void* (*Property_get_productName)(void** reinteropException);
  public: static ::DotNet::System::String productName();
  private: static ::std::uint8_t (*Property_get_isEditor)(void** reinteropException);
  public: static bool isEditor();
  private: static void (*CallOpenURL_i4__FgVIR5VYHO4KBzPBwNQ)(void* url, void** reinteropException);
  public: static void OpenURL(const ::DotNet::System::String& url);
};

} // namespace DotNet::UnityEngine


