#include <DotNet/UnityEngine/Networking/UploadHandler.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>



namespace DotNet::UnityEngine::Networking {

UploadHandler::UploadHandler(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


UploadHandler::UploadHandler(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool UploadHandler::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool UploadHandler::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& UploadHandler::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& UploadHandler::GetHandle() {
    return this->_handle;
}


UploadHandler::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


} // namespace DotNet::UnityEngine::Networking


