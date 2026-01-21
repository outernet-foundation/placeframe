#include <DotNet/CesiumForUnity/CesiumEditorUtility.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/System/String.h>
#include <DotNet/CesiumForUnity/CesiumIonRasterOverlay.h>



namespace DotNet::CesiumForUnity {

void* (*DotNet::CesiumForUnity::CesiumEditorUtility::CallFindFirstTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::Cesium3DTileset CesiumEditorUtility::FindFirstTileset() {
    void* reinteropException = nullptr;
    auto result = CallFindFirstTileset_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumEditorUtility::CallFindFirstTilesetWithAssetID_OUsZiF60__hSy6sWtVPSwsA)(::std::int64_t assetID, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::Cesium3DTileset CesiumEditorUtility::FindFirstTilesetWithAssetID(::std::int64_t assetID) {
    void* reinteropException = nullptr;
    auto result = CallFindFirstTilesetWithAssetID_OUsZiF60__hSy6sWtVPSwsA(assetID, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumEditorUtility::CallCreateTileset_jsvXjE1xIXP0dz0Yem4Nag)(void* name, ::std::int64_t assetID, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::Cesium3DTileset CesiumEditorUtility::CreateTileset(const ::DotNet::System::String& name, ::std::int64_t assetID) {
    void* reinteropException = nullptr;
    auto result = CallCreateTileset_jsvXjE1xIXP0dz0Yem4Nag(name.GetHandle().GetRaw(), assetID, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumEditorUtility::CallAddBaseOverlayToTileset_GE91HI1OIybUlB1E__yYJCQ)(void* tileset, ::std::int64_t assetID, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonRasterOverlay CesiumEditorUtility::AddBaseOverlayToTileset(const ::DotNet::CesiumForUnity::Cesium3DTileset& tileset, ::std::int64_t assetID) {
    void* reinteropException = nullptr;
    auto result = CallAddBaseOverlayToTileset_GE91HI1OIybUlB1E__yYJCQ(tileset.GetHandle().GetRaw(), assetID, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::CesiumForUnity


