#include <DotNet/UnityEngine/Networking/UnityWebRequest.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/UnityEngine/Networking/DownloadHandler.h>
#include <DotNet/UnityEngine/Networking/UploadHandler.h>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/UnityEngine/Networking/Result.h>
#include <DotNet/System/Collections/Generic/Dictionary2.h>
#include <DotNet/UnityEngine/Networking/UnityWebRequestAsyncOperation.h>



namespace DotNet::UnityEngine::Networking {

UnityWebRequest::UnityWebRequest(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


UnityWebRequest::UnityWebRequest(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool UnityWebRequest::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool UnityWebRequest::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& UnityWebRequest::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& UnityWebRequest::GetHandle() {
    return this->_handle;
}


void* (*UnityWebRequest::Construct_N5nF6s7__PflIcgtgQgj6DA)(void* url, void* method, void* downloadHandler, void* uploadHandler, void** reinteropException) = nullptr;


UnityWebRequest::UnityWebRequest(const ::DotNet::System::String& url, const ::DotNet::System::String& method, const ::DotNet::UnityEngine::Networking::DownloadHandler& downloadHandler, const ::DotNet::UnityEngine::Networking::UploadHandler& uploadHandler)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_N5nF6s7__PflIcgtgQgj6DA(url.GetHandle().GetRaw(), method.GetHandle().GetRaw(), downloadHandler.GetHandle().GetRaw(), uploadHandler.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


UnityWebRequest::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::uint8_t (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_isDone)(void* thiz, void** reinteropException) = nullptr;


bool UnityWebRequest::isDone() const {
    void* reinteropException = nullptr;
    auto result = Property_get_isDone((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_error)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String UnityWebRequest::error() const {
    void* reinteropException = nullptr;
    auto result = Property_get_error((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_method)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String UnityWebRequest::method() const {
    void* reinteropException = nullptr;
    auto result = Property_get_method((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_set_method)(void* thiz, void* value, void** reinteropException) = nullptr;


void UnityWebRequest::method(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_method((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_url)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String UnityWebRequest::url() const {
    void* reinteropException = nullptr;
    auto result = Property_get_url((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_set_url)(void* thiz, void* value, void** reinteropException) = nullptr;


void UnityWebRequest::url(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_url((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint32_t (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_result)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Networking::Result UnityWebRequest::result() const {
    void* reinteropException = nullptr;
    auto result = Property_get_result((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Networking::Result(result);
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_downloadHandler)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Networking::DownloadHandler UnityWebRequest::downloadHandler() const {
    void* reinteropException = nullptr;
    auto result = Property_get_downloadHandler((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Networking::DownloadHandler(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_set_downloadHandler)(void* thiz, void* value, void** reinteropException) = nullptr;


void UnityWebRequest::downloadHandler(const ::DotNet::UnityEngine::Networking::DownloadHandler& value) const {
    void* reinteropException = nullptr;
    Property_set_downloadHandler((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::int64_t (*DotNet::UnityEngine::Networking::UnityWebRequest::Property_get_responseCode)(void* thiz, void** reinteropException) = nullptr;


::std::int64_t UnityWebRequest::responseCode() const {
    void* reinteropException = nullptr;
    auto result = Property_get_responseCode((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::CallGet_Y2__l4HVQ8CbSg4jpXDip9A)(void* uri, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Networking::UnityWebRequest UnityWebRequest::Get(const ::DotNet::System::String& uri) {
    void* reinteropException = nullptr;
    auto result = CallGet_Y2__l4HVQ8CbSg4jpXDip9A(uri.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Networking::UnityWebRequest(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequest::CallAbort_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void UnityWebRequest::Abort() const {
    void* reinteropException = nullptr;
    CallAbort_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequest::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void UnityWebRequest::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequest::CallSetRequestHeader_tEfBle3aSdR47_HxLakNjw)(void* thiz, void* name, void* value, void** reinteropException) = nullptr;


void UnityWebRequest::SetRequestHeader(const ::DotNet::System::String& name, const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    CallSetRequestHeader_tEfBle3aSdR47_HxLakNjw((*this).GetHandle().GetRaw(), name.GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::CallGetResponseHeader_wfPSjxsETIcebv8un8PGZw)(void* thiz, void* name, void** reinteropException) = nullptr;


::DotNet::System::String UnityWebRequest::GetResponseHeader(const ::DotNet::System::String& name) const {
    void* reinteropException = nullptr;
    auto result = CallGetResponseHeader_wfPSjxsETIcebv8un8PGZw((*this).GetHandle().GetRaw(), name.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::CallGetResponseHeaders_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::System::String> UnityWebRequest::GetResponseHeaders() const {
    void* reinteropException = nullptr;
    auto result = CallGetResponseHeaders_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::Dictionary2<::DotNet::System::String, ::DotNet::System::String>(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::UnityEngine::Networking::UnityWebRequest::CallSendWebRequest_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Networking::UnityWebRequestAsyncOperation UnityWebRequest::SendWebRequest() const {
    void* reinteropException = nullptr;
    auto result = CallSendWebRequest_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Networking::UnityWebRequestAsyncOperation(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::UnityEngine::Networking


