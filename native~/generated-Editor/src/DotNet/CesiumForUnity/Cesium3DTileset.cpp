#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/MonoBehaviour.h>
#include <DotNet/UnityEngine/Behaviour.h>
#include <DotNet/UnityEngine/Component.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumDataSource.h>
#include <DotNet/System/String.h>
#include <DotNet/CesiumForUnity/CesiumIonServer.h>
#include <DotNet/UnityEngine/Material.h>
#include <DotNet/CesiumForUnity/Cesium3DTilesetLoadFailureDetails.h>
#include <DotNet/UnityEngine/GameObject.h>
#include <DotNet/UnityEngine/Coroutine.h>
#include <DotNet/System/Collections/IEnumerator.h>
#include <DotNet/UnityEngine/Transform.h>
#include <DotNet/CesiumForUnity/CesiumPrimitiveFeatures.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "Cesium3DTilesetImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/CesiumForUnity/CesiumSampleHeightResult.h>
#include <DotNet/System/Threading/Tasks/Task1.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/System/Array1.h>



namespace DotNet::CesiumForUnity {

Cesium3DTileset::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Cesium3DTileset::Cesium3DTileset(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& Cesium3DTileset::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Cesium3DTileset::GetHandle() {
    return this->_handle;
}


void* (*Cesium3DTileset::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


Cesium3DTileset::Cesium3DTileset()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


Cesium3DTileset::operator ::DotNet::UnityEngine::MonoBehaviour() const {
    return ::DotNet::UnityEngine::MonoBehaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Cesium3DTileset::operator ::DotNet::UnityEngine::Behaviour() const {
    return ::DotNet::UnityEngine::Behaviour(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Cesium3DTileset::operator ::DotNet::UnityEngine::Component() const {
    return ::DotNet::UnityEngine::Component(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Cesium3DTileset::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


Cesium3DTileset::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint32_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_tilesetSource)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumDataSource Cesium3DTileset::tilesetSource() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tilesetSource((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumDataSource(result);
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_tilesetSource)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::tilesetSource(::DotNet::CesiumForUnity::CesiumDataSource value) const {
    void* reinteropException = nullptr;
    Property_set_tilesetSource((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ionAccessToken)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Cesium3DTileset::ionAccessToken() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionAccessToken((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ionAccessToken)(void* thiz, void* value, void** reinteropException) = nullptr;


void Cesium3DTileset::ionAccessToken(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_ionAccessToken((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ionAssetID)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t Cesium3DTileset::ionAssetID() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionAssetID((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ionAssetID)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::ionAssetID(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_ionAssetID((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ionServer)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServer Cesium3DTileset::ionServer() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionServer((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonServer(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ionServer)(void* thiz, void* value, void** reinteropException) = nullptr;


void Cesium3DTileset::ionServer(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const {
    void* reinteropException = nullptr;
    Property_set_ionServer((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_url)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Cesium3DTileset::url() const {
    void* reinteropException = nullptr;
    auto result = Property_get_url((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_url)(void* thiz, void* value, void** reinteropException) = nullptr;


void Cesium3DTileset::url(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_url((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_logSelectionStats)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::logSelectionStats() const {
    void* reinteropException = nullptr;
    auto result = Property_get_logSelectionStats((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_logSelectionStats)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::logSelectionStats(bool value) const {
    void* reinteropException = nullptr;
    Property_set_logSelectionStats((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_opaqueMaterial)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Material Cesium3DTileset::opaqueMaterial() const {
    void* reinteropException = nullptr;
    auto result = Property_get_opaqueMaterial((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Material(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_opaqueMaterial)(void* thiz, void* value, void** reinteropException) = nullptr;


void Cesium3DTileset::opaqueMaterial(const ::DotNet::UnityEngine::Material& value) const {
    void* reinteropException = nullptr;
    Property_set_opaqueMaterial((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


float (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_maximumScreenSpaceError)(void* thiz, void** reinteropException) = nullptr;


float Cesium3DTileset::maximumScreenSpaceError() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumScreenSpaceError((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_maximumScreenSpaceError)(void* thiz, float value, void** reinteropException) = nullptr;


void Cesium3DTileset::maximumScreenSpaceError(float value) const {
    void* reinteropException = nullptr;
    Property_set_maximumScreenSpaceError((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_preloadAncestors)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::preloadAncestors() const {
    void* reinteropException = nullptr;
    auto result = Property_get_preloadAncestors((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_preloadAncestors)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::preloadAncestors(bool value) const {
    void* reinteropException = nullptr;
    Property_set_preloadAncestors((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_preloadSiblings)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::preloadSiblings() const {
    void* reinteropException = nullptr;
    auto result = Property_get_preloadSiblings((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_preloadSiblings)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::preloadSiblings(bool value) const {
    void* reinteropException = nullptr;
    Property_set_preloadSiblings((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_forbidHoles)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::forbidHoles() const {
    void* reinteropException = nullptr;
    auto result = Property_get_forbidHoles((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_forbidHoles)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::forbidHoles(bool value) const {
    void* reinteropException = nullptr;
    Property_set_forbidHoles((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_maximumSimultaneousTileLoads)(void* thiz, void** reinteropException) = nullptr;


::std::uint32_t Cesium3DTileset::maximumSimultaneousTileLoads() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_maximumSimultaneousTileLoads)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::maximumSimultaneousTileLoads(::std::uint32_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumSimultaneousTileLoads((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_maximumCachedBytes)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t Cesium3DTileset::maximumCachedBytes() const {
    void* reinteropException = nullptr;
    auto result = Property_get_maximumCachedBytes((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_maximumCachedBytes)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::maximumCachedBytes(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Property_set_maximumCachedBytes((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_loadingDescendantLimit)(void* thiz, void** reinteropException) = nullptr;


::std::uint32_t Cesium3DTileset::loadingDescendantLimit() const {
    void* reinteropException = nullptr;
    auto result = Property_get_loadingDescendantLimit((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_loadingDescendantLimit)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::loadingDescendantLimit(::std::uint32_t value) const {
    void* reinteropException = nullptr;
    Property_set_loadingDescendantLimit((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enableFrustumCulling)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::enableFrustumCulling() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enableFrustumCulling((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enableFrustumCulling)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::enableFrustumCulling(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enableFrustumCulling((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enableFogCulling)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::enableFogCulling() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enableFogCulling((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enableFogCulling)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::enableFogCulling(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enableFogCulling((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enforceCulledScreenSpaceError)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::enforceCulledScreenSpaceError() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enforceCulledScreenSpaceError((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enforceCulledScreenSpaceError)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::enforceCulledScreenSpaceError(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enforceCulledScreenSpaceError((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


float (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_culledScreenSpaceError)(void* thiz, void** reinteropException) = nullptr;


float Cesium3DTileset::culledScreenSpaceError() const {
    void* reinteropException = nullptr;
    auto result = Property_get_culledScreenSpaceError((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_culledScreenSpaceError)(void* thiz, float value, void** reinteropException) = nullptr;


void Cesium3DTileset::culledScreenSpaceError(float value) const {
    void* reinteropException = nullptr;
    Property_set_culledScreenSpaceError((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_generateSmoothNormals)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::generateSmoothNormals() const {
    void* reinteropException = nullptr;
    auto result = Property_get_generateSmoothNormals((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_generateSmoothNormals)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::generateSmoothNormals(bool value) const {
    void* reinteropException = nullptr;
    Property_set_generateSmoothNormals((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_ignoreKhrMaterialsUnlit)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::ignoreKhrMaterialsUnlit() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ignoreKhrMaterialsUnlit((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_ignoreKhrMaterialsUnlit)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::ignoreKhrMaterialsUnlit(bool value) const {
    void* reinteropException = nullptr;
    Property_set_ignoreKhrMaterialsUnlit((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_createPhysicsMeshes)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::createPhysicsMeshes() const {
    void* reinteropException = nullptr;
    auto result = Property_get_createPhysicsMeshes((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_createPhysicsMeshes)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::createPhysicsMeshes(bool value) const {
    void* reinteropException = nullptr;
    Property_set_createPhysicsMeshes((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_suspendUpdate)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::suspendUpdate() const {
    void* reinteropException = nullptr;
    auto result = Property_get_suspendUpdate((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_suspendUpdate)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::suspendUpdate(bool value) const {
    void* reinteropException = nullptr;
    Property_set_suspendUpdate((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_previousSuspendUpdate)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::previousSuspendUpdate() const {
    void* reinteropException = nullptr;
    auto result = Property_get_previousSuspendUpdate((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_previousSuspendUpdate)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::previousSuspendUpdate(bool value) const {
    void* reinteropException = nullptr;
    Property_set_previousSuspendUpdate((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_showTilesInHierarchy)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::showTilesInHierarchy() const {
    void* reinteropException = nullptr;
    auto result = Property_get_showTilesInHierarchy((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_showTilesInHierarchy)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::showTilesInHierarchy(bool value) const {
    void* reinteropException = nullptr;
    Property_set_showTilesInHierarchy((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_updateInEditor)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::updateInEditor() const {
    void* reinteropException = nullptr;
    auto result = Property_get_updateInEditor((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_updateInEditor)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::updateInEditor(bool value) const {
    void* reinteropException = nullptr;
    Property_set_updateInEditor((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_showCreditsOnScreen)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::showCreditsOnScreen() const {
    void* reinteropException = nullptr;
    auto result = Property_get_showCreditsOnScreen((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_showCreditsOnScreen)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::showCreditsOnScreen(bool value) const {
    void* reinteropException = nullptr;
    Property_set_showCreditsOnScreen((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::CallRecreateTileset_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void Cesium3DTileset::RecreateTileset() const {
    void* reinteropException = nullptr;
    CallRecreateTileset_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::CallBroadcastCesium3DTilesetLoadFailure_EA9gid9gf99C0Ye5ZgnZYw)(void* details, void** reinteropException) = nullptr;


void Cesium3DTileset::BroadcastCesium3DTilesetLoadFailure(const ::DotNet::CesiumForUnity::Cesium3DTilesetLoadFailureDetails& details) {
    void* reinteropException = nullptr;
    CallBroadcastCesium3DTilesetLoadFailure_EA9gid9gf99C0Ye5ZgnZYw(details.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::CallBroadcastNewGameObjectCreated_PB2O3_b6vvn_5vRyfrXK8g)(void* thiz, void* go, void** reinteropException) = nullptr;


void Cesium3DTileset::BroadcastNewGameObjectCreated(const ::DotNet::UnityEngine::GameObject& go) const {
    void* reinteropException = nullptr;
    CallBroadcastNewGameObjectCreated_PB2O3_b6vvn_5vRyfrXK8g((*this).GetHandle().GetRaw(), go.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw)(void* thiz, void* routine, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Coroutine Cesium3DTileset::StartCoroutine(const ::DotNet::System::Collections::IEnumerator& routine) const {
    void* reinteropException = nullptr;
    auto result = CallStartCoroutine_ZFMblNea9_yxHzcTccrQTw((*this).GetHandle().GetRaw(), routine.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Coroutine(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_enabled)(void* thiz, void** reinteropException) = nullptr;


bool Cesium3DTileset::enabled() const {
    void* reinteropException = nullptr;
    auto result = Property_get_enabled((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_enabled)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::enabled(bool value) const {
    void* reinteropException = nullptr;
    Property_set_enabled((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_gameObject)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::GameObject Cesium3DTileset::gameObject() const {
    void* reinteropException = nullptr;
    auto result = Property_get_gameObject((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::GameObject(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_transform)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform Cesium3DTileset::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw)(void* thiz, void** reinteropException) = nullptr;


template <> ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures Cesium3DTileset::GetComponent<::DotNet::CesiumForUnity::CesiumPrimitiveFeatures>() const {
    void* reinteropException = nullptr;
    auto result = CallGetComponent_rQkkHgP4S0DBS3JoaG7KAw((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPrimitiveFeatures(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String Cesium3DTileset::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void Cesium3DTileset::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::Cesium3DTileset::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> Cesium3DTileset::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::Cesium3DTileset::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void Cesium3DTileset::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Cesium3DTileset::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool Cesium3DTileset::operator==(const Cesium3DTileset& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Cesium3DTileset::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Cesium3DTileset::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::Cesium3DTileset::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool Cesium3DTileset::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool Cesium3DTileset::operator!=(const Cesium3DTileset& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool Cesium3DTileset::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool Cesium3DTileset::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::Cesium3DTileset::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t Cesium3DTileset::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*Cesium3DTileset::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::Cesium3DTilesetImpl& Cesium3DTileset::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::Cesium3DTilesetImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_Cesium3DTileset_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::Cesium3DTilesetImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_Cesium3DTileset_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
float DotNet_CesiumForUnity_Cesium3DTileset_ComputeLoadProgress(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->ComputeLoadProgress(wrapper);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return float();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return float();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return float();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_Cesium3DTileset_RecreateTileset(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->RecreateTileset(wrapper);
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
void DotNet_CesiumForUnity_Cesium3DTileset_FocusTileset(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->FocusTileset(wrapper);
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
void* DotNet_CesiumForUnity_Cesium3DTileset_SampleHeightMostDetailed(void* handle, void* pImpl, void* longitudeLatitudeHeightPositions, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->SampleHeightMostDetailed(wrapper, ::DotNet::System::Array1<::DotNet::Unity::Mathematics::double3>(::DotNet::Reinterop::ObjectHandle(longitudeLatitudeHeightPositions)));
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_Cesium3DTileset_SetShowCreditsOnScreen(void* handle, void* pImpl, ::std::uint8_t value, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->SetShowCreditsOnScreen(wrapper, !!value);
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
void DotNet_CesiumForUnity_Cesium3DTileset_Start(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->Start(wrapper);
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
void DotNet_CesiumForUnity_Cesium3DTileset_Update(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->Update(wrapper);
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
void DotNet_CesiumForUnity_Cesium3DTileset_OnValidate(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->OnValidate(wrapper);
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
void DotNet_CesiumForUnity_Cesium3DTileset_OnEnable(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->OnEnable(wrapper);
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
void DotNet_CesiumForUnity_Cesium3DTileset_OnDisable(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->OnDisable(wrapper);
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
void DotNet_CesiumForUnity_Cesium3DTileset_UpdateOverlayMaterialKeys(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::Cesium3DTilesetImpl*>(pImpl);const ::DotNet::CesiumForUnity::Cesium3DTileset wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->UpdateOverlayMaterialKeys(wrapper);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

