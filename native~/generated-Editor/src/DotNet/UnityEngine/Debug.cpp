#include <DotNet/UnityEngine/Debug.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::UnityEngine {

Debug::Debug(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


Debug::Debug(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool Debug::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool Debug::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& Debug::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& Debug::GetHandle() {
    return this->_handle;
}


Debug::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::UnityEngine::Debug::CallLog_FA05wu8x__otZNsgdHTnU9A)(void* message, void** reinteropException) = nullptr;


void Debug::Log(const ::DotNet::System::Object& message) {
    void* reinteropException = nullptr;
    CallLog_FA05wu8x__otZNsgdHTnU9A(message.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Debug::CallLogWarning_FA05wu8x__otZNsgdHTnU9A)(void* message, void** reinteropException) = nullptr;


void Debug::LogWarning(const ::DotNet::System::Object& message) {
    void* reinteropException = nullptr;
    CallLogWarning_FA05wu8x__otZNsgdHTnU9A(message.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::UnityEngine::Debug::CallLogError_FA05wu8x__otZNsgdHTnU9A)(void* message, void** reinteropException) = nullptr;


void Debug::LogError(const ::DotNet::System::Object& message) {
    void* reinteropException = nullptr;
    CallLogError_FA05wu8x__otZNsgdHTnU9A(message.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine


