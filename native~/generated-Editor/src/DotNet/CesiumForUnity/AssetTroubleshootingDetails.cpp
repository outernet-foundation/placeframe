#include <DotNet/CesiumForUnity/AssetTroubleshootingDetails.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::CesiumForUnity {

AssetTroubleshootingDetails::AssetTroubleshootingDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


AssetTroubleshootingDetails::AssetTroubleshootingDetails(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool AssetTroubleshootingDetails::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool AssetTroubleshootingDetails::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& AssetTroubleshootingDetails::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& AssetTroubleshootingDetails::GetHandle() {
    return this->_handle;
}


AssetTroubleshootingDetails::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_get_assetExistsInUserAccount)(void* thiz, void** reinteropException) = nullptr;


bool AssetTroubleshootingDetails::assetExistsInUserAccount() const {
    void* reinteropException = nullptr;
    auto result = Property_get_assetExistsInUserAccount((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_set_assetExistsInUserAccount)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void AssetTroubleshootingDetails::assetExistsInUserAccount(bool value) const {
    void* reinteropException = nullptr;
    Property_set_assetExistsInUserAccount((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_get_loaded)(void* thiz, void** reinteropException) = nullptr;


bool AssetTroubleshootingDetails::loaded() const {
    void* reinteropException = nullptr;
    auto result = Property_get_loaded((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::AssetTroubleshootingDetails::Property_set_loaded)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void AssetTroubleshootingDetails::loaded(bool value) const {
    void* reinteropException = nullptr;
    Property_set_loaded((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity


