#include <DotNet/CesiumForUnity/CesiumIonServer.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>



namespace DotNet::CesiumForUnity {

CesiumIonServer::CesiumIonServer(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumIonServer::CesiumIonServer(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumIonServer::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumIonServer::GetHandle() {
    return this->_handle;
}


CesiumIonServer::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonServer::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumIonServer::Property_get_defaultServer)(void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServer CesiumIonServer::defaultServer() {
    void* reinteropException = nullptr;
    auto result = Property_get_defaultServer(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonServer(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonServer::Field_get_defaultIonAccessToken)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumIonServer::Field_set_defaultIonAccessToken)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServer::defaultIonAccessToken() const {
    void* reinteropException = nullptr;
    auto result = Field_get_defaultIonAccessToken((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void CesiumIonServer::defaultIonAccessToken(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_defaultIonAccessToken((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::CesiumIonServer::Field_get_defaultIonAccessTokenId)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumIonServer::Field_set_defaultIonAccessTokenId)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServer::defaultIonAccessTokenId() const {
    void* reinteropException = nullptr;
    auto result = Field_get_defaultIonAccessTokenId((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void CesiumIonServer::defaultIonAccessTokenId(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_defaultIonAccessTokenId((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::CesiumIonServer::Field_get_apiUrl)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumIonServer::Field_set_apiUrl)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServer::apiUrl() const {
    void* reinteropException = nullptr;
    auto result = Field_get_apiUrl((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void CesiumIonServer::apiUrl(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_apiUrl((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::CesiumIonServer::Field_get_serverUrl)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumIonServer::Field_set_serverUrl)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServer::serverUrl() const {
    void* reinteropException = nullptr;
    auto result = Field_get_serverUrl((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void CesiumIonServer::serverUrl(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_serverUrl((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumIonServer::Field_get_oauth2ApplicationID)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumIonServer::Field_set_oauth2ApplicationID)(void* thiz, ::std::int64_t value, void** reinteropException) = nullptr;


::std::int64_t CesiumIonServer::oauth2ApplicationID() const {
    void* reinteropException = nullptr;
    auto result = Field_get_oauth2ApplicationID((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return result;
}


void CesiumIonServer::oauth2ApplicationID(::std::int64_t value) const {
    void* reinteropException = nullptr;
    Field_set_oauth2ApplicationID((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::CesiumIonServer::Field_get_serverUrlThatIsLoadingApiUrl)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::CesiumIonServer::Field_set_serverUrlThatIsLoadingApiUrl)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServer::serverUrlThatIsLoadingApiUrl() const {
    void* reinteropException = nullptr;
    auto result = Field_get_serverUrlThatIsLoadingApiUrl((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void CesiumIonServer::serverUrlThatIsLoadingApiUrl(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Field_set_serverUrlThatIsLoadingApiUrl((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::CesiumIonServer::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServer::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonServer::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonServer::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumIonServer::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumIonServer::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumIonServer::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumIonServer::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonServer::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumIonServer::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumIonServer::operator==(const CesiumIonServer& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumIonServer::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumIonServer::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonServer::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumIonServer::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumIonServer::operator!=(const CesiumIonServer& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumIonServer::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumIonServer::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumIonServer::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumIonServer::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


