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
class Object;
}

namespace DotNet::UnityEditor {

class EditorUtility {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit EditorUtility(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: EditorUtility(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void (*CallSetDirty_byPIQUdz9akDU2__zoHd1tg)(void* target, void** reinteropException);
  public: static void SetDirty(const ::DotNet::UnityEngine::Object& target);
};

} // namespace DotNet::UnityEditor


