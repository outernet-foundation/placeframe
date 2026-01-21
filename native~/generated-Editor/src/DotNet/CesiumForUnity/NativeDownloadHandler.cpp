#include <DotNet/CesiumForUnity/NativeDownloadHandler.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Networking/DownloadHandler.h>
#include <DotNet/System/Object.h>
#include "NativeDownloadHandlerImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/System/String.h>
#include <cstdint>



namespace DotNet::CesiumForUnity {

NativeDownloadHandler::NativeDownloadHandler(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


NativeDownloadHandler::NativeDownloadHandler(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool NativeDownloadHandler::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool NativeDownloadHandler::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& NativeDownloadHandler::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& NativeDownloadHandler::GetHandle() {
    return this->_handle;
}


void* (*NativeDownloadHandler::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


NativeDownloadHandler::NativeDownloadHandler()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


NativeDownloadHandler::operator ::DotNet::UnityEngine::Networking::DownloadHandler() const {
    return ::DotNet::UnityEngine::Networking::DownloadHandler(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


NativeDownloadHandler::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::CesiumForUnity::NativeDownloadHandler::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void NativeDownloadHandler::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*NativeDownloadHandler::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::NativeDownloadHandlerImpl& NativeDownloadHandler::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::NativeDownloadHandlerImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_NativeDownloadHandler_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::NativeDownloadHandler wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::NativeDownloadHandlerImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_NativeDownloadHandler_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::NativeDownloadHandlerImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_NativeDownloadHandler_ReceiveDataNative(void* handle, void* pImpl, void* data, ::std::int32_t dataLength, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::NativeDownloadHandlerImpl*>(pImpl);const ::DotNet::CesiumForUnity::NativeDownloadHandler wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->ReceiveDataNative(wrapper, data, dataLength);
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

} // extern "C"

