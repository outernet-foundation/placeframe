#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "Cesium3DTilesetImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
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
namespace DotNet::CesiumForUnity {
enum class CesiumDataSource;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumIonServer;
}
namespace DotNet::UnityEngine {
class Material;
}
namespace DotNet::CesiumForUnity {
struct Cesium3DTilesetLoadFailureDetails;
}
namespace DotNet::UnityEngine {
class GameObject;
}
namespace DotNet::UnityEngine {
class Coroutine;
}
namespace DotNet::System::Collections {
class IEnumerator;
}
namespace DotNet::UnityEngine {
class Transform;
}
namespace DotNet::UnityEngine {
enum class HideFlags : uint32_t;
}

namespace DotNet::CesiumForUnity {

class Cesium3DTileset {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit Cesium3DTileset(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: Cesium3DTileset(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: Cesium3DTileset();
  public: operator ::DotNet::UnityEngine::MonoBehaviour() const;
  public: operator ::DotNet::UnityEngine::Behaviour() const;
  public: operator ::DotNet::UnityEngine::Component() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static ::std::uint32_t (*Property_get_tilesetSource)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumDataSource tilesetSource() const;
  private: static void (*Property_set_tilesetSource)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void tilesetSource(::DotNet::CesiumForUnity::CesiumDataSource value) const;
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
  private: static void* (*Property_get_url)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String url() const;
  private: static void (*Property_set_url)(void* thiz, void* value, void** reinteropException);
  public: void url(const ::DotNet::System::String& value) const;
  private: static ::std::uint8_t (*Property_get_logSelectionStats)(void* thiz, void** reinteropException);
  public: bool logSelectionStats() const;
  private: static void (*Property_set_logSelectionStats)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void logSelectionStats(bool value) const;
  private: static void* (*Property_get_opaqueMaterial)(void* thiz, void** reinteropException);
  public: ::DotNet::UnityEngine::Material opaqueMaterial() const;
  private: static void (*Property_set_opaqueMaterial)(void* thiz, void* value, void** reinteropException);
  public: void opaqueMaterial(const ::DotNet::UnityEngine::Material& value) const;
  private: static float (*Property_get_maximumScreenSpaceError)(void* thiz, void** reinteropException);
  public: float maximumScreenSpaceError() const;
  private: static void (*Property_set_maximumScreenSpaceError)(void* thiz, float value, void** reinteropException);
  public: void maximumScreenSpaceError(float value) const;
  private: static ::std::uint8_t (*Property_get_preloadAncestors)(void* thiz, void** reinteropException);
  public: bool preloadAncestors() const;
  private: static void (*Property_set_preloadAncestors)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void preloadAncestors(bool value) const;
  private: static ::std::uint8_t (*Property_get_preloadSiblings)(void* thiz, void** reinteropException);
  public: bool preloadSiblings() const;
  private: static void (*Property_set_preloadSiblings)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void preloadSiblings(bool value) const;
  private: static ::std::uint8_t (*Property_get_forbidHoles)(void* thiz, void** reinteropException);
  public: bool forbidHoles() const;
  private: static void (*Property_set_forbidHoles)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void forbidHoles(bool value) const;
  private: static ::std::uint32_t (*Property_get_maximumSimultaneousTileLoads)(void* thiz, void** reinteropException);
  public: ::std::uint32_t maximumSimultaneousTileLoads() const;
  private: static void (*Property_set_maximumSimultaneousTileLoads)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void maximumSimultaneousTileLoads(::std::uint32_t value) const;
  private: static ::std::int64_t (*Property_get_maximumCachedBytes)(void* thiz, void** reinteropException);
  public: ::std::int64_t maximumCachedBytes() const;
  private: static void (*Property_set_maximumCachedBytes)(void* thiz, ::std::int64_t value, void** reinteropException);
  public: void maximumCachedBytes(::std::int64_t value) const;
  private: static ::std::uint32_t (*Property_get_loadingDescendantLimit)(void* thiz, void** reinteropException);
  public: ::std::uint32_t loadingDescendantLimit() const;
  private: static void (*Property_set_loadingDescendantLimit)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void loadingDescendantLimit(::std::uint32_t value) const;
  private: static ::std::uint8_t (*Property_get_enableFrustumCulling)(void* thiz, void** reinteropException);
  public: bool enableFrustumCulling() const;
  private: static void (*Property_set_enableFrustumCulling)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void enableFrustumCulling(bool value) const;
  private: static ::std::uint8_t (*Property_get_enableFogCulling)(void* thiz, void** reinteropException);
  public: bool enableFogCulling() const;
  private: static void (*Property_set_enableFogCulling)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void enableFogCulling(bool value) const;
  private: static ::std::uint8_t (*Property_get_enforceCulledScreenSpaceError)(void* thiz, void** reinteropException);
  public: bool enforceCulledScreenSpaceError() const;
  private: static void (*Property_set_enforceCulledScreenSpaceError)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void enforceCulledScreenSpaceError(bool value) const;
  private: static float (*Property_get_culledScreenSpaceError)(void* thiz, void** reinteropException);
  public: float culledScreenSpaceError() const;
  private: static void (*Property_set_culledScreenSpaceError)(void* thiz, float value, void** reinteropException);
  public: void culledScreenSpaceError(float value) const;
  private: static ::std::uint8_t (*Property_get_generateSmoothNormals)(void* thiz, void** reinteropException);
  public: bool generateSmoothNormals() const;
  private: static void (*Property_set_generateSmoothNormals)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void generateSmoothNormals(bool value) const;
  private: static ::std::uint8_t (*Property_get_ignoreKhrMaterialsUnlit)(void* thiz, void** reinteropException);
  public: bool ignoreKhrMaterialsUnlit() const;
  private: static void (*Property_set_ignoreKhrMaterialsUnlit)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void ignoreKhrMaterialsUnlit(bool value) const;
  private: static ::std::uint8_t (*Property_get_createPhysicsMeshes)(void* thiz, void** reinteropException);
  public: bool createPhysicsMeshes() const;
  private: static void (*Property_set_createPhysicsMeshes)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void createPhysicsMeshes(bool value) const;
  private: static ::std::uint8_t (*Property_get_suspendUpdate)(void* thiz, void** reinteropException);
  public: bool suspendUpdate() const;
  private: static void (*Property_set_suspendUpdate)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void suspendUpdate(bool value) const;
  private: static ::std::uint8_t (*Property_get_previousSuspendUpdate)(void* thiz, void** reinteropException);
  public: bool previousSuspendUpdate() const;
  private: static void (*Property_set_previousSuspendUpdate)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void previousSuspendUpdate(bool value) const;
  private: static ::std::uint8_t (*Property_get_showTilesInHierarchy)(void* thiz, void** reinteropException);
  public: bool showTilesInHierarchy() const;
  private: static void (*Property_set_showTilesInHierarchy)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void showTilesInHierarchy(bool value) const;
  private: static ::std::uint8_t (*Property_get_updateInEditor)(void* thiz, void** reinteropException);
  public: bool updateInEditor() const;
  private: static void (*Property_set_updateInEditor)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void updateInEditor(bool value) const;
  private: static ::std::uint8_t (*Property_get_showCreditsOnScreen)(void* thiz, void** reinteropException);
  public: bool showCreditsOnScreen() const;
  private: static void (*Property_set_showCreditsOnScreen)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void showCreditsOnScreen(bool value) const;
  private: static void (*CallRecreateTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: void RecreateTileset() const;
  private: static void (*CallBroadcastCesium3DTilesetLoadFailure_EA9gid9gf99C0Ye5ZgnZYw)(void* details, void** reinteropException);
  public: static void BroadcastCesium3DTilesetLoadFailure(const ::DotNet::CesiumForUnity::Cesium3DTilesetLoadFailureDetails& details);
  private: static void (*CallBroadcastNewGameObjectCreated_PB2O3_b6vvn_5vRyfrXK8g)(void* thiz, void* go, void** reinteropException);
  public: void BroadcastNewGameObjectCreated(const ::DotNet::UnityEngine::GameObject& go) const;
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
  public: bool operator==(const Cesium3DTileset& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const Cesium3DTileset& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::Cesium3DTilesetImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


