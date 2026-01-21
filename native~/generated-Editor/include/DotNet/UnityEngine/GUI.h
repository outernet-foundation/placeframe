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
namespace DotNet::UnityEngine {
struct Rect;
}
namespace DotNet::System {
class String;
}

namespace DotNet::UnityEngine {

class GUI {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit GUI(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: GUI(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallLabel_iRU7t71QqJzkr4BTYehN9A)(const ::DotNet::UnityEngine::Rect* position, void* text, void** reinteropException);
  public: static void Label(const ::DotNet::UnityEngine::Rect& position, const ::DotNet::System::String& text);
};

} // namespace DotNet::UnityEngine


