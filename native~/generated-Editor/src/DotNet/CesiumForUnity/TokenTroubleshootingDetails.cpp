#include <DotNet/CesiumForUnity/TokenTroubleshootingDetails.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/System/String.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>



namespace DotNet::CesiumForUnity {

TokenTroubleshootingDetails::TokenTroubleshootingDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


TokenTroubleshootingDetails::TokenTroubleshootingDetails(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool TokenTroubleshootingDetails::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool TokenTroubleshootingDetails::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& TokenTroubleshootingDetails::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& TokenTroubleshootingDetails::GetHandle() {
    return this->_handle;
}


TokenTroubleshootingDetails::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_token)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String TokenTroubleshootingDetails::token() const {
    void* reinteropException = nullptr;
    auto result = Property_get_token((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_token)(void* thiz, void* value, void** reinteropException) = nullptr;


void TokenTroubleshootingDetails::token(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_token((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_isValid)(void* thiz, void** reinteropException) = nullptr;


bool TokenTroubleshootingDetails::isValid() const {
    void* reinteropException = nullptr;
    auto result = Property_get_isValid((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_isValid)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void TokenTroubleshootingDetails::isValid(bool value) const {
    void* reinteropException = nullptr;
    Property_set_isValid((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_allowsAccessToAsset)(void* thiz, void** reinteropException) = nullptr;


bool TokenTroubleshootingDetails::allowsAccessToAsset() const {
    void* reinteropException = nullptr;
    auto result = Property_get_allowsAccessToAsset((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_allowsAccessToAsset)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void TokenTroubleshootingDetails::allowsAccessToAsset(bool value) const {
    void* reinteropException = nullptr;
    Property_set_allowsAccessToAsset((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_associatedWithUserAccount)(void* thiz, void** reinteropException) = nullptr;


bool TokenTroubleshootingDetails::associatedWithUserAccount() const {
    void* reinteropException = nullptr;
    auto result = Property_get_associatedWithUserAccount((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_associatedWithUserAccount)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void TokenTroubleshootingDetails::associatedWithUserAccount(bool value) const {
    void* reinteropException = nullptr;
    Property_set_associatedWithUserAccount((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_get_loaded)(void* thiz, void** reinteropException) = nullptr;


bool TokenTroubleshootingDetails::loaded() const {
    void* reinteropException = nullptr;
    auto result = Property_get_loaded((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void (*DotNet::CesiumForUnity::TokenTroubleshootingDetails::Property_set_loaded)(void* thiz, ::std::uint8_t value, void** reinteropException) = nullptr;


void TokenTroubleshootingDetails::loaded(bool value) const {
    void* reinteropException = nullptr;
    Property_set_loaded((*this).GetHandle().GetRaw(), value ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::CesiumForUnity


