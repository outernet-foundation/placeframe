#include <DotNet/UnityEngine/AsyncOperation.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Action1.h>



namespace DotNet::UnityEngine {

AsyncOperation::AsyncOperation(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


AsyncOperation::AsyncOperation(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool AsyncOperation::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool AsyncOperation::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& AsyncOperation::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& AsyncOperation::GetHandle() {
    return this->_handle;
}


AsyncOperation::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::AsyncOperation::Calladd_completed_89b__Riirtgd1Q5mmRzPojA)(void* thiz, void* value, void** reinteropException) = nullptr;


void AsyncOperation::add_completed(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& value) const {
    void* reinteropException = nullptr;
    Calladd_completed_89b__Riirtgd1Q5mmRzPojA((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::AsyncOperation::Callremove_completed_89b__Riirtgd1Q5mmRzPojA)(void* thiz, void* value, void** reinteropException) = nullptr;


void AsyncOperation::remove_completed(const ::DotNet::System::Action1<::DotNet::UnityEngine::AsyncOperation>& value) const {
    void* reinteropException = nullptr;
    Callremove_completed_89b__Riirtgd1Q5mmRzPojA((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine


