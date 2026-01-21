#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumIonRasterOverlayImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::CesiumForUnity {
class CesiumRasterOverlay;
}
namespace DotNet::UnityEngine {
class MonoBehaviour;
}
namespace DotNet::UnityEngine {
class Behaviour;
}
namespace DotNet::UnityEngine {
class Component;
}
namespace DotNet::UnityEngine {
class Object;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumIonServer;
}
namespace DotNet::System::Collections {
class IEnumerator;
}
namespace DotNet::CesiumForUnity {
class Cesium3DTileset;
}
namespace DotNet::UnityEngine {
class Coroutine;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class CesiumIonRasterOverlay {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumIonRasterOverlay(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumIonRasterOverlay(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::CesiumForUnity::CesiumRasterOverlay() const;
  public: operator ::DotNet::UnityEngine::MonoBehaviour() const;
  public: operator ::DotNet::UnityEngine::Behaviour() const;
  public: operator ::DotNet::UnityEngine::Component() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_ionAccessToken)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String ionAccessToken() const;
  private: static void (*Property_set_ionAccessToken)(void* thiz, void* value, void** reinteropException);
  public: void ionAccessToken(const ::DotNet::System::String& value) const;
  private: static ::std::int64_t (*Property_get_ionAssetID)(void* thiz, void** reinteropException);
  public: ::std::int64_t ionAssetID() const;
  private: static void (*Property_set_ionAssetID)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void ionAssetID(::std::int64_t value) const;
  private: static void* (*Property_get_ionServer)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumIonServer ionServer() const;
  private: static void (*Property_set_ionServer)(void* thiz, void* value, void** reinteropException);
  public: void ionServer(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const;
  private: static void* (*Property_get_assetOptions)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String assetOptions() const;
  private: static void (*Property_set_assetOptions)(void* thiz, void* value, void** reinteropException);
  public: void assetOptions(const ::DotNet::System::String& value) const;
  private: static void* (*CallAddToTilesetLater_SrfNoP9IJM__ZwyysR9yJTQ)(void* thiz, void* tileset, void** reinteropException);
  public: ::DotNet::System::Collections::IEnumerator AddToTilesetLater(const ::DotNet::CesiumForUnity::Cesium3DTileset& tileset) const;
  private: static void* (*Property_get_materialKey)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String materialKey() const;
  private: static void (*Property_set_materialKey)(void* thiz, void* value, void** reinteropException);
  public: void materialKey(const ::DotNet::System::String& value) const;
  private: static ::std::uint8_t (*Property_get_showCreditsOnScreen)(void* thiz, void** reinteropException);
  public: bool showCreditsOnScreen() const;
  private: static void (*Property_set_showCreditsOnScreen)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void showCreditsOnScreen(bool value) const;
  private: static float (*Property_get_maximumScreenSpaceError)(void* thiz, void** reinteropException);
  public: float maximumScreenSpaceError() const;
  private: static void (*Property_set_maximumScreenSpaceError)(void* thiz, float value, void** reinteropException);
  public: void maximumScreenSpaceError(float value) const;
  private: static ::std::int32_t (*Property_get_maximumTextureSize)(void* thiz, void** reinteropException);
  public: ::std::int32_t maximumTextureSize() const;
  private: static void (*Property_set_maximumTextureSize)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void maximumTextureSize(::std::int32_t value) const;
  private: static ::std::int32_t (*Property_get_maximumSimultaneousTileLoads)(void* thiz, void** reinteropException);
  public: ::std::int32_t maximumSimultaneousTileLoads() const;
  private: static void (*Property_set_maximumSimultaneousTileLoads)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void maximumSimultaneousTileLoads(::std::int32_t value) const;
  private: static ::std::int64_t (*Property_get_subTileCacheBytes)(void* thiz, void** reinteropException);
  public: ::std::int64_t subTileCacheBytes() const;
  private: static void (*Property_set_subTileCacheBytes)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void subTileCacheBytes(::std::int64_t value) const;
  private: static void (*CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void Refresh() const;
  private: static void (*CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void AddToTileset() const;
  private: static void (*CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void RemoveFromTileset() const;
  private: static void* (*CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException);
  public: ::DotNet::UnityEngine::Coroutine StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const;
  private: static ::std::uint8_t (*Property_get_enabled)(void* thiz, void** reinteropException);
  public: bool enabled() const;
  private: static void (*Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void enabled(bool value) const;
  private: static void* (*Property_get_gameObject)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::GameObject gameObject() const;
  private: static void* (*Property_get_transform)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Transform transform() const;
  public: template <typename T>
  T GetComponent() const;
  private: static void* (*CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException);
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
  public: bool operator==(const CesiumIonRasterOverlay& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const CesiumIonRasterOverlay& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumIonRasterOverlayImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


