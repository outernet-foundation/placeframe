#include <DotNet/CesiumForUnity/CesiumGoogleMapTilesRasterOverlay.h>
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
#include <DotNet/CesiumForUnity/GoogleMapTilesMapType.h>
#include <DotNet/CesiumForUnity/GoogleMapTilesScale.h>
#include <DotNet/CesiumForUnity/GoogleMapTilesLayerType.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumGoogleMapTilesRasterOverlayImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>



namespace DotNet::CesiumForUnity {

CesiumGoogleMapTilesRasterOverlay::CesiumGoogleMapTilesRasterOverlay(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumGoogleMapTilesRasterOverlay::CesiumGoogleMapTilesRasterOverlay(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumGoogleMapTilesRasterOverlay::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumGoogleMapTilesRasterOverlay::GetHandle() {
    return this->_handle;
}


CesiumGoogleMapTilesRasterOverlay::operator ::DotNet::CesiumForUnity::CesiumRasterOverlay() const {
    return ::DotNet::CesiumForUnity::CesiumRasterOverlay(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGoogleMapTilesRasterOverlay::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGoogleMapTilesRasterOverlay::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGoogleMapTilesRasterOverlay::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGoogleMapTilesRasterOverlay::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumGoogleMapTilesRasterOverlay::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_apiKey)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumGoogleMapTilesRasterOverlay::apiKey() const {
    void* reinteropException = nullptr;
    auto result = Property_get_apiKey((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_apiKey)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::apiKey(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_apiKey((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_mapType)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::GoogleMapTilesMapType CesiumGoogleMapTilesRasterOverlay::mapType() const {
    void* reinteropException = nullptr;
    auto result = Property_get_mapType((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::GoogleMapTilesMapType(result);
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_mapType)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::mapType(::DotNet::CesiumForUnity::GoogleMapTilesMapType value) const {
    void* reinteropException = nullptr;
    Property_set_mapType((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_language)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumGoogleMapTilesRasterOverlay::language() const {
    void* reinteropException = nullptr;
    auto result = Property_get_language((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_language)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::language(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_language((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_region)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumGoogleMapTilesRasterOverlay::region() const {
    void* reinteropException = nullptr;
    auto result = Property_get_region((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_region)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::region(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_region((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_scale)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::GoogleMapTilesScale CesiumGoogleMapTilesRasterOverlay::scale() const {
    void* reinteropException = nullptr;
    auto result = Property_get_scale((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::GoogleMapTilesScale(result);
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_scale)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::scale(::DotNet::CesiumForUnity::GoogleMapTilesScale value) const {
    void* reinteropException = nullptr;
    Property_set_scale((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_highDpi)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGoogleMapTilesRasterOverlay::highDpi() const {
    void* reinteropException = nullptr;
    auto result = Property_get_highDpi((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_highDpi)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::highDpi(bool value) const {
    void* reinteropException = nullptr;
    Property_set_highDpi((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_layerTypes)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType> CesiumGoogleMapTilesRasterOverlay::layerTypes() const {
    void* reinteropException = nullptr;
    auto result = Property_get_layerTypes((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_layerTypes)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::layerTypes(const ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::GoogleMapTilesLayerType>& value) const {
    void* reinteropException = nullptr;
    Property_set_layerTypes((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_styles)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::System::String> CesiumGoogleMapTilesRasterOverlay::styles() const {
    void* reinteropException = nullptr;
    auto result = Property_get_styles((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_styles)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::styles(const ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>& value) const {
    void* reinteropException = nullptr;
    Property_set_styles((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_overlay)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGoogleMapTilesRasterOverlay::overlay() const {
    void* reinteropException = nullptr;
    auto result = Property_get_overlay((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_overlay)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::overlay(bool value) const {
    void* reinteropException = nullptr;
    Property_set_overlay((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_materialKey)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumGoogleMapTilesRasterOverlay::materialKey() const {
    void* reinteropException = nullptr;
    auto result = Property_get_materialKey((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_materialKey)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::materialKey(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_materialKey((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_showCreditsOnScreen)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGoogleMapTilesRasterOverlay::showCreditsOnScreen() const {
    void* reinteropException = nullptr;
    auto result = Property_get_showCreditsOnScreen((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_showCreditsOnScreen)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::showCreditsOnScreen(bool value) const {
    void* reinteropException = nullptr;
    Property_set_showCreditsOnScreen((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


float (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_maximumScreenSpaceError)(void* thiz, void** reinteropException) = nullptr;


float CesiumGoogleMapTilesRasterOverlay::maximumScreenSpaceError() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumScreenSpaceError((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_maximumScreenSpaceError)(void* thiz, float value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::maximumScreenSpaceError(float value) const {
    void* reinteropException = nullptr;
    Property_set_maximumScreenSpaceError((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_maximumTextureSize)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumGoogleMapTilesRasterOverlay::maximumTextureSize() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumTextureSize((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_maximumTextureSize)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::maximumTextureSize(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumTextureSize((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_maximumSimultaneousTileLoads)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumGoogleMapTilesRasterOverlay::maximumSimultaneousTileLoads() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_maximumSimultaneousTileLoads)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::maximumSimultaneousTileLoads(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_subTileCacheBytes)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumGoogleMapTilesRasterOverlay::subTileCacheBytes() const {
    void* reinteropException = nullptr;
    auto result = Property_get_subTileCacheBytes((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_subTileCacheBytes)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::subTileCacheBytes(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_subTileCacheBytes((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::Refresh() const {
    void* reinteropException = nullptr;
    CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::AddToTileset() const {
    void* reinteropException = nullptr;
    CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::RemoveFromTileset() const {
    void* reinteropException = nullptr;
    CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumGoogleMapTilesRasterOverlay::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumGoogleMapTilesRasterOverlay::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumGoogleMapTilesRasterOverlay::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumGoogleMapTilesRasterOverlay::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumGoogleMapTilesRasterOverlay::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumGoogleMapTilesRasterOverlay::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumGoogleMapTilesRasterOverlay::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumGoogleMapTilesRasterOverlay::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumGoogleMapTilesRasterOverlay::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumGoogleMapTilesRasterOverlay::operator==(const CesiumGoogleMapTilesRasterOverlay& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumGoogleMapTilesRasterOverlay::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumGoogleMapTilesRasterOverlay::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumGoogleMapTilesRasterOverlay::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumGoogleMapTilesRasterOverlay::operator!=(const CesiumGoogleMapTilesRasterOverlay& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumGoogleMapTilesRasterOverlay::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumGoogleMapTilesRasterOverlay::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumGoogleMapTilesRasterOverlay::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*CesiumGoogleMapTilesRasterOverlay::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumGoogleMapTilesRasterOverlayImpl& CesiumGoogleMapTilesRasterOverlay::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumGoogleMapTilesRasterOverlayImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumGoogleMapTilesRasterOverlay_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumGoogleMapTilesRasterOverlayImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGoogleMapTilesRasterOverlay_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumGoogleMapTilesRasterOverlayImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumGoogleMapTilesRasterOverlay_AddToTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumGoogleMapTilesRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
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
void DotNet_CesiumForUnity_CesiumGoogleMapTilesRasterOverlay_RemoveFromTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumGoogleMapTilesRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumGoogleMapTilesRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
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

