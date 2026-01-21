#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include "CesiumIonSessionImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
class CesiumIonServer;
}
namespace DotNet::CesiumForUnity {
class QuickAddItem;
}
namespace DotNet::System::Collections::Generic {
template <typename T0> class List1;
}

namespace DotNet::CesiumForUnity {

class CesiumIonSession {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumIonSession(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumIonSession(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_server)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonServer server() const;
  private: static void (*Property_set_server)(void* thiz, void* value, void** reinteropException);
  public: void server(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const;
  private: static ::std::uint8_t (*CallIsConnected_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: bool IsConnected() const;
  private: static void* (*CallGetQuickAddItems_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::QuickAddItem> GetQuickAddItems() const;
  private: static void (*CallBroadcastConnectionUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void BroadcastConnectionUpdate() const;
  private: static void (*CallBroadcastAssetsUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void BroadcastAssetsUpdate() const;
  private: static void (*CallBroadcastProfileUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void BroadcastProfileUpdate() const;
  private: static void (*CallBroadcastTokensUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void BroadcastTokensUpdate() const;
  private: static void (*CallBroadcastDefaultsUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void BroadcastDefaultsUpdate() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumIonSessionImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


