#include <DotNet/UnityEngine/Networking/UnityWebRequestAsyncOperation.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/UnityEngine/AsyncOperation.h>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Action1.h>



namespace DotNet::UnityEngine::Networking {

UnityWebRequestAsyncOperation::UnityWebRequestAsyncOperation(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


UnityWebRequestAsyncOperation::UnityWebRequestAsyncOperation(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool UnityWebRequestAsyncOperation::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool UnityWebRequestAsyncOperation::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& UnityWebRequestAsyncOperation::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& UnityWebRequestAsyncOperation::GetHandle() {
    return this->_handle;
}


UnityWebRequestAsyncOperation::operator ::DotNet::UnityEngine::AsyncOperation() const {
    return ::DotNet::UnityEngine::AsyncOperation(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


UnityWebRequestAsyncOperation::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequestAsyncOperation::Calladd_completed_89b__Riirtgd1Q5mmRzPojA)(void* thiz, void* value, void** reinteropException) = nullptr;


void UnityWebRequestAsyncOperation::add_completed(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& value) const {
    void* reinteropException = nullptr;
    Calladd_completed_89b__Riirtgd1Q5mmRzPojA((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Networking::UnityWebRequestAsyncOperation::Callremove_completed_89b__Riirtgd1Q5mmRzPojA)(void* thiz, void* value, void** reinteropException) = nullptr;


void UnityWebRequestAsyncOperation::remove_completed(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& value) const {
    void* reinteropException = nullptr;
    Callremove_completed_89b__Riirtgd1Q5mmRzPojA((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine::Networking


