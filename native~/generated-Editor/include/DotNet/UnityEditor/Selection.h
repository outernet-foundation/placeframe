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
class GameObject;
}

namespace DotNet::UnityEditor {

class Selection {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Selection(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Selection(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_activeGameObject)(void** reinteropException);
  public: static ::DotNet::UnityEngine::GameObject activeGameObject();
  private: static void (*Property_set_activeGameObject)(void* value, void** reinteropException);
  public: static void activeGameObject(const ::DotNet::UnityEngine::GameObject& value);
};

} // namespace DotNet::UnityEditor


