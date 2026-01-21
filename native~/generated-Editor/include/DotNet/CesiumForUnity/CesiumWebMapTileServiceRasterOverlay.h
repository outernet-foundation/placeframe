#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumWebMapTileServiceRasterOverlayImpl.h"

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
namespace DotNet::System::Collections::Generic {
template <typename T0> class List1;
}
namespace DotNet::CesiumForUnity {
enum class CesiumWebMapTileServiceRasterOverlayProjection;
}
namespace DotNet::UnityEngine {
class Coroutine;
}
namespace DotNet::System::Collections {
class IEnumerator;
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

class CesiumWebMapTileServiceRasterOverlay {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumWebMapTileServiceRasterOverlay(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumWebMapTileServiceRasterOverlay(std::nullptr_t) noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::CesiumForUnity::CesiumRasterOverlay() const;
  public: operator ::DotNet::UnityEngine::MonoBehaviour() const;
  public: operator ::DotNet::UnityEngine::Behaviour() const;
  public: operator ::DotNet::UnityEngine::Component() const;
  public: operator ::DotNet::UnityEngine::Object() const;
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_baseUrl)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String baseUrl() const;
  private: static void (*Property_set_baseUrl)(void* thiz, void* value, void** reinteropException);
  public: void baseUrl(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_layer)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String layer() const;
  private: static void (*Property_set_layer)(void* thiz, void* value, void** reinteropException);
  public: void layer(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_style)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String style() const;
  private: static void (*Property_set_style)(void* thiz, void* value, void** reinteropException);
  public: void style(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_format)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String format() const;
  private: static void (*Property_set_format)(void* thiz, void* value, void** reinteropException);
  public: void format(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_tileMatrixSetID)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String tileMatrixSetID() const;
  private: static void (*Property_set_tileMatrixSetID)(void* thiz, void* value, void** reinteropException);
  public: void tileMatrixSetID(const ::DotNet::System::String& value) const;
  private: static void* (*Property_get_tileMatrixSetLabelPrefix)(void* thiz, void** reinteropException);
  public: ::DotNet::System::String tileMatrixSetLabelPrefix() const;
  private: static void (*Property_set_tileMatrixSetLabelPrefix)(void* thiz, void* value, void** reinteropException);
  public: void tileMatrixSetLabelPrefix(const ::DotNet::System::String& value) const;
  private: static ::std::uint8_t (*Property_get_specifyTileMatrixSetLabels)(void* thiz, void** reinteropException);
  public: bool specifyTileMatrixSetLabels() const;
  private: static void (*Property_set_specifyTileMatrixSetLabels)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void specifyTileMatrixSetLabels(bool value) const;
  private: static void* (*Property_get_tileMatrixSetLabels)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::List1<::DotNet::System::String> tileMatrixSetLabels() const;
  private: static void (*Property_set_tileMatrixSetLabels)(void* thiz, void* value, void** reinteropException);
  public: void tileMatrixSetLabels(const ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>& value) const;
  private: static ::std::uint32_t (*Property_get_projection)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlayProjection projection() const;
  private: static void (*Property_set_projection)(void* thiz, ::std::uint32_t value, void** reinteropException);
  public: void projection(::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlayProjection value) const;
  private: static ::std::uint8_t (*Property_get_specifyTilingScheme)(void* thiz, void** reinteropException);
  public: bool specifyTilingScheme() const;
  private: static void (*Property_set_specifyTilingScheme)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void specifyTilingScheme(bool value) const;
  private: static ::std::int32_t (*Property_get_rootTilesX)(void* thiz, void** reinteropException);
  public: ::std::int32_t rootTilesX() const;
  private: static void (*Property_set_rootTilesX)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void rootTilesX(::std::int32_t value) const;
  private: static ::std::int32_t (*Property_get_rootTilesY)(void* thiz, void** reinteropException);
  public: ::std::int32_t rootTilesY() const;
  private: static void (*Property_set_rootTilesY)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void rootTilesY(::std::int32_t value) const;
  private: static double (*Property_get_rectangleEast)(void* thiz, void** reinteropException);
  public: double rectangleEast() const;
  private: static void (*Property_set_rectangleEast)(void* thiz, double value, void** reinteropException);
  public: void rectangleEast(double value) const;
  private: static double (*Property_get_rectangleSouth)(void* thiz, void** reinteropException);
  public: double rectangleSouth() const;
  private: static void (*Property_set_rectangleSouth)(void* thiz, double value, void** reinteropException);
  public: void rectangleSouth(double value) const;
  private: static double (*Property_get_rectangleWest)(void* thiz, void** reinteropException);
  public: double rectangleWest() const;
  private: static void (*Property_set_rectangleWest)(void* thiz, double value, void** reinteropException);
  public: void rectangleWest(double value) const;
  private: static double (*Property_get_rectangleNorth)(void* thiz, void** reinteropException);
  public: double rectangleNorth() const;
  private: static void (*Property_set_rectangleNorth)(void* thiz, double value, void** reinteropException);
  public: void rectangleNorth(double value) const;
  private: static ::std::uint8_t (*Property_get_specifyZoomLevels)(void* thiz, void** reinteropException);
  public: bool specifyZoomLevels() const;
  private: static void (*Property_set_specifyZoomLevels)(void* thiz, ::std::uint8_t value, void** reinteropException);
  public: void specifyZoomLevels(bool value) const;
  private: static ::std::int32_t (*Property_get_minimumLevel)(void* thiz, void** reinteropException);
  public: ::std::int32_t minimumLevel() const;
  private: static void (*Property_set_minimumLevel)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void minimumLevel(::std::int32_t value) const;
  private: static ::std::int32_t (*Property_get_maximumLevel)(void* thiz, void** reinteropException);
  public: ::std::int32_t maximumLevel() const;
  private: static void (*Property_set_maximumLevel)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void maximumLevel(::std::int32_t value) const;
  private: static ::std::int32_t (*Property_get_tileWidth)(void* thiz, void** reinteropException);
  public: ::std::int32_t tileWidth() const;
  private: static void (*Property_set_tileWidth)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void tileWidth(::std::int32_t value) const;
  private: static ::std::int32_t (*Property_get_tileHeight)(void* thiz, void** reinteropException);
  public: ::std::int32_t tileHeight() const;
  private: static void (*Property_set_tileHeight)(void* thiz, ::std::int32_t value, void** reinteropException);
  public: void tileHeight(::std::int32_t value) const;
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
  public: bool operator==(const CesiumWebMapTileServiceRasterOverlay& rhs) const;
  public: bool operator==(std::nullptr_t) const;
  private: static ::std::uint8_t (*Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException);
  private: static bool op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y);
  public: bool operator!=(const ::DotNet::UnityEngine::Object& rhs) const;
  public: bool operator!=(const CesiumWebMapTileServiceRasterOverlay& rhs) const;
  public: bool operator!=(std::nullptr_t) const;
  private: static ::std::int32_t (*CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::std::int32_t GetInstanceID() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::CesiumWebMapTileServiceRasterOverlayImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity


