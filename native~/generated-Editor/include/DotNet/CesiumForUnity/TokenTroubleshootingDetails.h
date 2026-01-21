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

namespace DotNet::CesiumForUnity {

class TokenTroubleshootingDetails {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit TokenTroubleshootingDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: TokenTroubleshootingDetails(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_token)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String token() const;
  private: static void (*Property_set_token)(void* thiz, void* value, void** reinteropException);
  public: void token(const ::DotNet::System::String& value) const;
  private: static ::std::uint8_t (*Property_get_isValid)(void* thiz, void** reinteropException);
  public: bool isValid() const;
  private: static void (*Property_set_isValid)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void isValid(bool value) const;
  private: static ::std::uint8_t (*Property_get_allowsAccessToAsset)(void* thiz, void** reinteropException);
  public: bool allowsAccessToAsset() const;
  private: static void (*Property_set_allowsAccessToAsset)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void allowsAccessToAsset(bool value) const;
  private: static ::std::uint8_t (*Property_get_associatedWithUserAccount)(void* thiz, void** reinteropException);
  public: bool associatedWithUserAccount() const;
  private: static void (*Property_set_associatedWithUserAccount)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void associatedWithUserAccount(bool value) const;
  private: static ::std::uint8_t (*Property_get_loaded)(void* thiz, void** reinteropException);
  public: bool loaded() const;
  private: static void (*Property_set_loaded)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void loaded(bool value) const;
};

} // namespace DotNet::CesiumForUnity


