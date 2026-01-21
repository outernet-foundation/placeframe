#include <DotNet/CesiumForUnity/CesiumIonSession.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/CesiumForUnity/CesiumIonServer.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/QuickAddItem.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include "CesiumIonSessionImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>



namespace DotNet::CesiumForUnity {

CesiumIonSession::CesiumIonSession(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumIonSession::CesiumIonSession(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumIonSession::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumIonSession::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumIonSession::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumIonSession::GetHandle() {
    return this->_handle;
}


CesiumIonSession::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumIonSession::Property_get_server)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIonServer CesiumIonSession::server() const {
    void* reinteropException = nullptr;
    auto result = Property_get_server((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumIonServer(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonSession::Property_set_server)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumIonSession::server(const ::DotNet::CesiumForUnity::CesiumIonServer& value) const {
    void* reinteropException = nullptr;
    Property_set_server((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumIonSession::CallIsConnected_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


bool CesiumIonSession::IsConnected() const {
    void* reinteropException = nullptr;
    auto result = CallIsConnected_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*DotNet::CesiumForUnity::CesiumIonSession::CallGetQuickAddItems_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::QuickAddItem> CesiumIonSession::GetQuickAddItems() const {
    void* reinteropException = nullptr;
    auto result = CallGetQuickAddItems_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::QuickAddItem>(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastConnectionUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonSession::BroadcastConnectionUpdate() const {
    void* reinteropException = nullptr;
    CallBroadcastConnectionUpdate_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastAssetsUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonSession::BroadcastAssetsUpdate() const {
    void* reinteropException = nullptr;
    CallBroadcastAssetsUpdate_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastProfileUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonSession::BroadcastProfileUpdate() const {
    void* reinteropException = nullptr;
    CallBroadcastProfileUpdate_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastTokensUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonSession::BroadcastTokensUpdate() const {
    void* reinteropException = nullptr;
    CallBroadcastTokensUpdate_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumIonSession::CallBroadcastDefaultsUpdate_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void CesiumIonSession::BroadcastDefaultsUpdate() const {
    void* reinteropException = nullptr;
    CallBroadcastDefaultsUpdate_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*CesiumIonSession::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::CesiumIonSessionImpl& CesiumIonSession::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::CesiumIonSessionImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumIonSession_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::CesiumIonSessionImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumIonSession_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsConnected(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsConnected(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsConnecting(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsConnecting(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsResuming(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsResuming(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsProfileLoaded(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsProfileLoaded(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsLoadingProfile(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsLoadingProfile(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsAssetListLoaded(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsAssetListLoaded(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsLoadingAssetList(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsLoadingAssetList(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsTokenListLoaded(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsTokenListLoaded(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsLoadingTokenList(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsLoadingTokenList(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsDefaultsLoaded(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsDefaultsLoaded(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsLoadingDefaults(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsLoadingDefaults(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumIonSession_IsAuthenticationRequired(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->IsAuthenticationRequired(wrapper);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumIonSession_Connect(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->Connect(wrapper);
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
void DotNet_CesiumForUnity_CesiumIonSession_Resume(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->Resume(wrapper);
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
void DotNet_CesiumForUnity_CesiumIonSession_Disconnect(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->Disconnect(wrapper);
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
void* DotNet_CesiumForUnity_CesiumIonSession_GetProfileUsername(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetProfileUsername(wrapper);
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
void* DotNet_CesiumForUnity_CesiumIonSession_GetAuthorizeUrl(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetAuthorizeUrl(wrapper);
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
void* DotNet_CesiumForUnity_CesiumIonSession_GetRedirectUrl(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetRedirectUrl(wrapper);
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
void* DotNet_CesiumForUnity_CesiumIonSession_GetQuickAddItems(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetQuickAddItems(wrapper);
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
void DotNet_CesiumForUnity_CesiumIonSession_Tick(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->Tick(wrapper);
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
void DotNet_CesiumForUnity_CesiumIonSession_RefreshProfile(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->RefreshProfile(wrapper);
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
void DotNet_CesiumForUnity_CesiumIonSession_RefreshTokens(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
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
void DotNet_CesiumForUnity_CesiumIonSession_RefreshAssets(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->RefreshAssets(wrapper);
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
void DotNet_CesiumForUnity_CesiumIonSession_RefreshDefaults(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::CesiumIonSessionImpl*>(pImpl);const ::DotNet::CesiumForUnity::CesiumIonSession wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->RefreshDefaults(wrapper);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

