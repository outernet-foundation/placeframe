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
namespace DotNet::CesiumForUnity {
class CesiumIonServerManager;
}
namespace DotNet::UnityEditor {
template <typename T0> class ScriptableSingleton1;
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
namespace DotNet::CesiumForUnity {
class CesiumIonSession;
}
namespace DotNet::System {
class String;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class CesiumIonServerManager {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumIonServerManager(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumIonServerManager(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_current)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonServer current() const;
  private: static void (*Property_set_current)(void* thiz, void* value, void** reinteropException);
  public: void current(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const;
  private: static void* (*Property_get_currentSession)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonSession currentSession() const;
  private: static void* (*CallGetSession_ouKG7YNdV4bUJcBV0W3dBA)(void* thiz, void* server, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonSession GetSession(const ::DotNet::CesiumForUnity::CesiumIonServer& server) const;
  private: static void* (*CallGetUserAccessToken_ouKG7YNdV4bUJcBV0W3dBA)(void* thiz, void* server, void** reinteropException);
  public: ::DotNet::System::String GetUserAccessToken(const ::DotNet::CesiumForUnity::CesiumIonServer& server) const;
  private: static void (*CallSetUserAccessToken_i1OZfOwTwhgNuaqLRy9vZQ)(void* thiz, void* server, void* token, void** reinteropException);
  public: void SetUserAccessToken(const ::DotNet::CesiumForUnity::CesiumIonServer& server, const ::DotNet::System::String& token) const;
  private: static void* (*Property_get_instance)(void** reinteropException);
  public: static ::DotNet::CesiumForUnity::CesiumIonServerManager instance();
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
  public: bool operator==(const CesiumIonServerManager& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const CesiumIonServerManager& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
};

} // namespace DotNet::CesiumForUnity


