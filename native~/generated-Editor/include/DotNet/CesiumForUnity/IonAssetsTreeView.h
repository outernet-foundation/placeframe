#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include "IonAssetsTreeViewImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEditor::IMGUI::Controls {
class TreeViewState;
}
namespace DotNet::UnityEditor::IMGUI::Controls {
class TreeView;
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

namespace DotNet::CesiumForUnity {

class IonAssetsTreeView {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit IonAssetsTreeView(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: IonAssetsTreeView(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_bk3kO2aTAFaE0GWD9sxbig)(void* assetsTreeState, void** reinteropException);
  public: IonAssetsTreeView(const ::DotNet::UnityEditor::IMGUI::Controls::TreeViewState& assetsTreeState);
  public: operator ::DotNet::UnityEditor::IMGUI::Controls::TreeView() const;
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
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::IonAssetsTreeViewImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


