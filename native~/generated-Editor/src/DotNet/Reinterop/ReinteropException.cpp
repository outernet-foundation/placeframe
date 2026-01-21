#include <DotNet/Reinterop/ReinteropException.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/String.h>
#include <DotNet/System/Exception.h>
#include <DotNet/System/Object.h>



namespace DotNet::Reinterop {

ReinteropException::ReinteropException(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


ReinteropException::ReinteropException(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool ReinteropException::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool ReinteropException::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& ReinteropException::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& ReinteropException::GetHandle() {
    return this->_handle;
}


void* (*ReinteropException::Construct_XwA9a8yCTL1RNh1m2OT3bA)(void* message, void** reinteropException) = nullptr;


ReinteropException::ReinteropException(const ::DotNet::System::String& message)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_XwA9a8yCTL1RNh1m2OT3bA(message.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


ReinteropException::operator ::DotNet::System::Exception() const {
    return ::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


ReinteropException::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::Reinterop::ReinteropException::Property_get_Message)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String ReinteropException::Message() const {
    void* reinteropException = nullptr;
    auto result = Property_get_Message((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::Reinterop


