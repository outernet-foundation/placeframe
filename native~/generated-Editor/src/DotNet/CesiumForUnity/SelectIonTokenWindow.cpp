#include <DotNet/CesiumForUnity/SelectIonTokenWindow.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEditor/EditorWindow.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/IonTokenSource.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/CesiumForUnity/CesiumIonServer.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "SelectIonTokenWindowImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>



namespace DotNet::CesiumForUnity {

SelectIonTokenWindow::SelectIonTokenWindow(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


SelectIonTokenWindow::SelectIonTokenWindow(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& SelectIonTokenWindow::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& SelectIonTokenWindow::GetHandle() {
    return this->_handle;
}


SelectIonTokenWindow::operator ::DotNet::UnityEditor::EditorWindow() const {
    return ::DotNet::UnityEditor::EditorWindow(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


SelectIonTokenWindow::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


SelectIonTokenWindow::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint32_t (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_tokenSource)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::IonTokenSource SelectIonTokenWindow::tokenSource() const {
    void* reinteropException = nullptr;
    auto result = Property_get_tokenSource((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::IonTokenSource(result);
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_tokenSource)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void SelectIonTokenWindow::tokenSource(::DotNet::CesiumForUnity::IonTokenSource value) const {
    void* reinteropException = nullptr;
    Property_set_tokenSource((*this).GetHandle().GetRaw(), ::std::uint32_t(value), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_createdTokenName)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String SelectIonTokenWindow::createdTokenName() const {
    void* reinteropException = nullptr;
    auto result = Property_get_createdTokenName((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_createdTokenName)(void* thiz, void* value, void** reinteropException) = nullptr;


void SelectIonTokenWindow::createdTokenName(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_createdTokenName((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int32_t (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_selectedExistingTokenIndex)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t SelectIonTokenWindow::selectedExistingTokenIndex() const {
    void* reinteropException = nullptr;
    auto result = Property_get_selectedExistingTokenIndex((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_selectedExistingTokenIndex)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void SelectIonTokenWindow::selectedExistingTokenIndex(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_selectedExistingTokenIndex((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_specifiedToken)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String SelectIonTokenWindow::specifiedToken() const {
    void* reinteropException = nullptr;
    auto result = Property_get_specifiedToken((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_specifiedToken)(void* thiz, void* value, void** reinteropException) = nullptr;


void SelectIonTokenWindow::specifiedToken(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_specifiedToken((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::SelectIonTokenWindow::CallGetDefaultNewTokenName_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


::DotNet::System::String SelectIonTokenWindow::GetDefaultNewTokenName() {
    void* reinteropException = nullptr;
    auto result = CallGetDefaultNewTokenName_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::CallShowWindow_ouKG7YNdV4bUJcBV0W3dBA)(void* server, void** reinteropException) = nullptr;


void SelectIonTokenWindow::ShowWindow(const ::DotNet::CesiumForUnity::CesiumIonServer& server) {
    void* reinteropException = nullptr;
    CallShowWindow_ouKG7YNdV4bUJcBV0W3dBA(server.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::SelectIonTokenWindow::CallGetExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::System::String> SelectIonTokenWindow::GetExistingTokenList() const {
    void* reinteropException = nullptr;
    auto result = CallGetExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::CallRefreshExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void SelectIonTokenWindow::RefreshExistingTokenList() const {
    void* reinteropException = nullptr;
    CallRefreshExistingTokenList_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::SelectIonTokenWindow::Field_get_currentWindow)(void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Field_set_currentWindow)(void* value, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::SelectIonTokenWindow SelectIonTokenWindow::currentWindow() {
    void* reinteropException = nullptr;
    auto result = Field_get_currentWindow(&reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::CesiumForUnity::SelectIonTokenWindow(::DotNet::Reinterop::ObjectHandle(result));
}


void SelectIonTokenWindow::currentWindow(const ::DotNet::CesiumForUnity::SelectIonTokenWindow& value) {
    void* reinteropException = nullptr;
    Field_set_currentWindow(value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void* (*DotNet::CesiumForUnity::SelectIonTokenWindow::Field_get_server)(void* thiz, void** reinteropException) = nullptr;


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Field_set_server)(void* thiz, void* value, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServer SelectIonTokenWindow::server() const {
    void* reinteropException = nullptr;
    auto result = Field_get_server((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
      throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
    return ::DotNet::CesiumForUnity::CesiumIonServer(::DotNet::Reinterop::ObjectHandle(result));
}


void SelectIonTokenWindow::server(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const {
    void* reinteropException = nullptr;
    Field_set_server((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr) {
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    }
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::CallClose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void SelectIonTokenWindow::Close() const {
    void* reinteropException = nullptr;
    CallClose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String SelectIonTokenWindow::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void SelectIonTokenWindow::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> SelectIonTokenWindow::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::SelectIonTokenWindow::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void SelectIonTokenWindow::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::SelectIonTokenWindow::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool SelectIonTokenWindow::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool SelectIonTokenWindow::operator==(const SelectIonTokenWindow& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool SelectIonTokenWindow::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool SelectIonTokenWindow::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::SelectIonTokenWindow::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool SelectIonTokenWindow::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool SelectIonTokenWindow::operator!=(const SelectIonTokenWindow& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool SelectIonTokenWindow::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool SelectIonTokenWindow::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::SelectIonTokenWindow::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t SelectIonTokenWindow::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*SelectIonTokenWindow::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::SelectIonTokenWindowImpl& SelectIonTokenWindow::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::SelectIonTokenWindowImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_SelectIonTokenWindow_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::SelectIonTokenWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::SelectIonTokenWindowImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_SelectIonTokenWindow_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::SelectIonTokenWindowImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_SelectIonTokenWindow_RefreshTokens(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::SelectIonTokenWindowImpl*>(pImpl);const ::DotNet::CesiumForUnity::SelectIonTokenWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->RefreshTokens(wrapper);
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
void DotNet_CesiumForUnity_SelectIonTokenWindow_CreateToken(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::SelectIonTokenWindowImpl*>(pImpl);const ::DotNet::CesiumForUnity::SelectIonTokenWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->CreateToken(wrapper);
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
void DotNet_CesiumForUnity_SelectIonTokenWindow_UseExistingToken(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::SelectIonTokenWindowImpl*>(pImpl);const ::DotNet::CesiumForUnity::SelectIonTokenWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->UseExistingToken(wrapper);
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
void DotNet_CesiumForUnity_SelectIonTokenWindow_SpecifyToken(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::SelectIonTokenWindowImpl*>(pImpl);const ::DotNet::CesiumForUnity::SelectIonTokenWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->SpecifyToken(wrapper);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

