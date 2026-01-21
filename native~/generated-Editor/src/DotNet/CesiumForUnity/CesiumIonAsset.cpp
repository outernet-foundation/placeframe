#include <DotNet/CesiumForUnity/CesiumIonAsset.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/Cesium3DTileset.h>
#include <DotNet/CesiumForUnity/CesiumIonRasterOverlay.h>



namespace DotNet::CesiumForUnity {

CesiumIonAsset::CesiumIonAsset(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumIonAsset::CesiumIonAsset(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumIonAsset::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumIonAsset::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumIonAsset::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumIonAsset::GetHandle() {
    return this->_handle;
}


CesiumIonAsset::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumIonAsset::Property_get_objectName)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonAsset::objectName() const {
    void* reinteropException = nullptr;
    auto result = Property_get_objectName((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonAsset::Property_get_type)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonAsset::type() const {
    void* reinteropException = nullptr;
    auto result = Property_get_type((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonAsset::Property_get_componentType)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonAsset::componentType() const {
    void* reinteropException = nullptr;
    auto result = Property_get_componentType((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonAsset::Property_get_ionAccessToken)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonAsset::ionAccessToken() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionAccessToken((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonAsset::Property_set_ionAccessToken)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonAsset::ionAccessToken(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_ionAccessToken((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumIonAsset::Property_get_ionAssetID)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t CesiumIonAsset::ionAssetID() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionAssetID((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::CesiumForUnity::CesiumIonAsset::Property_get_tileset)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::Cesium3DTileset CesiumIonAsset::tileset() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tileset((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::Cesium3DTileset(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonAsset::Property_get_overlay)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonRasterOverlay CesiumIonAsset::overlay() const {
    void* reinteropException = nullptr;
    auto result = Property_get_overlay((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonRasterOverlay(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonAsset::CallIsNull_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


bool CesiumIonAsset::IsNull() const {
    void* reinteropException = nullptr;
    auto result = CallIsNull_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


} // namespace DotNet::CesiumForUnity


