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
namespace DotNet::UnityEditor {
class CallbackFunction;
}

namespace DotNet::UnityEditor {

class EditorApplication {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit EditorApplication(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: EditorApplication(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*Property_get_isPlaying)(void** reinteropException);
  public: static bool isPlaying();
  private: static void (*Property_set_isPlaying)(::std::uint8_t value, void** reinteropException);
  public: static void isPlaying(bool value);
  private: static ::std::uint8_t (*CallExecuteMenuItem__mTAWffFaNJNxtE3VLYhxw)(void* menuItemPath, void** reinteropException);
  public: static bool ExecuteMenuItem(const ::DotNet::System::String& menuItemPath);
  private: static void* (*Field_get_update)(void** reinteropException);
  private: static void (*Field_set_update)(void* value, void** reinteropException);
  public: static ::DotNet::UnityEditor::CallbackFunction update();
  public: static void update(const ::DotNet::UnityEditor::CallbackFunction& value);
};

} // namespace DotNet::UnityEditor


