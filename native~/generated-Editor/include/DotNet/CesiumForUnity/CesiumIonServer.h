#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
class CesiumIonServer;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class CesiumIonServer {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumIonServer(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumIonServer(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_defaultServer)(void** reinteropException);
  public: static ::DotNet::CesiumForUnity::CesiumIonServer defaultServer();
  private: static void* (*Field_get_defaultIonAccessToken)(void* thiz, void** reinteropException);
  private: static void (*Field_set_defaultIonAccessToken)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String defaultIonAccessToken() const;
  public: void defaultIonAccessToken(const ::DotNet::System::String& value) const;
  private: static void* (*Field_get_defaultIonAccessTokenId)(void* thiz, void** reinteropException);
  private: static void (*Field_set_defaultIonAccessTokenId)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String defaultIonAccessTokenId() const;
  public: void defaultIonAccessTokenId(const ::DotNet::System::String& value) const;
  private: static void* (*Field_get_apiUrl)(void* thiz, void** reinteropException);
  private: static void (*Field_set_apiUrl)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String apiUrl() const;
  public: void apiUrl(const ::DotNet::System::String& value) const;
  private: static void* (*Field_get_serverUrl)(void* thiz, void** reinteropException);
  private: static void (*Field_set_serverUrl)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String serverUrl() const;
  public: void serverUrl(const ::DotNet::System::String& value) const;
  private: static ::std::int64_t (*Field_get_oauth2ApplicationID)(void* thiz, void** reinteropException);
  private: static void (*Field_set_oauth2ApplicationID)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: ::std::int64_t oauth2ApplicationID() const;
  public: void oauth2ApplicationID(::std::int64_t value) const;
  private: static void* (*Field_get_serverUrlThatIsLoadingApiUrl)(void* thiz, void** reinteropException);
  private: static void (*Field_set_serverUrlThatIsLoadingApiUrl)(void* thiz, void* value, void** reinteropException);
  public: ::DotNet::System::String serverUrlThatIsLoadingApiUrl() const;
  public: void serverUrlThatIsLoadingApiUrl(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_name)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String name() const;
  private: static void (*Property_set_name)(void* thiz, void* value, void** reinteropException);
  public: void name(const ::DotNet::System::String& value) const;
  private: static ::std::uint32_t (*Property_get_hideFlags)(void* thiz, void** reinteropException);
  public: ::flags::flags<::DotNet::UnityEngine::HideFlags> hideFlags() const;
  private: static void (*Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const;
  private: static ::std::uint8_t (*Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator==(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator==(const CesiumIonServer& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const CesiumIonServer& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::CesiumForUnity


