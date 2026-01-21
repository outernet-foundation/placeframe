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

namespace DotNet::CesiumForUnity {

class AssetTroubleshootingDetails {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit AssetTroubleshootingDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: AssetTroubleshootingDetails(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint8_t (*Property_get_assetExistsInUserAccount)(void* thiz, void** reinteropException);
  public: bool assetExistsInUserAccount() const;
  private: static void (*Property_set_assetExistsInUserAccount)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void assetExistsInUserAccount(bool value) const;
  private: static ::std::uint8_t (*Property_get_loaded)(void* thiz, void** reinteropException);
  public: bool loaded() const;
  private: static void (*Property_set_loaded)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void loaded(bool value) const;
};

} // namespace DotNet::CesiumForUnity


