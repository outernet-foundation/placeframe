#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::CesiumForUnity {
class Cesium3DTileset;
}
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumIonRasterOverlay;
}

namespace DotNet::CesiumForUnity {

class CesiumEditorUtility {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: CesiumEditorUtility() = delete;
  private: static void* (*CallFindFirstTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: static ::DotNet::CesiumForUnity::Cesium3DTileset FindFirstTileset();
  private: static void* (*CallFindFirstTilesetWithAssetID_OUsZiF60__hSy6sWtVPSwsA)(::std::int64_t assetID, void** reinteropException);
  public: static ::DotNet::CesiumForUnity::Cesium3DTileset FindFirstTilesetWithAssetID(::std::int64_t assetID);
  private: static void* (*CallCreateTileset_jsvXjE1xIXP0dz0Yem4Nag)(void* name, ::std::int64_t assetID, void** reinteropException);
  public: static ::DotNet::CesiumForUnity::Cesium3DTileset CreateTileset(const ::DotNet::System::String& name, ::std::int64_t assetID);
  private: static void* (*CallAddBaseOverlayToTileset_GE91HI1OIybUlB1E__yYJCQ)(void* tileset, ::std::int64_t assetID, void** reinteropException);
  public: static ::DotNet::CesiumForUnity::CesiumIonRasterOverlay AddBaseOverlayToTileset(const ::DotNet::CesiumForUnity::Cesium3DTileset& tileset, ::std::int64_t assetID);
};

} // namespace DotNet::CesiumForUnity


