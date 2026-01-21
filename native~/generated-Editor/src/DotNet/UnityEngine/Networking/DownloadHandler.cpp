#include <DotNet/UnityEngine/Networking/DownloadHandler.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::UnityEngine::Networking {

DownloadHandler::DownloadHandler(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


DownloadHandler::DownloadHandler(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool DownloadHandler::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool DownloadHandler::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& DownloadHandler::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& DownloadHandler::GetHandle() {
    return this->_handle;
}


DownloadHandler::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::Networking::DownloadHandler::CallDispose_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void DownloadHandler::Dispose() const {
    void* reinteropException = nullptr;
    CallDispose_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine::Networking


