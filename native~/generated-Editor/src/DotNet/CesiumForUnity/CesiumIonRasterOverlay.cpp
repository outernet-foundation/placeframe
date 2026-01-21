#include <DotNet/CesiumForUnity/CesiumIonRasterOverlay.h>
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
#include <DotNet/CesiumForUnity/CesiumIonServer.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "CesiumIonRasterOverlayImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>



namespace DotNet::CesiumForUnity {

CesiumIonRasterOverlay::CesiumIonRasterOverlay(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumIonRasterOverlay::CesiumIonRasterOverlay(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumIonRasterOverlay::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumIonRasterOverlay::GetHandle() {
    return this->_handle;
}


CesiumIonRasterOverlay::operator ::DotNet::CesiumForUnity::CesiumRasterOverlay() const {
    return ::DotNet::CesiumForUnity::CesiumRasterOverlay(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonRasterOverlay::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonRasterOverlay::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonRasterOverlay::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonRasterOverlay::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonRasterOverlay::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_ionAccessToken)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonRasterOverlay::ionAccessToken() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionAccessToken((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_ionAccessToken)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::ionAccessToken(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_ionAccessToken((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_ionAssetID)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumIonRasterOverlay::ionAssetID() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionAssetID((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_ionAssetID)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::ionAssetID(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_ionAssetID((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_ionServer)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServer CesiumIonRasterOverlay::ionServer() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionServer((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonServer(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_ionServer)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::ionServer(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const {
    void* reinteropException = nullptr;
    Property_set_ionServer((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_assetOptions)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonRasterOverlay::assetOptions() const {
    void* reinteropException = nullptr;
    auto result = Property_get_assetOptions((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_assetOptions)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::assetOptions(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_assetOptions((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallAddToTilesetLater_SrfNoP9IJM__ZwyysR9yJTQ)(void* thiz, void* tileset, void** reinteropException) = nullptr;


::DotNet::System::Collections::IEnumerator CesiumIonRasterOverlay::AddToTilesetLater(const ::DotNet::CesiumForUnity::Cesium3DTileset& tileset) const {
    void* reinteropException = nullptr;
    auto result = CallAddToTilesetLater_SrfNoP9IJM__ZwyysR9yJTQ((*this).GetHandle().GetRaw(), tileset.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::IEnumerator(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_materialKey)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonRasterOverlay::materialKey() const {
    void* reinteropException = nullptr;
    auto result = Property_get_materialKey((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_materialKey)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::materialKey(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_materialKey((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_showCreditsOnScreen)(void* thiz, void** reinteropException) = nullptr;


bool CesiumIonRasterOverlay::showCreditsOnScreen() const {
    void* reinteropException = nullptr;
    auto result = Property_get_showCreditsOnScreen((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_showCreditsOnScreen)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::showCreditsOnScreen(bool value) const {
    void* reinteropException = nullptr;
    Property_set_showCreditsOnScreen((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


float (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_maximumScreenSpaceError)(void* thiz, void** reinteropException) = nullptr;


float CesiumIonRasterOverlay::maximumScreenSpaceError() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumScreenSpaceError((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_maximumScreenSpaceError)(void* thiz, float value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::maximumScreenSpaceError(float value) const {
    void* reinteropException = nullptr;
    Property_set_maximumScreenSpaceError((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_maximumTextureSize)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumIonRasterOverlay::maximumTextureSize() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumTextureSize((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_maximumTextureSize)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::maximumTextureSize(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumTextureSize((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_maximumSimultaneousTileLoads)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumIonRasterOverlay::maximumSimultaneousTileLoads() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_maximumSimultaneousTileLoads)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::maximumSimultaneousTileLoads(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_subTileCacheBytes)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumIonRasterOverlay::subTileCacheBytes() const {
    void* reinteropException = nullptr;
    auto result = Property_get_subTileCacheBytes((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_subTileCacheBytes)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::subTileCacheBytes(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_subTileCacheBytes((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::Refresh() const {
    void* reinteropException = nullptr;
    CallRefresh_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::AddToTileset() const {
    void* reinteropException = nullptr;
    CallAddToTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::RemoveFromTileset() const {
    void* reinteropException = nullptr;
    CallRemoveFromTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine CesiumIonRasterOverlay::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool CesiumIonRasterOverlay::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject CesiumIonRasterOverlay::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform CesiumIonRasterOverlay::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures CesiumIonRasterOverlay::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonRasterOverlay::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumIonRasterOverlay::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumIonRasterOverlay::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumIonRasterOverlay::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumIonRasterOverlay::operator==(const CesiumIonRasterOverlay& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumIonRasterOverlay::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumIonRasterOverlay::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumIonRasterOverlay::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumIonRasterOverlay::operator!=(const CesiumIonRasterOverlay& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumIonRasterOverlay::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumIonRasterOverlay::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumIonRasterOverlay::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumIonRasterOverlay::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*CesiumIonRasterOverlay::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumIonRasterOverlayImpl& CesiumIonRasterOverlay::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumIonRasterOverlayImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumIonRasterOverlay_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumIonRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumIonRasterOverlayImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumIonRasterOverlay_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonRasterOverlayImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumIonRasterOverlay_AddToTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
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
void DotNet_CesiumForUnity_CesiumIonRasterOverlay_RemoveFromTileset(void* handle, void* pImpl, void* tileset, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonRasterOverlayImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonRasterOverlay wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
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

