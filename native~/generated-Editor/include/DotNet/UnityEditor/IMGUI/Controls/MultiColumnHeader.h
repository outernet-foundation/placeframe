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

class MultiColumnHeader {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit MultiColumnHeader(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: MultiColumnHeader(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::int32_t (*Property_get_sortedColumnIndex)(void* thiz, void** reinteropException);
  public: ::std::int32_t sortedColumnIndex() const;
  private: static void (*Property_set_sortedColumnIndex)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void sortedColumnIndex(::std::int32_t value) const;
  private: static ::std::uint8_t (*CallIsSortedAscending_ZiJhFqE0LPDoV__RgQlNVpQ)(void* thiz, ::std::int32_t columnIndex, void** reinteropException);
  public: bool IsSortedAscending(::std::int32_t columnIndex) const;
};

} // namespace DotNet::UnityEditor::IMGUI::Controls


