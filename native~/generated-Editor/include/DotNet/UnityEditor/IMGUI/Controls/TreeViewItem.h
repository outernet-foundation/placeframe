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
class Object;
}

namespace DotNet::UnityEditor::IMGUI::Controls {

class TreeViewItem {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit TreeViewItem(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: TreeViewItem(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_fAkE2H7EjTzReHiM2XHBPA)(::std::int32_t id, ::std::int32_t depth, void* displayName, void** reinteropException);
  public: TreeViewItem(::std::int32_t id, ::std::int32_t depth, const ::DotNet::System::String& displayName);
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_id)(void* thiz, void** reinteropException);
  public: ::std::int32_t id() const;
  private: static void (*Property_set_id)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void id(::std::int32_t value) const;
};

} // namespace DotNet::UnityEditor::IMGUI::Controls


