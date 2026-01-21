#include <DotNet/CesiumForUnity/CesiumIonServerManager.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEditor/ScriptableSingleton1.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/CesiumForUnity/CesiumIonServer.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumIonSession.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>



namespace DotNet::CesiumForUnity {

CesiumIonServerManager::CesiumIonServerManager(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumIonServerManager::CesiumIonServerManager(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& CesiumIonServerManager::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumIonServerManager::GetHandle() {
    return this->_handle;
}


CesiumIonServerManager::operator ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>() const {
    return ::DotNet::UnityEditor::ScriptableSingleton1<::DotNet::CesiumForUnity::CesiumIonServerManager>(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonServerManager::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


CesiumIonServerManager::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_current)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServer CesiumIonServerManager::current() const {
    void* reinteropException = nullptr;
    auto result = Property_get_current((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonServer(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_set_current)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonServerManager::current(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const {
    void* reinteropException = nullptr;
    Property_set_current((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_currentSession)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonSession CesiumIonServerManager::currentSession() const {
    void* reinteropException = nullptr;
    auto result = Property_get_currentSession((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonSession(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonServerManager::CallGetSession_ouKG7YNdV4bUJcBV0W3dBA)(void* thiz, void* server, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonSession CesiumIonServerManager::GetSession(const ::DotNet::CesiumForUnity::CesiumIonServer& server) const {
    void* reinteropException = nullptr;
    auto result = CallGetSession_ouKG7YNdV4bUJcBV0W3dBA((*this).GetHandle().GetRaw(), server.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonSession(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonServerManager::CallGetUserAccessToken_ouKG7YNdV4bUJcBV0W3dBA)(void* thiz, void* server, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServerManager::GetUserAccessToken(const ::DotNet::CesiumForUnity::CesiumIonServer& server) const {
    void* reinteropException = nullptr;
    auto result = CallGetUserAccessToken_ouKG7YNdV4bUJcBV0W3dBA((*this).GetHandle().GetRaw(), server.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonServerManager::CallSetUserAccessToken_i1OZfOwTwhgNuaqLRy9vZQ)(void* thiz, void* server, void* token, void** reinteropException) = nullptr;


void CesiumIonServerManager::SetUserAccessToken(const ::DotNet::CesiumForUnity::CesiumIonServer& server, const ::DotNet::System::String& token) const {
    void* reinteropException = nullptr;
    CallSetUserAccessToken_i1OZfOwTwhgNuaqLRy9vZQ((*this).GetHandle().GetRaw(), server.GetHandle().GetRaw(), token.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_instance)(void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServerManager CesiumIonServerManager::instance() {
    void* reinteropException = nullptr;
    auto result = Property_get_instance(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonServerManager(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String CesiumIonServerManager::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonServerManager::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> CesiumIonServerManager::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::CesiumIonServerManager::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void CesiumIonServerManager::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonServerManager::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumIonServerManager::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool CesiumIonServerManager::operator==(const CesiumIonServerManager& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumIonServerManager::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumIonServerManager::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonServerManager::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool CesiumIonServerManager::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool CesiumIonServerManager::operator!=(const CesiumIonServerManager& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool CesiumIonServerManager::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool CesiumIonServerManager::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumIonServerManager::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t CesiumIonServerManager::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


