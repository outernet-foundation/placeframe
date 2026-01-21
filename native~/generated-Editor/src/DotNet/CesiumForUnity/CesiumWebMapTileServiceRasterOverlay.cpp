#include <DotNet/CesiumForUnity/CesiumWebMapTileServiceRasterOverlay.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/CesiumForUnity/CesiumRasterOverlay.h>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/CesiumForUnity/CesiumWebMapTileServiceRasterOverlayProjection.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumWebMapTileServiceRasterOverlayImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>



namespace DotNet::CesiumForUnity {

CesiumWebMapTileServiceRasterOverlay::CesiumWebMapTileServiceRasterOverlay(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumWebMapTileServiceRasterOverlay::CesiumWebMapTileServiceRasterOverlay(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumWebMapTileServiceRasterOverlay::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumWebMapTileServiceRasterOverlay::GetHandle() {
    return this->_handle;
}


CesiumWebMapTileServiceRasterOverlay::operator ::DotNet::CesiumForUnity::CesiumRasterOverlay() const {
    return ::DotNet::CesiumForUnity::CesiumRasterOverlay(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumWebMapTileServiceRasterOverlay::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumWebMapTileServiceRasterOverlay::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumWebMapTileServiceRasterOverlay::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumWebMapTileServiceRasterOverlay::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumWebMapTileServiceRasterOverlay::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_baseUrl)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::baseUrl() const {
    void* reinteropException = nullptr;
    auto result = Property_get_baseUrl((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_baseUrl)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::baseUrl(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_baseUrl((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_layer)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::layer() const {
    void* reinteropException = nullptr;
    auto result = Property_get_layer((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_layer)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::layer(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_layer((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_style)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::style() const {
    void* reinteropException = nullptr;
    auto result = Property_get_style((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_style)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::style(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_style((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_format)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::format() const {
    void* reinteropException = nullptr;
    auto result = Property_get_format((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_format)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::format(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_format((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileMatrixSetID)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::tileMatrixSetID() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileMatrixSetID((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileMatrixSetID)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::tileMatrixSetID(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_tileMatrixSetID((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileMatrixSetLabelPrefix)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::tileMatrixSetLabelPrefix() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileMatrixSetLabelPrefix((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileMatrixSetLabelPrefix)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::tileMatrixSetLabelPrefix(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_tileMatrixSetLabelPrefix((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_specifyTileMatrixSetLabels)(void* thiz, void** reinteropException) = nullptr;


bool CesiumWebMapTileServiceRasterOverlay::specifyTileMatrixSetLabels() const {
    void* reinteropException = nullptr;
    auto result = Property_get_specifyTileMatrixSetLabels((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_specifyTileMatrixSetLabels)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::specifyTileMatrixSetLabels(bool value) const {
    void* reinteropException = nullptr;
    Property_set_specifyTileMatrixSetLabels((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileMatrixSetLabels)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::System::String> CesiumWebMapTileServiceRasterOverlay::tileMatrixSetLabels() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileMatrixSetLabels((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileMatrixSetLabels)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::tileMatrixSetLabels(const ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>& value) const {
    void* reinteropException = nullptr;
    Property_set_tileMatrixSetLabels((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_projection)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlayProjection CesiumWebMapTileServiceRasterOverlay::projection() const {
    void* reinteropException = nullptr;
    auto result = Property_get_projection((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlayProjection(result);
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_projection)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::projection(::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlayProjection value) const {
    void* reinteropException = nullptr;
    Property_set_projection((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_specifyTilingScheme)(void* thiz, void** reinteropException) = nullptr;


bool CesiumWebMapTileServiceRasterOverlay::specifyTilingScheme() const {
    void* reinteropException = nullptr;
    auto result = Property_get_specifyTilingScheme((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_specifyTilingScheme)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::specifyTilingScheme(bool value) const {
    void* reinteropException = nullptr;
    Property_set_specifyTilingScheme((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rootTilesX)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::rootTilesX() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rootTilesX((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rootTilesX)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::rootTilesX(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_rootTilesX((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rootTilesY)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::rootTilesY() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rootTilesY((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rootTilesY)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::rootTilesY(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_rootTilesY((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleEast)(void* thiz, void** reinteropException) = nullptr;


double CesiumWebMapTileServiceRasterOverlay::rectangleEast() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleEast((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleEast)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::rectangleEast(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleEast((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleSouth)(void* thiz, void** reinteropException) = nullptr;


double CesiumWebMapTileServiceRasterOverlay::rectangleSouth() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleSouth((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleSouth)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::rectangleSouth(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleSouth((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleWest)(void* thiz, void** reinteropException) = nullptr;


double CesiumWebMapTileServiceRasterOverlay::rectangleWest() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleWest((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleWest)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::rectangleWest(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleWest((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_rectangleNorth)(void* thiz, void** reinteropException) = nullptr;


double CesiumWebMapTileServiceRasterOverlay::rectangleNorth() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleNorth((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_rectangleNorth)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::rectangleNorth(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleNorth((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_specifyZoomLevels)(void* thiz, void** reinteropException) = nullptr;


bool CesiumWebMapTileServiceRasterOverlay::specifyZoomLevels() const {
    void* reinteropException = nullptr;
    auto result = Property_get_specifyZoomLevels((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_specifyZoomLevels)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::specifyZoomLevels(bool value) const {
    void* reinteropException = nullptr;
    Property_set_specifyZoomLevels((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_minimumLevel)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::minimumLevel() const {
    void* reinteropException = nullptr;
    auto result = Property_get_minimumLevel((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_minimumLevel)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::minimumLevel(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_minimumLevel((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumLevel)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::maximumLevel() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumLevel((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumLevel)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::maximumLevel(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumLevel((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileWidth)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::tileWidth() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileWidth((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileWidth)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::tileWidth(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_tileWidth((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_tileHeight)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::tileHeight() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileHeight((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_tileHeight)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::tileHeight(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_tileHeight((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_materialKey)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::materialKey() const {
    void* reinteropException = nullptr;
    auto result = Property_get_materialKey((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_materialKey)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::materialKey(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_materialKey((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_showCreditsOnScreen)(void* thiz, void** reinteropException) = nullptr;


bool CesiumWebMapTileServiceRasterOverlay::showCreditsOnScreen() const {
    void* reinteropException = nullptr;
    auto result = Property_get_showCreditsOnScreen((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_showCreditsOnScreen)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::showCreditsOnScreen(bool value) const {
    void* reinteropException = nullptr;
    Property_set_showCreditsOnScreen((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


float (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumScreenSpaceError)(void* thiz, void** reinteropException) = nullptr;


float CesiumWebMapTileServiceRasterOverlay::maximumScreenSpaceError() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumScreenSpaceError((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumScreenSpaceError)(void* thiz, float value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::maximumScreenSpaceError(float value) const {
    void* reinteropException = nullptr;
    Property_set_maximumScreenSpaceError((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumTextureSize)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::maximumTextureSize() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumTextureSize((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumTextureSize)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::maximumTextureSize(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumTextureSize((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_maximumSimultaneousTileLoads)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::maximumSimultaneousTileLoads() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_maximumSimultaneousTileLoads)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::maximumSimultaneousTileLoads(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_subTileCacheBytes)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumWebMapTileServiceRasterOverlay::subTileCacheBytes() const {
    void* reinteropException = nullptr;
    auto result = Property_get_subTileCacheBytes((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_subTileCacheBytes)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::subTileCacheBytes(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_subTileCacheBytes((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::Refresh() const {
    void* reinteropException = nullptr;
    CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::AddToTileset() const {
    void* reinteropException = nullptr;
    CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::RemoveFromTileset() const {
    void* reinteropException = nullptr;
    CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumWebMapTileServiceRasterOverlay::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumWebMapTileServiceRasterOverlay::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumWebMapTileServiceRasterOverlay::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumWebMapTileServiceRasterOverlay::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumWebMapTileServiceRasterOverlay::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumWebMapTileServiceRasterOverlay::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumWebMapTileServiceRasterOverlay::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumWebMapTileServiceRasterOverlay::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumWebMapTileServiceRasterOverlay::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumWebMapTileServiceRasterOverlay::operator==(const CesiumWebMapTileServiceRasterOverlay& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumWebMapTileServiceRasterOverlay::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumWebMapTileServiceRasterOverlay::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumWebMapTileServiceRasterOverlay::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumWebMapTileServiceRasterOverlay::operator!=(const CesiumWebMapTileServiceRasterOverlay& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumWebMapTileServiceRasterOverlay::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumWebMapTileServiceRasterOverlay::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumWebMapTileServiceRasterOverlay::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*CesiumWebMapTileServiceRasterOverlay::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumWebMapTileServiceRasterOverlayImpl& CesiumWebMapTileServiceRasterOverlay::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumWebMapTileServiceRasterOverlayImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumWebMapTileServiceRasterOverlay_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumWebMapTileServiceRasterOverlayImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumWebMapTileServiceRasterOverlay_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumWebMapTileServiceRasterOverlayImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumWebMapTileServiceRasterOverlay_AddToTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumWebMapTileServiceRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->AddToTileset(wrapper, ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(tileset)));
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumWebMapTileServiceRasterOverlay_RemoveFromTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumWebMapTileServiceRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumWebMapTileServiceRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->RemoveFromTileset(wrapper, ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(tileset)));
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

