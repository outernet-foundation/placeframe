#include <DotNet/CesiumForUnity/IonTokenTroubleshootingWindow.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEditor/EditorWindow.h>
#include <DotNet/UnityEngine/Object.h>
#include <DotNet/System/Object.h>
#include <DotNet/CesiumForUnity/CesiumIonAsset.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/TokenTroubleshootingDetails.h>
#include <DotNet/CesiumForUnity/AssetTroubleshootingDetails.h>
#include <DotNet/System/String.h>
#include <cstdint>
#include <DotNet/UnityEngine/HideFlags.h>
#include <flags/flags.hpp>
#include "IonTokenTroubleshootingWindowImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>



namespace DotNet::CesiumForUnity {

IonTokenTroubleshootingWindow::IonTokenTroubleshootingWindow(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


IonTokenTroubleshootingWindow::IonTokenTroubleshootingWindow(std::nullptr_t) noexcept : _handle(nullptr) {
}


const ::DotNet::Reinterop::ObjectHandle& IonTokenTroubleshootingWindow::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& IonTokenTroubleshootingWindow::GetHandle() {
    return this->_handle;
}


IonTokenTroubleshootingWindow::operator ::DotNet::UnityEditor::EditorWindow() const {
    return ::DotNet::UnityEditor::EditorWindow(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


IonTokenTroubleshootingWindow::operator ::DotNet::UnityEngine::Object() const {
    return ::DotNet::UnityEngine::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


IonTokenTroubleshootingWindow::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_ionAsset)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonAsset IonTokenTroubleshootingWindow::ionAsset() const {
    void* reinteropException = nullptr;
    auto result = Property_get_ionAsset((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonAsset(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_set_ionAsset)(void* thiz, void* value, void** reinteropException) = nullptr;


void IonTokenTroubleshootingWindow::ionAsset(const ::DotNet::CesiumForUnity::CesiumIonAsset& value) const {
    void* reinteropException = nullptr;
    Property_set_ionAsset((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_assetTokenDetails)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::TokenTroubleshootingDetails IonTokenTroubleshootingWindow::assetTokenDetails() const {
    void* reinteropException = nullptr;
    auto result = Property_get_assetTokenDetails((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::TokenTroubleshootingDetails(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_defaultTokenDetails)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::TokenTroubleshootingDetails IonTokenTroubleshootingWindow::defaultTokenDetails() const {
    void* reinteropException = nullptr;
    auto result = Property_get_defaultTokenDetails((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::TokenTroubleshootingDetails(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_assetDetails)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::AssetTroubleshootingDetails IonTokenTroubleshootingWindow::assetDetails() const {
    void* reinteropException = nullptr;
    auto result = Property_get_assetDetails((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::AssetTroubleshootingDetails(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::CallUseDefaultToken_qpX7eE7SvOg4KIeidX7yng)(void* asset, void** reinteropException) = nullptr;


void IonTokenTroubleshootingWindow::UseDefaultToken(const ::DotNet::CesiumForUnity::CesiumIonAsset& asset) {
    void* reinteropException = nullptr;
    CallUseDefaultToken_qpX7eE7SvOg4KIeidX7yng(asset.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::CallClose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void IonTokenTroubleshootingWindow::Close() const {
    void* reinteropException = nullptr;
    CallClose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_name)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String IonTokenTroubleshootingWindow::name() const {
    void* reinteropException = nullptr;
    auto result = Property_get_name((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_set_name)(void* thiz, void* value, void** reinteropException) = nullptr;


void IonTokenTroubleshootingWindow::name(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_name((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_get_hideFlags)(void* thiz, void** reinteropException) = nullptr;


::flags::flags<::DotNet::UnityEngine::HideFlags> IonTokenTroubleshootingWindow::hideFlags() const {
    void* reinteropException = nullptr;
    auto result = Property_get_hideFlags((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::HideFlags(result);
}


void (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Property_set_hideFlags)(void* thiz, ::std::uint32_t value, void** reinteropException) = nullptr;


void IonTokenTroubleshootingWindow::hideFlags(::flags::flags<::DotNet::UnityEngine::HideFlags> value) const {
    void* reinteropException = nullptr;
    Property_set_hideFlags((*this).GetHandle().GetRaw(), value.underlying_value(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool IonTokenTroubleshootingWindow::operator==(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Equality(*this, rhs);
}


bool IonTokenTroubleshootingWindow::operator==(const IonTokenTroubleshootingWindow& rhs) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool IonTokenTroubleshootingWindow::operator==(std::nullptr_t) const {
return op_Equality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool IonTokenTroubleshootingWindow::op_Equality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Equality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::uint8_t (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg)(void* x, void* y, void** reinteropException) = nullptr;


bool IonTokenTroubleshootingWindow::operator!=(const ::DotNet::UnityEngine::Object& rhs) const {
  return op_Inequality(*this, rhs);
}


bool IonTokenTroubleshootingWindow::operator!=(const IonTokenTroubleshootingWindow& rhs) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(rhs));
}


bool IonTokenTroubleshootingWindow::operator!=(std::nullptr_t) const {
return op_Inequality(*this, ::DotNet::UnityEngine::Object(nullptr));
}


bool IonTokenTroubleshootingWindow::op_Inequality(const ::DotNet::UnityEngine::Object& x, const ::DotNet::UnityEngine::Object& y) {
    void* reinteropException = nullptr;
    auto result = Callop_Inequality_5bi2N6jTkaYVhpHPRxL2Wg(x.GetHandle().GetRaw(), y.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int32_t (*DotNet::CesiumForUnity::IonTokenTroubleshootingWindow::CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t IonTokenTroubleshootingWindow::GetInstanceID() const {
    void* reinteropException = nullptr;
    auto result = CallGetInstanceID_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_IonTokenTroubleshootingWindow_GetTroubleshootingDetails(void* handle, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    CesiumForUnityNative::IonTokenTroubleshootingWindowImpl::GetTroubleshootingDetails(wrapper);
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
void DotNet_CesiumForUnity_IonTokenTroubleshootingWindow_AuthorizeToken(void* handle, void* token, ::std::uint8_t isDefaultToken, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    CesiumForUnityNative::IonTokenTroubleshootingWindowImpl::AuthorizeToken(wrapper, ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(token)), !!isDefaultToken);
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
void DotNet_CesiumForUnity_IonTokenTroubleshootingWindow_SelectNewDefaultToken(void* handle, void** reinteropException) {
  try {
    const ::DotNet::CesiumForUnity::IonTokenTroubleshootingWindow wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    CesiumForUnityNative::IonTokenTroubleshootingWindowImpl::SelectNewDefaultToken(wrapper);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

