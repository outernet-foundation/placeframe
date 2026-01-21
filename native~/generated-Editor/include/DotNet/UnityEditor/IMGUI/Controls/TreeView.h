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
namespace DotNet::UnityEditor::IMGUI::Controls {
class MultiColumnHeader;
}
namespace DotNet::System {
class String;
}

namespace DotNet::UnityEditor::IMGUI::Controls {

class TreeView {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit TreeView(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: TreeView(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_multiColumnHeader)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader multiColumnHeader() const;
  private: static void (*Property_set_multiColumnHeader)(void* thiz, void* value, void** reinteropException);
  public: void multiColumnHeader(const ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader& value) const;
  private: static void* (*Property_get_searchString)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String searchString() const;
  private: static void (*Property_set_searchString)(void* thiz, void* value, void** reinteropException);
  public: void searchString(const ::DotNet::System::String& value) const;
  private: static void (*CallReload_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Reload() const;
};

} // namespace DotNet::UnityEditor::IMGUI::Controls


