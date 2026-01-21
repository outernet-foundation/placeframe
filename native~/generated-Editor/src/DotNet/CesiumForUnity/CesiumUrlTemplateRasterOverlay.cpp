#include <DotNet/CesiumForUnity/CesiumUrlTemplateRasterOverlay.h>
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
#include <DotNet/CesiumForUnity/CesiumUrlTemplateRasterOverlayProjection.h>
#include <DotNet/CesiumForUnity/HeaderEntry.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumUrlTemplateRasterOverlayImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>



namespace DotNet::CesiumForUnity {

CesiumUrlTemplateRasterOverlay::CesiumUrlTemplateRasterOverlay(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumUrlTemplateRasterOverlay::CesiumUrlTemplateRasterOverlay(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumUrlTemplateRasterOverlay::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumUrlTemplateRasterOverlay::GetHandle() {
    return this->_handle;
}


CesiumUrlTemplateRasterOverlay::operator ::DotNet::CesiumForUnity::CesiumRasterOverlay() const {
    return ::DotNet::CesiumForUnity::CesiumRasterOverlay(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumUrlTemplateRasterOverlay::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumUrlTemplateRasterOverlay::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumUrlTemplateRasterOverlay::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumUrlTemplateRasterOverlay::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumUrlTemplateRasterOverlay::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_templateUrl)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumUrlTemplateRasterOverlay::templateUrl() const {
    void* reinteropException = nullptr;
    auto result = Property_get_templateUrl((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_templateUrl)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::templateUrl(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_templateUrl((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_projection)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlayProjection CesiumUrlTemplateRasterOverlay::projection() const {
    void* reinteropException = nullptr;
    auto result = Property_get_projection((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlayProjection(result);
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_projection)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::projection(::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlayProjection value) const {
    void* reinteropException = nullptr;
    Property_set_projection((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_specifyTilingScheme)(void* thiz, void** reinteropException) = nullptr;


bool CesiumUrlTemplateRasterOverlay::specifyTilingScheme() const {
    void* reinteropException = nullptr;
    auto result = Property_get_specifyTilingScheme((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_specifyTilingScheme)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::specifyTilingScheme(bool value) const {
    void* reinteropException = nullptr;
    Property_set_specifyTilingScheme((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rootTilesX)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::rootTilesX() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rootTilesX((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rootTilesX)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::rootTilesX(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_rootTilesX((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rootTilesY)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::rootTilesY() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rootTilesY((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rootTilesY)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::rootTilesY(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_rootTilesY((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleWest)(void* thiz, void** reinteropException) = nullptr;


double CesiumUrlTemplateRasterOverlay::rectangleWest() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleWest((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleWest)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::rectangleWest(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleWest((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleSouth)(void* thiz, void** reinteropException) = nullptr;


double CesiumUrlTemplateRasterOverlay::rectangleSouth() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleSouth((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleSouth)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::rectangleSouth(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleSouth((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleEast)(void* thiz, void** reinteropException) = nullptr;


double CesiumUrlTemplateRasterOverlay::rectangleEast() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleEast((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleEast)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::rectangleEast(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleEast((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


double (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_rectangleNorth)(void* thiz, void** reinteropException) = nullptr;


double CesiumUrlTemplateRasterOverlay::rectangleNorth() const {
    void* reinteropException = nullptr;
    auto result = Property_get_rectangleNorth((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_rectangleNorth)(void* thiz, double value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::rectangleNorth(double value) const {
    void* reinteropException = nullptr;
    Property_set_rectangleNorth((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_minimumLevel)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::minimumLevel() const {
    void* reinteropException = nullptr;
    auto result = Property_get_minimumLevel((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_minimumLevel)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::minimumLevel(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_minimumLevel((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumLevel)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::maximumLevel() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumLevel((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumLevel)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::maximumLevel(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumLevel((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_tileWidth)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::tileWidth() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileWidth((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_tileWidth)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::tileWidth(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_tileWidth((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_tileHeight)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::tileHeight() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileHeight((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_tileHeight)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::tileHeight(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_tileHeight((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_requestHeaders)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::HeaderEntry> CesiumUrlTemplateRasterOverlay::requestHeaders() const {
    void* reinteropException = nullptr;
    auto result = Property_get_requestHeaders((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::HeaderEntry>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_requestHeaders)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::requestHeaders(const ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::HeaderEntry>& value) const {
    void* reinteropException = nullptr;
    Property_set_requestHeaders((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_materialKey)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumUrlTemplateRasterOverlay::materialKey() const {
    void* reinteropException = nullptr;
    auto result = Property_get_materialKey((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_materialKey)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::materialKey(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_materialKey((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_showCreditsOnScreen)(void* thiz, void** reinteropException) = nullptr;


bool CesiumUrlTemplateRasterOverlay::showCreditsOnScreen() const {
    void* reinteropException = nullptr;
    auto result = Property_get_showCreditsOnScreen((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_showCreditsOnScreen)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::showCreditsOnScreen(bool value) const {
    void* reinteropException = nullptr;
    Property_set_showCreditsOnScreen((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


float (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumScreenSpaceError)(void* thiz, void** reinteropException) = nullptr;


float CesiumUrlTemplateRasterOverlay::maximumScreenSpaceError() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumScreenSpaceError((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumScreenSpaceError)(void* thiz, float value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::maximumScreenSpaceError(float value) const {
    void* reinteropException = nullptr;
    Property_set_maximumScreenSpaceError((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumTextureSize)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::maximumTextureSize() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumTextureSize((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumTextureSize)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::maximumTextureSize(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumTextureSize((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_maximumSimultaneousTileLoads)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::maximumSimultaneousTileLoads() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_maximumSimultaneousTileLoads)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::maximumSimultaneousTileLoads(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_subTileCacheBytes)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumUrlTemplateRasterOverlay::subTileCacheBytes() const {
    void* reinteropException = nullptr;
    auto result = Property_get_subTileCacheBytes((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_subTileCacheBytes)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::subTileCacheBytes(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_subTileCacheBytes((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::Refresh() const {
    void* reinteropException = nullptr;
    CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::AddToTileset() const {
    void* reinteropException = nullptr;
    CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::RemoveFromTileset() const {
    void* reinteropException = nullptr;
    CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumUrlTemplateRasterOverlay::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumUrlTemplateRasterOverlay::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumUrlTemplateRasterOverlay::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumUrlTemplateRasterOverlay::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumUrlTemplateRasterOverlay::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumUrlTemplateRasterOverlay::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumUrlTemplateRasterOverlay::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumUrlTemplateRasterOverlay::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumUrlTemplateRasterOverlay::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumUrlTemplateRasterOverlay::operator==(const CesiumUrlTemplateRasterOverlay& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumUrlTemplateRasterOverlay::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumUrlTemplateRasterOverlay::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumUrlTemplateRasterOverlay::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumUrlTemplateRasterOverlay::operator!=(const CesiumUrlTemplateRasterOverlay& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumUrlTemplateRasterOverlay::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumUrlTemplateRasterOverlay::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumUrlTemplateRasterOverlay::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*CesiumUrlTemplateRasterOverlay::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumUrlTemplateRasterOverlayImpl& CesiumUrlTemplateRasterOverlay::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumUrlTemplateRasterOverlayImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumUrlTemplateRasterOverlay_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumUrlTemplateRasterOverlayImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumUrlTemplateRasterOverlay_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumUrlTemplateRasterOverlayImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumUrlTemplateRasterOverlay_AddToTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumUrlTemplateRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
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
void DotNet_CesiumForUnity_CesiumUrlTemplateRasterOverlay_RemoveFromTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumUrlTemplateRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumUrlTemplateRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
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

